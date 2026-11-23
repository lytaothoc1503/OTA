"""Generate scripts/properties.json: the 86 BanlaTravel.vn catalogue items (4 batches, 16 regions)."""
import json, re, unicodedata, pathlib

def slug(s):
    s = s.replace('Đ', 'D').replace('đ', 'd')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

REGIONS = [
 # (batch, slug, name, province)
 (1, 'sapa', 'Sapa', 'Lào Cai'),
 (1, 'ta-xua', 'Tà Xùa', 'Sơn La'),
 (1, 'mu-cang-chai', 'Mù Cang Chải', 'Lào Cai (Yên Bái cũ)'),
 (1, 'lao-cai-khac', 'Lào Cai khác (Bắc Hà, Y Tý, TP. Lào Cai)', 'Lào Cai'),
 (2, 'ha-noi', 'Hà Nội', 'Hà Nội'),
 (2, 'ninh-binh', 'Ninh Bình', 'Ninh Bình'),
 (2, 'hue', 'Huế', 'TP. Huế'),
 (2, 'tau-di-san', 'Tuyến Tàu Di Sản & Du Lịch', 'Liên tỉnh'),
 (3, 'da-lat', 'Đà Lạt', 'Lâm Đồng'),
 (3, 'lam-dong-khac', 'Lâm Đồng khác (Bảo Lộc, Di Linh, Lạc Dương)', 'Lâm Đồng'),
 (3, 'vung-tau-thuy-van', 'Đường Thùy Vân – Vũng Tàu', 'TP. Hồ Chí Minh (Bà Rịa – Vũng Tàu cũ)'),
 (4, 'cam-ranh', 'Cam Ranh', 'Khánh Hòa'),
 (4, 'nha-trang', 'Nha Trang', 'Khánh Hòa'),
 (4, 'khanh-hoa-khac', 'Khánh Hòa khác (Ninh Hòa, Vạn Ninh / Điệp Sơn)', 'Khánh Hòa'),
 (4, 'phu-quoc', 'Phú Quốc', 'An Giang (Kiên Giang cũ)'),
 (4, 'an-giang', 'An Giang (Châu Đốc, Tri Tôn, Núi Cấm, Long Xuyên)', 'An Giang'),
]

# region, name, category, area, search place, tokens (all groups must match; '|' = alternatives), extra queries
P = [
 ('sapa', 'Hotel de la Coupole - MGallery', 'hotel', 'Sa Pa', 'Sapa', 'coupole', []),
 ('sapa', 'Silk Path Grand Sapa Resort & Spa', 'resort', 'Sa Pa', 'Sapa', 'silk path;sapa', []),
 ('sapa', "Pao's Sapa Leisure Hotel", 'hotel', 'Sa Pa', 'Sapa', 'pao;sapa', []),
 ('sapa', 'Sapa Jade Hill Resort & Spa', 'resort', 'Sa Pa', 'Sapa', 'jade hill', []),
 ('sapa', 'Lady Hill Sapa Resort', 'resort', 'Sa Pa', 'Sapa', 'lady hill', []),
 ('sapa', 'Viettrekking Sapa', 'homestay', 'Sa Pa', 'Sapa', 'viettrekking|viet trekking', []),
 ('sapa', 'Delasol Sapa Hotel', 'hotel', 'Sa Pa', 'Sapa', 'delasol', []),
 ('ta-xua', 'Cloud Forest Tà Xùa', 'homestay', 'Tà Xùa, Bắc Yên', 'Tà Xùa', 'cloud forest;ta xua|taxua', []),
 ('ta-xua', 'Tà Xùa Ecolodge', 'homestay', 'Tà Xùa, Bắc Yên', 'Sơn La', 'ecolodge|eco lodge;ta xua|taxua', []),
 ('ta-xua', 'À Lôi Homestay', 'homestay', 'Tà Xùa, Bắc Yên', 'Tà Xùa', 'a loi;ta xua|taxua|homestay', []),
 ('ta-xua', 'Mây Mơ Màng Homestay Tà Xùa', 'homestay', 'Tà Xùa, Bắc Yên', 'Tà Xùa', 'may mo mang', []),
 ('ta-xua', 'Tà Xùa Hills Homestay', 'homestay', 'Tà Xùa, Bắc Yên', 'Sơn La', 'ta xua hills|taxua hills', []),
 ('ta-xua', 'Nhà của An Homestay Tà Xùa', 'homestay', 'Tà Xùa, Bắc Yên', 'Tà Xùa', 'nha cua an;ta xua|taxua', []),
 ('mu-cang-chai', 'Garrya Mù Cang Chải', 'resort', 'Mù Cang Chải', 'Mù Cang Chải', 'garrya', []),
 ('mu-cang-chai', 'Le Champ Tu Le Resort Hot Spring & Spa', 'resort', 'Tú Lệ', 'Yên Bái', 'le champ|lechamp', []),
 ('mu-cang-chai', 'Mù Cang Chải Ecolodge', 'homestay', 'Mù Cang Chải', 'Yên Bái', 'ecolodge|eco lodge;mu cang chai', []),
 ('mu-cang-chai', 'Hello Mù Cang Chải Homestay', 'homestay', 'Mù Cang Chải', 'Yên Bái', 'hello mu cang chai|hello mucangchai', []),
 ('mu-cang-chai', 'A Páo Homestay Mù Cang Chải', 'homestay', 'Mù Cang Chải', 'Yên Bái', 'a pao;mu cang chai|mucangchai', []),
 ('lao-cai-khac', 'Mường Thanh Grand Lào Cai Hotel', 'hotel', 'TP. Lào Cai', 'Lào Cai', 'muong thanh;lao cai', []),
 ('lao-cai-khac', 'Sapaly Hotel Lào Cai', 'hotel', 'TP. Lào Cai', 'Lào Cai', 'sapaly', []),
 ('lao-cai-khac', 'Ngải Thầu Xanh Homestay', 'homestay', 'Y Tý, Bát Xát', 'Y Tý', 'ngai thau', []),
 ('lao-cai-khac', 'A Hờ Homestay', 'homestay', 'Y Tý, Bát Xát', 'Y Tý', 'a ho;y ty', []),
 ('lao-cai-khac', 'Bắc Hà Boutique Homestay', 'homestay', 'Bắc Hà', 'Bắc Hà Lào Cai', 'bac ha;boutique', []),
 ('ha-noi', 'Sofitel Legend Metropole Hanoi', 'hotel', 'Hoàn Kiếm', 'Hanoi', 'metropole', []),
 ('ha-noi', 'Capella Hanoi', 'hotel', 'Hoàn Kiếm', 'Hanoi', 'capella;hanoi|ha noi', []),
 ('ha-noi', 'JW Marriott Hotel Hanoi', 'hotel', 'Nam Từ Liêm', 'Hanoi', 'jw marriott;hanoi|ha noi', []),
 ('ha-noi', 'InterContinental Hanoi Westlake', 'hotel', 'Tây Hồ', 'Hanoi', 'intercontinental;westlake|west lake|ho tay', []),
 ('ha-noi', 'La Siesta Classic Ma May Hotel', 'hotel', 'Hoàn Kiếm', 'Hanoi', 'la siesta;ma may', []),
 ('ninh-binh', 'Emeralda Resort Tam Coc', 'resort', 'Tam Cốc, Hoa Lư', 'Ninh Binh', 'emeralda;tam coc', []),
 ('ninh-binh', 'Tam Coc Garden Resort', 'resort', 'Tam Cốc, Hoa Lư', 'Ninh Binh', 'tam coc garden', []),
 ('ninh-binh', 'Ninh Binh Hidden Charm Hotel & Resort', 'resort', 'Hoa Lư', 'Ninh Binh', 'hidden charm', []),
 ('ninh-binh', 'Vedana Resort Ninh Binh', 'resort', 'Cúc Phương', 'Ninh Binh', 'vedana;ninh binh', []),
 ('ninh-binh', 'Aravinda Resort Ninh Binh', 'resort', 'Gia Viễn', 'Ninh Binh', 'aravinda', []),
 ('ninh-binh', 'Clau Hotel Ninh Bình', 'hotel', 'TP. Ninh Bình', 'Ninh Bình', 'clau', []),
 ('ninh-binh', 'Phố Cổ Hotel Ninh Bình', 'hotel', 'Ninh Bình', 'Ninh Bình', 'pho co hotel|khach san pho co|phoco hotel;ninh binh', []),
 ('hue', 'Azerai La Residence, Hue', 'hotel', 'TP. Huế', 'Hue', 'azerai|la residence;hue', []),
 ('hue', 'Banyan Tree Lang Co', 'resort', 'Lăng Cô, Chân Mây', 'Lang Co', 'banyan tree;lang co', []),
 ('hue', 'Vedana Lagoon Resort & Spa', 'resort', 'Phá Tam Giang – Cầu Hai', 'Hue', 'vedana lagoon', []),
 ('hue', 'Pilgrimage Village Boutique Resort & Spa', 'resort', 'TP. Huế', 'Hue', 'pilgrimage village', []),
 ('hue', 'Indochine Palace', 'hotel', 'TP. Huế', 'Hue hotel', 'indochine palace', []),
 ('tau-di-san', 'Tàu Di Sản Kết Nối Miền Trung (Huế – Đà Nẵng: HĐ1/HĐ2/HĐ3/HĐ4)', 'train', 'Huế – Đà Nẵng', 'Kết nối di sản miền Trung tàu Huế Đà Nẵng', 'tau|train|toa;di san|heritage', ['tàu Kết nối di sản miền Trung toa xe', 'tàu HĐ1 HĐ2 Huế Đà Nẵng đèo Hải Vân', 'Hue Da Nang heritage train carriage']),
 ('tau-di-san', 'Tàu Du Lịch Di Sản Huế – Phong Nha (HQ1/HQ2)', 'train', 'Huế – Đồng Hới (Quảng Trị)', 'tàu du lịch Huế Phong Nha', 'tau|train|toa;phong nha|dong hoi', ['tàu HQ1 HQ2 Huế Đồng Hới', 'tàu di sản Huế Phong Nha khai trương']),
 ('tau-di-san', 'Tàu Du Lịch 5 Cửa Ô Hà Nội (The Hanoi Train)', 'train', 'Hà Nội', 'tàu du lịch 5 cửa ô Hà Nội', 'tau|train|toa;cua o|hanoi train', ['The Hanoi Train 5 cửa ô toa xe', 'tàu 5 cửa ô Hà Nội nội thất']),
 ('tau-di-san', 'Tàu Hỏa Hạng Sang SJourney (Xuyên Việt khởi hành từ Hà Nội)', 'train', 'Hà Nội – TP.HCM', 'SJourney tàu hạng sang', 'sjourney|s journey', ['SJourney luxury train Vietnam', 'tàu SJourney toa xe hạng sang']),
 ('tau-di-san', 'Tàu Du Lịch Đêm Đà Lạt – Trại Mát (ĐL11/ĐL12)', 'train', 'Đà Lạt – Trại Mát', 'tàu đêm Đà Lạt Trại Mát', 'tau|train|toa|ga;trai mat|da lat|dalat', ['ga Đà Lạt tàu đêm Trại Mát', 'tàu ĐL11 ĐL12 Đà Lạt']),
 ('da-lat', 'MerPerle Dalat Hotel', 'hotel', 'Đà Lạt', 'Dalat', 'merperle|mer perle', []),
 ('da-lat', 'Grand Mercure Dalat', 'hotel', 'Đà Lạt', 'Dalat', 'grand mercure;dalat|da lat', []),
 ('da-lat', 'Ana Mandara Villas Dalat Resort & Spa', 'resort', 'Đà Lạt', 'Dalat', 'ana mandara;dalat|da lat', []),
 ('da-lat', 'Hôtel Colline Đà Lạt', 'hotel', 'Đà Lạt', 'Dalat', 'colline', []),
 ('da-lat', 'Dalat Wonder Resort', 'resort', 'Hồ Tuyền Lâm, Đà Lạt', 'Dalat', 'wonder;dalat|da lat', []),
 ('lam-dong-khac', 'Đôi Dép Tea Resort', 'resort', 'Bảo Lộc', 'Bảo Lộc', 'doi dep', []),
 ('lam-dong-khac', 'Sandals Vista Hotel', 'hotel', 'Bảo Lộc', 'Bảo Lộc', 'sandals vista', []),
 ('lam-dong-khac', 'Memories Hotel Bảo Lộc', 'hotel', 'Bảo Lộc', 'Bảo Lộc', 'memories;bao loc', []),
 ('lam-dong-khac', 'Twin Beans Farm', 'homestay', 'Lạc Dương', 'Đà Lạt', 'twin beans', []),
 ('lam-dong-khac', 'Zenna Glamping & Farm', 'homestay', 'Lạc Dương', 'Đà Lạt', 'zenna', []),
 ('vung-tau-thuy-van', 'The IMPERIAL Hotel Vung Tau', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vung Tau', 'imperial;vung tau', []),
 ('vung-tau-thuy-van', 'Vias Hotel Vung Tau', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vung Tau', 'vias', []),
 ('vung-tau-thuy-van', 'Pullman Vung Tau', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vung Tau', 'pullman;vung tau', []),
 ('vung-tau-thuy-van', 'Malibu Hotel Vung Tau', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vung Tau', 'malibu;vung tau', []),
 ('vung-tau-thuy-van', 'Premier Pearl Hotel Vung Tau', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vung Tau', 'premier pearl', []),
 ('vung-tau-thuy-van', 'Thùy Vân Hotel', 'hotel', 'Thùy Vân, Vũng Tàu', 'Vũng Tàu', 'thuy van hotel|khach san thuy van', []),
 ('cam-ranh', 'The Anam Cam Ranh', 'resort', 'Bãi Dài, Cam Ranh', 'Cam Ranh', 'anam', []),
 ('cam-ranh', 'Alma Resort Cam Ranh', 'resort', 'Bãi Dài, Cam Ranh', 'Cam Ranh', 'alma;cam ranh', []),
 ('cam-ranh', 'Mövenpick Resort Cam Ranh', 'resort', 'Bãi Dài, Cam Ranh', 'Cam Ranh', 'movenpick;cam ranh', []),
 ('cam-ranh', 'Fusion Resort Cam Ranh', 'resort', 'Bãi Dài, Cam Ranh', 'Cam Ranh', 'fusion;cam ranh', []),
 ('cam-ranh', 'Radisson Blu Resort Cam Ranh', 'resort', 'Bãi Dài, Cam Ranh', 'Cam Ranh', 'radisson;cam ranh', []),
 ('nha-trang', 'Six Senses Ninh Van Bay', 'resort', 'Vịnh Ninh Vân', 'Nha Trang', 'six senses;ninh van', []),
 ('nha-trang', 'Amiana Resort Nha Trang', 'resort', 'Nha Trang', 'Nha Trang', 'amiana', []),
 ('nha-trang', 'Vinpearl Resort & Spa Nha Trang Bay', 'resort', 'Hòn Tre, Nha Trang', 'Nha Trang', 'vinpearl;nha trang', []),
 ('nha-trang', 'InterContinental Nha Trang', 'hotel', 'Trần Phú, Nha Trang', 'Nha Trang', 'intercontinental;nha trang', []),
 ('nha-trang', 'Mia Resort Nha Trang', 'resort', 'Bãi Đông, Cam Lâm', 'Nha Trang', 'mia;nha trang', []),
 ('khanh-hoa-khac', 'An Lam Retreats Ninh Van Bay', 'resort', 'Vịnh Ninh Vân, Ninh Hòa', 'Nha Trang', 'an lam', []),
 ('khanh-hoa-khac', "L'Alya Ninh Van Bay", 'resort', 'Vịnh Ninh Vân, Ninh Hòa', 'Nha Trang', 'alya', []),
 ('khanh-hoa-khac', 'GM Doc Let Beach Resort & Spa', 'resort', 'Dốc Lết, Ninh Hòa', 'Ninh Hòa', 'gm doc let|gm doclet', []),
 ('khanh-hoa-khac', 'Pax Ana Doc Let Resort & Spa', 'resort', 'Dốc Lết, Ninh Hòa', 'Ninh Hòa', 'pax ana', []),
 ('khanh-hoa-khac', 'Whale Island Resort (Đảo Cá Ông – Vịnh Vân Phong)', 'resort', 'Đảo Hòn Ông, Vạn Ninh', 'Van Phong Nha Trang', 'whale island|dao ca ong|hon ong', []),
 ('phu-quoc', 'La Festa Phu Quoc, Curio Collection by Hilton', 'hotel', 'Sunset Town, An Thới', 'Phu Quoc', 'la festa', []),
 ('phu-quoc', 'JW Marriott Phu Quoc Emerald Bay Resort & Spa', 'resort', 'Bãi Khem, An Thới', 'Phu Quoc', 'jw marriott;phu quoc', []),
 ('phu-quoc', 'Premier Village Phu Quoc Resort', 'resort', 'Mũi Ông Đội, An Thới', 'Phu Quoc', 'premier village;phu quoc', []),
 ('phu-quoc', 'Regent Phu Quoc', 'resort', 'Bãi Trường', 'Phu Quoc', 'regent;phu quoc', []),
 ('phu-quoc', 'Vé Show & Sự Kiện Sunset Town (Kiss of the Sea, Symphony of the Sea, Cầu Hôn, Cáp treo Hòn Thơm)', 'ticket', 'Sunset Town / Hòn Thơm, An Thới', 'Phú Quốc', 'kiss of the sea|symphony of the sea|hon thom|sunset town|cau hon', ['Kiss of the Sea show Phú Quốc', 'Symphony of the Sea Sunset Town', 'cáp treo Hòn Thơm Phú Quốc', 'Cầu Hôn Sunset Town Phú Quốc']),
 ('an-giang', 'Victoria Nui Sam Lodge', 'resort', 'Núi Sam, Châu Đốc', 'Chau Doc', 'nui sam;victoria|lodge', []),
 ('an-giang', 'Victoria Chau Doc Hotel', 'hotel', 'Châu Đốc', 'Chau Doc', 'victoria;chau doc', []),
 ('an-giang', 'Sang Như Ngọc Resort (Núi Cấm)', 'resort', 'Núi Cấm, Tịnh Biên', 'Núi Cấm', 'sang nhu ngoc', []),
 ('an-giang', 'Bến Đá Núi Sam Hotel', 'hotel', 'Núi Sam, Châu Đốc', 'Châu Đốc', 'ben da;nui sam|chau doc', []),
 ('an-giang', 'Đông Xuyên Hotel (Long Xuyên)', 'hotel', 'Long Xuyên', 'Long Xuyên', 'dong xuyen', []),
]

reg = {r[1]: r for r in REGIONS}
items = []
for i, (rs, name, cat, area, place, tok, extra) in enumerate(P, 1):
    b, _, rname, prov = reg[rs]
    base = re.sub(r'\s*\(.*\)$', '', name)
    sl = slug(base)
    if rs == 'tau-di-san' or cat == 'ticket':
        sl = slug(base)[:60].strip('-')
    items.append(dict(id=f'{rs}-{sl}' if not sl.startswith(rs) else sl, slug=sl, seq=i, name=name, batch=b,
                      region=rs, region_name=rname, province=prov, area=area, category=cat,
                      search_place=place, match=[g.split('|') for g in tok.split(';')], extra_queries=extra))
assert len(items) == 86, len(items)
assert len({x['id'] for x in items}) == 86
for b in (1, 2, 3, 4):
    print('batch', b, sum(x['batch'] == b for x in items))
out = pathlib.Path(__file__).with_name('properties.json')
out.write_text(json.dumps(dict(regions=[dict(batch=r[0], slug=r[1], name=r[2], province=r[3]) for r in REGIONS], items=items), ensure_ascii=False, indent=1))
print('wrote', out)
