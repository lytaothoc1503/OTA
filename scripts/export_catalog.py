#!/usr/bin/env python3
"""Build frontend/catalog.json from scripts/properties.json + scripts/checkpoint.json,
validate it against scripts/catalog.schema.json, enforce size limits and write scripts/media_report.md."""
import json, sys, time
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
S = ROOT / 'scripts'
FRONT = ROOT / 'frontend'
MAX_IMG = 160_000          # hard per-image cap (target 60–120 KB)
MAX_TOTAL = 60 * 1024**2   # whole library cap
MAX_CATALOG = 1024**2      # catalog.json cap
PRESS = ['vnexpress', 'tuoitre', 'thanhnien', 'dantri', 'vietnamnet', 'znews', 'baochinhphu', 'vtv', 'vov',
         'nhandan', 'laodong', 'tienphong', 'vietnamplus', 'baodautu', 'kinhtedothi', 'dsvn', 'vr.com.vn',
         'cafef', 'saigontimes', 'vietnamnews']
BRANDS = ['accor', 'ahstatic', 'marriott', 'ihg', 'hilton', 'sofitel', 'capella', 'banyantree', 'sixsenses',
          'victoriahotels', 'vinpearl', 'movenpick', 'radisson', 'sungroup', 'sunworld', 'azerai', 'regenthotels',
          'pullman', 'mgallery', 'garrya', 'muongthanh', 'intercontinental', 'cloudfront']
LIC = ('Ảnh thuộc bản quyền của chủ sở hữu (xem source_page). Lưu để hiển thị giới thiệu cơ sở; '
       'cần xin phép hoặc thay bằng ảnh do cơ sở cung cấp trước khi dùng cho quảng cáo thương mại.')


def kind(it, im):
    import ota_media_pipeline as p
    d = (im['source_domain'] + ' ' + p.domain(im['source_url'])).replace('-', '').replace('.', '')
    for a in it['match'][0]:
        c = p.compact(a)
        if len(c) >= 5 and c in d:
            return 'official'
    if any(b in d for b in BRANDS if b != 'cloudfront'):
        return 'official'
    if any(x in im['source_domain'] for x in PRESS):
        return 'press'
    return 'review/blog'


def main():
    sys.path.insert(0, str(S))
    props = json.loads((S / 'properties.json').read_text())
    ck = json.loads((S / 'checkpoint.json').read_text())
    items, total_bytes, problems = [], 0, []
    for it in props['items']:
        e = ck['done'].get(it['id'], {'images': [], 'status': 'missing', 'log': {}})
        imgs = []
        for im in e['images']:
            f = FRONT / im['path'][2:]
            if not f.exists():
                problems.append(f'missing file {f}')
                continue
            b = f.stat().st_size
            total_bytes += b
            if b > MAX_IMG:
                problems.append(f'{f} {b} bytes > cap')
            imgs.append(dict(path=im['path'], role='hero' if not imgs else 'gallery', width=im['width'], height=im['height'],
                             bytes=b, source_url=im['source_url'], source_page=im['source_page'],
                             source_domain=im['source_domain'], source_kind=kind(it, im),
                             credit=f"Nguồn: {im['source_domain'] or 'không rõ'}", license_note=LIC))
        n = len(imgs)
        status = 'complete' if n >= 4 else 'partial' if n else 'missing'
        note = {'complete': '', 'partial': f'Chỉ tìm được {n} ảnh đạt chuẩn & đúng cơ sở — cần bổ sung ảnh từ chủ cơ sở.',
                'missing': 'Chưa tìm được ảnh thực tế đạt chuẩn & xác minh đúng cơ sở — cần xin ảnh trực tiếp từ chủ cơ sở.'}[status]
        if e.get('note'):
            note = (note + ' ' + e['note']).strip()
        items.append(dict(id=it['id'], slug=it['slug'], name=it['name'], region=it['region'], region_name=it['region_name'],
                          province=it['province'], area=it['area'], category=it['category'], batch=it['batch'],
                          hero_image=imgs[0]['path'] if imgs else None, images=imgs, photo_count=n,
                          photo_status=status, notes=note))
    regions = [dict(slug=r['slug'], name=r['name'], province=r['province'], batch=r['batch'],
                    item_count=sum(i['region'] == r['slug'] for i in items)) for r in props['regions']]
    cat = dict(version=1, generated_at=time.strftime('%Y-%m-%dT%H:%M:%S+07:00'), site='BanlaTravel.vn',
               totals=dict(items=len(items), images=sum(i['photo_count'] for i in items),
                           complete=sum(i['photo_status'] == 'complete' for i in items),
                           partial=sum(i['photo_status'] == 'partial' for i in items),
                           missing=sum(i['photo_status'] == 'missing' for i in items), bytes=total_bytes),
               regions=regions, items=items)
    errs = sorted(Draft202012Validator(json.loads((S / 'catalog.schema.json').read_text()),
                                       format_checker=FormatChecker()).iter_errors(cat), key=str)
    for e in errs:
        problems.append(f"schema: {'/'.join(map(str, e.path))}: {e.message}")
    # every webp on disk must be referenced (no orphans)
    ref = {i['path'][2:] for x in items for i in x['images']}
    for f in (FRONT / 'assets' / 'places').rglob('*.webp'):
        if str(f.relative_to(FRONT)) not in ref:
            problems.append(f'orphan file {f.relative_to(ROOT)}')
    if total_bytes > MAX_TOTAL:
        problems.append(f'library {total_bytes} bytes > {MAX_TOTAL}')
    txt = json.dumps(cat, ensure_ascii=False, indent=1)
    if len(txt.encode()) > MAX_CATALOG:
        problems.append('catalog.json > 1 MB')
    (FRONT / 'catalog.json').write_text(txt + '\n')
    write_report(cat, ck, problems)
    print(json.dumps(cat['totals']), 'problems:', len(problems))
    for p in problems[:30]:
        print(' -', p)
    return 1 if problems else 0


def write_report(cat, ck, problems):
    L = ['# Báo cáo kho ảnh BanlaTravel.vn', '', f"Tạo lúc: {cat['generated_at']} (giờ Việt Nam, UTC+7)", '',
         f"Tổng: **{cat['totals']['items']} sản phẩm**, **{cat['totals']['images']} ảnh WebP** "
         f"({cat['totals']['bytes'] / 1024 / 1024:.1f} MB). Đủ 4–5 ảnh: {cat['totals']['complete']} · "
         f"Thiếu (1–3 ảnh): {cat['totals']['partial']} · Chưa có ảnh: {cat['totals']['missing']}.", '',
         '## Quy tắc đã áp dụng',
         '- Nguồn: website chính thức / trang thương hiệu, báo chí, blog review du lịch. Loại toàn bộ ảnh từ OTA (Booking, Agoda, Traveloka, Tripadvisor, Expedia, Trip.com, iVIVU, Mytour…), kho ảnh stock có watermark, Pinterest, YouTube, trang ảnh AI.',
         '- Xác minh đúng cơ sở: tiêu đề hoặc URL trang nguồn phải chứa tên riêng của cơ sở; sau đó rà mắt từng ảnh trên contact sheet, ảnh sai/nghi ngờ bị loại.',
         '- Quality gate: rộng ≥ 900px, tỷ lệ 1.3–1.9, loại ảnh mờ (phương sai Laplacian), ảnh phẳng/viền, ảnh trùng (dHash), từ khóa render/phối cảnh/logo/bản đồ.',
         '- WebP 1280px, quality 82 (tự hạ tối đa còn 64 nếu > 125 KB).', '',
         '## Bản quyền', '', 'Mỗi ảnh trong `frontend/catalog.json` có `source_url`, `source_page`, `credit`, `license_note`. Ảnh vẫn thuộc bản quyền chủ sở hữu; nên xin phép hoặc thay bằng ảnh do cơ sở cung cấp trước khi chạy quảng cáo.', '']
    for b in (1, 2, 3, 4):
        its = [i for i in cat['items'] if i['batch'] == b]
        L += [f'## Lô {b}', '', f"{len(its)} sản phẩm · {sum(i['photo_count'] for i in its)} ảnh · "
              f"đủ: {sum(i['photo_status']=='complete' for i in its)} · thiếu: {sum(i['photo_status']=='partial' for i in its)} · "
              f"chưa có: {sum(i['photo_status']=='missing' for i in its)}", '',
              '| # | Sản phẩm | Khu vực | Ảnh | Trạng thái | Nguồn chính |', '|---|---|---|---|---|---|']
        for n, i in enumerate(its, 1):
            doms = sorted({im['source_domain'] for im in i['images']})
            L.append(f"| {n} | {i['name']} | {i['region']} | {i['photo_count']} | {i['photo_status']} | {', '.join(doms[:3])} |")
        L.append('')
    low = [i for i in cat['items'] if i['photo_count'] < 4]
    L += ['## Cần bổ sung ảnh (< 4 ảnh)', '']
    L += [f"- {i['name']} ({i['region']}): {i['photo_count']} ảnh — {i['notes']}" for i in low] or ['- Không có']
    L += ['', '## Vướng mắc & ghi chú', '']
    L += [f'- {x}' for x in ck.get('blockers', [])] or ['- Không có']
    if problems:
        L += ['', '## Lỗi kiểm định', ''] + [f'- {p}' for p in problems]
    (S / 'media_report.md').write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    sys.exit(main())
