#!/usr/bin/env python3
"""BanlaTravel.vn media pipeline.

Finds real photos for each catalogue item (scripts/properties.json), runs a quality gate,
converts to WebP (1280px wide, q82) under frontend/assets/places/{region}/{slug}-0N.webp,
records provenance per image, and checkpoints after every property (scripts/checkpoint.json)
so an interrupted run resumes where it stopped.

Usage:
  python scripts/ota_media_pipeline.py                # run all 4 batches (resumes)
  python scripts/ota_media_pipeline.py --batch 2      # one batch
  python scripts/ota_media_pipeline.py --redo ID ...  # re-run given property ids
  python scripts/ota_media_pipeline.py --reject ID:N  # drop image N of ID after manual review and refill
Requires: pip install ddgs pillow requests numpy
"""
import argparse, hashlib, io, json, random, re, sys, time, unicodedata
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests
from PIL import Image, ImageFilter, ImageOps

Image.MAX_IMAGE_PIXELS = 200_000_000

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
ASSETS = ROOT / 'frontend' / 'assets' / 'places'
CKPT = SCRIPTS / 'checkpoint.json'
PROPS = SCRIPTS / 'properties.json'

MIN_W, AR_MIN, AR_MAX = 900, 1.3, 1.9
OUT_W, QUALITY, MAX_KB = 1280, 82, 120
TARGET, MIN_OK = 5, 4
BLUR_MIN = 60.0           # variance of Laplacian on 640px grayscale
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

# Sources whose photos carry OTA / stock watermarks or are aggregators of unknown origin.
BLOCK_DOMAINS = [
    'booking.com', 'bstatic.com', 'agoda', 'traveloka', 'tripadvisor', 'expedia', 'hotels.com', 'trip.com',
    'ctrip', 'tripcdn', 'ivivu', 'mytour', 'vntrip', 'chudu24', 'klook', 'kayak', 'trivago', 'hotelscombined',
    'pinterest', 'pinimg', 'shutterstock', 'alamy', 'dreamstime', 'istockphoto', 'gettyimages', '123rf',
    'depositphotos', 'stock.adobe', 'freepik', 'vecteezy', 'lexica', 'openart', 'midjourney', 'civitai',
    'ytimg', 'youtube', 'tiktok', 'airbnb', 'muzli', 'vietnamtrip', 'travelbook', 'gotadi', 'bestprice',
    'luxstay', 'hotels.ng', 'momondo', 'priceline', 'orbitz', 'skyscanner', 'cleartrip', 'makemytrip',
    'goibibo', 'hostelworld', 'hrs.com', 'tablethotels', 'hotelmix', 'hotel-mix', 'tiket.com', 'pegipegi',
    'wego', 'yatra', 'zenhotels', 'ostrovok', 'hotelopia', 'lastminute', 'ebookers', 'travelocity',
    'vinpearl.com/vi/tour', 'vemaybay', 'mia.vn', 'dulichviet', 'trip.vn', 'tripi', 'pystravel',
]
BAD_TEXT = ['phoi canh', 'render', '3d ', 'ai generated', 'ai-generated', 'midjourney', 'stable diffusion',
            'logo', 'map', 'ban do', 'menu', 'voucher', 'floor plan', 'so do', 'infographic', 'banner']
PRESS_HINTS = ['vnexpress', 'tuoitre', 'thanhnien', 'dantri', 'vietnamnet', 'zingnews', 'znews', 'baochinhphu',
               'vtv', 'vov', 'nhandan', 'laodong', 'tienphong', 'vietnamplus', 'baodautu', 'kinhtedothi',
               'dsvn', 'vr.com.vn', 'saigontimes', 'cafef', 'thesaigontimes', 'vietnamnews', 'e.vnexpress']
WP_SIZE = re.compile(r'-\d{2,4}x\d{2,4}(\.(?:jpe?g|png|webp))', re.I)
HERO_WORDS = ['aerial', 'exterior', 'overview', 'facade', 'toan canh', 'view', 'resort', 'panorama']


def norm(s):
    s = (s or '').replace('Đ', 'D').replace('đ', 'd')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' ' + s.strip() + ' '


def compact(s):
    return norm(s).replace(' ', '')


def matches(item, text):
    t = norm(text)
    tc = t.replace(' ', '')
    for group in item['match']:
        if not any((' ' + norm(a).strip() + ' ') in t or (len(compact(a)) >= 6 and compact(a) in tc) for a in group):
            return False
    return True


def domain(u):
    try:
        return urlparse(u).netloc.lower()
    except Exception:
        return ''


def blocked(u):
    u = (u or '').lower()
    return any(b in u for b in BLOCK_DOMAINS)


def official_score(item, page, img):
    """Official sites usually carry a distinctive name token in their domain."""
    d = domain(page) + ' ' + domain(img)
    dc = d.replace('-', '').replace('.', '')
    score = 0
    for a in item['match'][0]:  # first group = the distinctive name token(s)
        c = compact(a)
        if len(c) >= 5 and c in dc:
            score += 3
            break
    for brand in ['accor', 'ahstatic', 'marriott', 'ihg', 'hilton', 'sofitel', 'capella', 'banyantree', 'sixsenses',
                  'victoriahotels', 'vinpearl', 'movenpick', 'radisson', 'fusion', 'sungroup', 'sunworld', 'azerai',
                  'regenthotels', 'pullman', 'mgallery', 'garrya', 'muongthanh', 'intercontinental']:
        if brand in dc:
            score += 3
            break
    if any(p in d for p in PRESS_HINTS):
        score += 1
    return score


class Gate(Exception):
    pass


def fetch_image(url, referer):
    r = requests.get(url, headers={'User-Agent': UA, 'Referer': referer or url}, timeout=20)
    r.raise_for_status()
    if len(r.content) < 30_000:
        raise Gate('file too small')
    im = Image.open(io.BytesIO(r.content))
    im = ImageOps.exif_transpose(im)
    return im.convert('RGB'), r.content


def quality(im):
    w, h = im.size
    if w < MIN_W:
        raise Gate(f'width {w}<900')
    ar = w / h
    if not (AR_MIN <= ar <= AR_MAX):
        raise Gate(f'aspect {ar:.2f}')
    g = np.asarray(im.convert('L').resize((640, int(640 / ar))), dtype=np.float32)
    lap = g[1:-1, 1:-1] * -4 + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    v = float(lap.var())
    if v < BLUR_MIN:
        raise Gate(f'blurry {v:.0f}')
    if g.std() < 18:
        raise Gate('flat/low-contrast')
    # collage / letterbox borders: large uniform rows at top or bottom
    rows = g.std(axis=1)
    if (rows[:20] < 3).all() or (rows[-20:] < 3).all():
        raise Gate('letterbox/border')
    return v


def dhash(im):
    g = np.asarray(im.convert('L').resize((9, 8)), dtype=np.int16)
    return int(''.join('1' if b else '0' for b in (g[:, 1:] > g[:, :-1]).flatten()), 2)


def to_webp(im, path):
    w, h = im.size
    nh = round(h * OUT_W / w)
    out = im.resize((OUT_W, nh), Image.LANCZOS) if w != OUT_W else im
    q, buf = QUALITY, None
    # 1) lower quality step by step; 2) if a very detailed photo is still too heavy, light denoise
    for rad in (0, 0.5, 0.8, 1.1):
        src = out.filter(ImageFilter.GaussianBlur(rad)) if rad else out
        for q in ((82, 76, 70, 64, 58) if rad == 0 else (66, 58, 50)):
            buf = io.BytesIO()
            src.save(buf, 'WEBP', quality=q, method=6)
            if buf.tell() <= MAX_KB * 1024:
                break
        if buf.tell() <= MAX_KB * 1024:
            break
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())
    return buf.tell(), q, (OUT_W, nh)


def search(queries, per=40):
    from ddgs import DDGS
    seen, res = set(), []
    for qi, q in enumerate(queries):
        for attempt in range(3):
            try:
                rows = DDGS().images(q, max_results=per, region='wt-wt', safesearch='moderate')
                break
            except Exception as e:  # rate limit -> back off
                time.sleep(5 + attempt * 10)
                rows = []
        for r in rows:
            u = r.get('image')
            if u and u not in seen:
                seen.add(u)
                r['_q'] = qi
                res.append(r)
        time.sleep(random.uniform(1.0, 2.0))
    return res


def page_images(it, pages, seen):
    """Fallback candidates: <img> tags of articles/pages whose title names the property."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    out = []
    for pg in pages:
        try:
            h = requests.get(pg, headers={'User-Agent': UA}, timeout=15)
            soup = BeautifulSoup(h.text, 'html.parser')
        except Exception:
            continue
        title = (soup.title.string if soup.title and soup.title.string else '')
        if not matches(it, title + ' ' + pg):
            continue
        for tag in soup.find_all('img'):
            cands = [tag.get('data-src'), tag.get('data-lazy-src'), tag.get('src')]
            ss = tag.get('srcset') or tag.get('data-srcset')
            if ss:
                cands.insert(0, ss.split(',')[-1].strip().split(' ')[0])
            u = next((c for c in cands if c and not c.startswith('data:')), None)
            if not u:
                continue
            u = urljoin(pg, u)
            if WP_SIZE.search(u):
                u = WP_SIZE.sub(r'\1', u)
            low = u.lower()
            if u in seen or blocked(u) or not re.search(r'\.(jpe?g|png|webp)(\?|$)', low) or any(
                    k in low for k in ['logo', 'icon', 'avatar', 'banner', 'qr', 'map']):
                continue
            # the image itself (file name / alt / caption) must name the property, so related-post
            # thumbnails of other places on the same page are never picked up
            own = ' '.join([u.rsplit('/', 1)[-1], tag.get('alt') or '', tag.get('title') or ''])
            if not matches({'match': it['match'][:1]}, own):
                continue
            seen.add(u)
            out.append({'image': u, 'url': pg, 'title': title.strip(), '_q': 9})
        if len(out) > 60:
            break
    return out


def queries_for(it):
    base = re.sub(r'\s*\(.*\)$', '', it['name'])
    place = it['search_place']
    q = [f'{base} {place}'] if norm(place).strip() not in norm(base) else [base]
    if it['category'] in ('train', 'ticket'):
        return [it['search_place']] + it['extra_queries']
    if it['category'] == 'homestay':
        q += [f'"{base}" {place} phòng nghỉ', f'{base} {place} review', f'{base} {place} view']
    else:
        q += [f'{base} room', f'{base} pool', f'{base} aerial view']
    return q + it['extra_queries']


def process(it, ck, rejected_urls=()):
    region_dir = ASSETS / it['region']
    cands = search(queries_for(it))
    log = {'candidates': len(cands), 'rejects': {}}
    scored, pages = [], []
    for r in cands:
        pg = r.get('url', '')
        if pg and pg not in pages and 'facebook.com' not in pg and not blocked(pg) and matches(it, r.get('title', '') + ' ' + pg):
            pages.append(pg)
        img, page, title = r['image'], r.get('url', ''), r.get('title', '')
        why = None
        if img in rejected_urls:
            why = 'manual-reject'
        elif blocked(img) or blocked(page):
            why = 'ota/stock/aggregator source'
        elif any(b in norm(title) for b in [' ' + w.strip() + ' ' for w in BAD_TEXT]):
            why = 'render/logo/map/AI keyword'
        elif not matches(it, title + ' ' + page):
            why = 'page does not name the property'
        elif WP_SIZE.search(img) and int(r.get('width') or 0) < MIN_W:
            r = dict(r, image=WP_SIZE.sub(r'\1', img), width=0, height=0)  # try full-size original
        else:
            try:
                w, h = int(r.get('width') or 0), int(r.get('height') or 0)
                if w and w < MIN_W:
                    why = 'width<900 (meta)'
                elif w and h and not (AR_MIN - .02 <= w / h <= AR_MAX + .02):
                    why = 'aspect (meta)'
            except ValueError:
                pass
        if why:
            log['rejects'][why] = log['rejects'].get(why, 0) + 1
            continue
        s = official_score(it, page, img) * 10 - r['_q'] * 2
        if r['_q'] == 0 and any(w in norm(title) for w in HERO_WORDS):
            s += 3
        scored.append((s, r))
    scored.sort(key=lambda x: -x[0])
    kept, hashes = [], []
    scored += [(-50 - i, r) for i, r in enumerate(page_images(it, pages[:6], {r['image'] for _, r in scored}))]
    for s, r in scored:
        if len(kept) >= TARGET:
            break
        try:
            im, raw = fetch_image(r['image'], r.get('url'))
            sharp = quality(im)
            hsh = dhash(im)
            if any(bin(hsh ^ h).count('1') <= 8 for h in hashes):
                raise Gate('duplicate')
        except Gate as g:
            k = 'gate: ' + str(g).split(' ')[0]
            log['rejects'][k] = log['rejects'].get(k, 0) + 1
            continue
        except Exception as e:
            log['rejects']['download error'] = log['rejects'].get('download error', 0) + 1
            continue
        hashes.append(hsh)
        kept.append(dict(im=im, r=r, score=s, sharp=sharp, sha1=hashlib.sha1(raw).hexdigest()))
    # hero first: highest official score from the overview query; otherwise keep ranking
    kept.sort(key=lambda k: (-(k['score'] + (5 if k['r']['_q'] == 0 else 0))))
    for old in region_dir.glob(f"{it['slug']}-0*.webp"):
        old.unlink()
    images = []
    for n, k in enumerate(kept, 1):
        fn = f"{it['slug']}-{n:02d}.webp"
        size, q, dims = to_webp(k['im'], region_dir / fn)
        r = k['r']
        src_dom = domain(r.get('url') or r['image'])
        images.append(dict(
            path=f"./assets/places/{it['region']}/{fn}", role='hero' if n == 1 else 'gallery',
            width=dims[0], height=dims[1], bytes=size, webp_quality=q,
            source_url=r['image'], source_page=r.get('url', ''), source_title=r.get('title', ''),
            source_domain=src_dom, source_kind=('official' if official_score(it, r.get('url', ''), r['image']) >= 3
                                                else 'press' if any(p in src_dom for p in PRESS_HINTS) else 'review/blog'),
            license='© chủ sở hữu ảnh (xem source_page). Chưa có giấy phép tái sử dụng — cần xin phép/ghi nguồn trước khi dùng thương mại.',
            original_sha1=k['sha1']))
    status = 'complete' if len(images) >= MIN_OK else ('partial' if images else 'missing')
    ck['done'][it['id']] = dict(status=status, count=len(images), images=images, log=log,
                                 ts=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    return status, len(images)


def set_hero(entry, n):
    """Move image n to position 1 and rename files so -01 is always the hero."""
    imgs = entry['images']
    if not (1 < n <= len(imgs)):
        return
    order = [imgs[n - 1]] + imgs[:n - 1] + imgs[n:]
    files = [ASSETS.parent.parent / im['path'][2:] for im in order]
    tmp = [f.with_suffix('.tmpwebp') for f in files]
    for f, t in zip(files, tmp):
        f.rename(t)
    for i, (im, t) in enumerate(zip(order, tmp), 1):
        new = re.sub(r'-0\d\.webp$', f'-{i:02d}.webp', im['path'])
        t.rename(ASSETS.parent.parent / new[2:])
        im['path'] = new
        im['role'] = 'hero' if i == 1 else 'gallery'
    entry['images'] = order


def drop_images(entry, ns):
    """Delete images ns (1-based) and renumber the rest -01..-0N."""
    base = ASSETS.parent.parent
    keep = [im for i, im in enumerate(entry['images'], 1) if i not in ns]
    for i, im in enumerate(entry['images'], 1):
        if i in ns:
            (base / im['path'][2:]).unlink(missing_ok=True)
    tmp = []
    for im in keep:
        t = (base / im['path'][2:]).with_suffix('.tmpwebp')
        (base / im['path'][2:]).rename(t)
        tmp.append(t)
    for i, (im, t) in enumerate(zip(keep, tmp), 1):
        im['path'] = re.sub(r'-0\d\.webp$', f'-{i:02d}.webp', im['path'])
        im['role'] = 'hero' if i == 1 else 'gallery'
        t.rename(base / im['path'][2:])
    entry['images'] = keep
    entry['count'] = len(keep)
    entry['status'] = 'complete' if len(keep) >= MIN_OK else ('partial' if keep else 'missing')


def load_ck():
    if CKPT.exists():
        return json.loads(CKPT.read_text())
    return {'version': 1, 'done': {}}


def save_ck(ck):
    tmp = CKPT.with_suffix('.tmp')
    tmp.write_text(json.dumps(ck, ensure_ascii=False, indent=1))
    tmp.replace(CKPT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int)
    ap.add_argument('--redo', nargs='*', default=[])
    ap.add_argument('--reject', nargs='*', default=[], help='ID:N image numbers to drop (manual review)')
    ap.add_argument('--drop', nargs='*', default=[], help='ID:N remove image N without re-searching (manual review)')
    ap.add_argument('--hero', nargs='*', default=[], help='ID:N make image N the hero (-01) after manual review')
    ap.add_argument('--checkpoint', help='alternate checkpoint file (parallel workers, one per batch)')
    ap.add_argument('--merge', nargs='*', help='merge worker checkpoints into scripts/checkpoint.json')
    a = ap.parse_args()
    global CKPT
    if a.merge:
        ck = load_ck()
        for f in a.merge:
            other = json.loads(Path(f).read_text())
            ck['done'].update(other['done'])
            for k, v in other.get('manual_rejects', {}).items():
                ck.setdefault('manual_rejects', {}).setdefault(k, []).extend(v)
        save_ck(ck)
        print('merged', len(ck['done']), 'items')
        return
    if a.checkpoint:
        CKPT = Path(a.checkpoint)
    data = json.loads(PROPS.read_text())
    ck = load_ck()
    rej = {}
    for spec in a.reject:
        pid, n = spec.rsplit(':', 1)
        e = ck['done'].get(pid)
        if e and int(n) <= len(e['images']):
            ck.setdefault('manual_rejects', {}).setdefault(pid, []).append(e['images'][int(n) - 1]['source_url'])
        a.redo.append(pid)
    drops = {}
    for spec in a.drop:
        pid, n = spec.rsplit(':', 1)
        drops.setdefault(pid, []).append(int(n))
    for pid, ns in drops.items():
        drop_images(ck['done'][pid], ns)
        ck.setdefault('manual_rejects', {}).setdefault(pid, [])
    for spec in a.hero:
        pid, n = spec.rsplit(':', 1)
        set_hero(ck['done'][pid], int(n))
    for pid in set(a.redo):
        ck['done'].pop(pid, None)
    save_ck(ck)
    todo = [x for x in data['items'] if (a.batch in (None, x['batch'])) and x['id'] not in ck['done']]
    print(f'{len(todo)} items to process', flush=True)
    for it in todo:
        st, n = process(it, ck, set(ck.get('manual_rejects', {}).get(it['id'], [])))
        save_ck(ck)  # checkpoint after every property
        print(f"[L{it['batch']}] {it['id']}: {n} images ({st})", flush=True)
        time.sleep(random.uniform(2, 4))  # anti-CAPTCHA delay between properties


if __name__ == '__main__':
    main()
