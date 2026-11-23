---
name: framer-ota-ui
description: Chuẩn thiết kế vĩnh viễn cho BanlaTravel.vn (frontend/index.html) theo phong cách Framer.com / Spatial Travel UI — font, hệ màu Sky Blue + Cloud White + Scarlet, kính mờ, vật lý lò xo, thư viện chuyển động và các quy tắc bất biến về nghiệp vụ đặt phòng. Dùng khi sửa, thêm tính năng hoặc nghiệm thu giao diện website OTA này.
---

# Framer OTA UI — Chuẩn thiết kế BanlaTravel.vn

Áp dụng cho mọi thay đổi giao diện trong `frontend/index.html`. Mục tiêu: đẹp, sang trọng, có chiều sâu 3D, chuyển động vật lý mượt **60fps** trên cả Desktop và Mobile (375px – 430px).

## 1. Font chữ
| Vai trò | Font | Ghi chú |
|---|---|---|
| Tiêu đề (`h1–h4`, logo, `.font-display`) | **Plus Jakarta Sans** 500–800 | đậm, hiện đại, `letter-spacing: -.015em` |
| Nội dung, nút, form, **số tiền** | **Inter** 400–800 | sắc nét |
| Giá tiền / số đêm / mã đơn | Inter + `font-variant-numeric: tabular-nums` | đang bật trên `body` để chữ số thẳng hàng |

- Tailwind: `fontFamily.sans = Inter`, `fontFamily.display = Plus Jakarta Sans`.
- Luôn dùng `display=swap`; không thêm font thứ ba.

## 2. Hệ màu 60-30-10 (Sky Blue + Cloud White + Scarlet)
Phong cách **Bầu trời tươi mới & Điểm nhấn Đỏ Scarlet**. Phân bổ trên toàn giao diện: **60% Cloud White · 30% Sky Blue · 10% Scarlet Red**.

### CSS Variables (bắt buộc có trong `:root`)
```css
:root {
  /* 60% — Cloud White */
  --bg-main: #F8FAFC;
  --bg-surface: #FFFFFF;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  /* 30% — Sky Blue */
  --brand-sky: #329DD2;
  --brand-sky-deep: #1E78A8;
  --brand-sky-soft: #E0F2FE;
  --brand-sky-light: #5BB8E8; /* gradient / aurora */
  /* 10% — Scarlet Red */
  --accent-scarlet: #EB2F33;
  --accent-scarlet-hover: #C81E22;
  --accent-scarlet-soft: #FEE2E2;
}
```

### Token Tailwind / alias (giữ tên cũ để không phá class hiện có)
| Token | Giá trị | Dùng cho |
|---|---|---|
| Nền trang (`ota-bg` / `--bg-main`) | `#F8FAFC` | `body`, khoảng trống giữa các khối |
| Surface (`--bg-surface`) | `#FFFFFF` | thẻ phòng, modal, bảng giá, search dock |
| Chữ chính (`booking-navy` / `--text-primary`) | `#0F172A` | tiêu đề, chữ đậm — **WCAG AA trên nền sáng** |
| Chữ phụ (`--text-secondary`) | `#475569` | mô tả, meta |
| Xanh thương hiệu (`ota-blue` / `--brand-sky`) | `#329DD2` | liên kết, điểm đánh giá, tiện ích, focus, slider, ghim mặc định, tab chọn, nút phụ |
| Xanh đậm (`brand-sky-deep`) | `#1E78A8` | hover nút xanh, chiều sâu gradient |
| Xanh nhạt (`brand-sky-soft`) | `#E0F2FE` | badge tiện ích, trạng thái chọn, chip lọc |
| Xanh trời gradient (`traveloka-sky`) | `#5BB8E8` | Aurora Sky Mesh, gradient hero |
| CTA Scarlet (`ota-amber` / `agoda-red` / `--accent-scarlet`) | `#EB2F33` (hover `#C81E22`) | **Đơn đặt**, **Tìm phòng**, **Đặt ngay**, **Xác nhận / Thanh toán VietQR**, giá cuối, badge `-%`, ghim map khi hot |
| Scarlet soft (`accent-scarlet-soft`) | `#FEE2E2` | nhãn cảnh báo khan hiếm |
| Vàng sao (`ota-gold`) | `#FFB700` | sao đánh giá, nhấn nhỏ |
| Footer / promo strip tối (`booking-dark`) | `#0B1324` | footer; thanh promo có thể dùng Sky |

### Phân bổ điểm nhấn (bắt buộc)
- **Scarlet `#EB2F33`:** CTA chính (Đơn đặt, Tìm phòng, Đặt ngay, thanh toán), giá tiền cuối, badge giảm `-%`, ghim bản đồ khi hover thẻ phòng, nhãn “Chỉ còn N phòng”.
- **Sky `#329DD2`:** badge điểm (9.8 Tuyệt hảo), icon/viền tiện ích, focus ring, nút “Xem chi tiết / Xem phòng”, dual-range slider, ghim giá mặc định (nền trắng + viền sky).
- **Không** dùng cam `#F97316` làm CTA nữa — đã thay bằng Scarlet.

### Hero & Header (Light Glass + Aurora Sky Mesh)
- **Hero:** gradient `#329DD2` → `#5BB8E8` → `#F8FAFC` (Aurora Sky Mesh); quả cầu 3D trắng ngọc / xanh da trời trong suốt; chữ tiêu đề tối (`--text-primary`), không nền hero tối.
- **Header kính mờ sáng:** `rgba(248, 250, 252, 0.85)` + `backdrop-filter: blur(20px)`; menu chữ tối; tab đang chọn nền/gạch chân `#329DD2`.
- **Search dock nổi:** nền `#FFFFFF`, đổ bóng mềm; tab chọn nền `#329DD2` chữ trắng; nút **Tìm phòng** Scarlet + `box-shadow: 0 8px 20px rgba(235, 47, 51, 0.3)`.

Kính mờ (glass) — dùng cho header nổi, dock tìm kiếm, popover:
```css
backdrop-filter: blur(20px) saturate(1.5);
border: 1px solid rgba(255,255,255,.55);
box-shadow: inset 0 1px 0 rgba(255,255,255,.7), 0 12px 24px -6px rgba(15, 23, 42, .12), 0 40px 80px -20px rgba(15, 23, 42, .18);
```
- Không đặt `backdrop-filter` lên phần tử lớn đang animate liên tục; không lồng quá 2 lớp kính.
- Mọi chữ trên nền sáng phải đạt **WCAG AA** (tối thiểu `#0F172A` trên `#F8FAFC` / `#FFFFFF`; `#475569` cho chữ phụ).

## 3. Vật lý chuyển động (Framer Spring Physics)
```css
--spring-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);  /* nảy tự nhiên: nút, thẻ, pill, chip */
--spring-smooth: cubic-bezier(0.22, 1, 0.36, 1);     /* êm: reveal, trượt ảnh, popover */
```
- **Nhấn & thả:** mọi `button` và `a[class*="rounded-xl"]` — `:active { scale: .95 }` rồi nhả bật nảy về `1` (dùng thuộc tính `scale` độc lập, không đè `transform`).
- **Kéo thả có quán tính (chuột):** slider khuyến mãi / điểm đến. Lò xo giảm chấn `K = 190`, `C = 21`, vận tốc thả × 240ms để chọn thẻ, rồi hít (elastic snap) vào thẻ gần nhất. Cảm ứng dùng cuộn gốc của trình duyệt (đã có quán tính). Chặn click sau khi kéo > 5px.
- **Nghiêng 3D + glare:** thẻ nổi bật & E-Voucher, tối đa 6–9°, `perspective(1000px)`; rời chuột trả về phẳng bằng `--spring-bounce`.
- **Reveal khi cuộn:** `translateY(24px) → 0` + `opacity`, trễ nối tiếp 70ms/phần tử (tối đa 8 bước).
- **Sliding pill:** dock tabs, chuyển bằng `transform` + `--spring-bounce`.
- **Chỉ animate `transform` và `opacity`** (kèm `scale`/`translate`). Không animate `width/height/top/left/box-shadow` liên tục. `will-change` chỉ đặt khi đang tương tác.
- **Tôn trọng `prefers-reduced-motion: reduce`:** tắt parallax, tilt, reveal, aurora, Lenis, confetti, spring.

## 4. Thư viện chuyển động (nhúng nhẹ, không chặn hiển thị)
| Thư viện | Phiên bản (ghim cứng) | Dùng cho |
|---|---|---|
| **Lenis** | `1.3.4` — `dist/lenis.min.js` | cuộn quán tính toàn trang |
| **Motion One** (`motion`) | `10.18.0` — `dist/motion.min.js` | spring cho lightbox, vào màn hình E-Voucher |

Quy tắc:
- Nạp **bất đồng bộ** bằng script động (jsDelivr → dự phòng unpkg), timeout 8s mỗi nguồn, **có `integrity` (SRI sha384)**. Tuyệt đối không dùng thẻ `<script src>` chặn render. Nếu CDN lỗi, website vẫn chạy đầy đủ (CSS/JS thuần).
- SRI hiện hành: Lenis `sha384-FKTX0CNJ8ngN1oGMBReVu7mvjTJyjFiD5etb1NKnYxc+8eFI2O0KWnksTN+oTFcu`; Motion `sha384-Yqz+BqPRR4A0raMrkHbKigm/8NYHfFXmYdcEoZ5qhPPjpYxIFfDxEuHMdTIoZ+c5`. Nâng phiên bản ⇒ tính lại hash.
- **Lenis phải `stop()` khi mở lightbox/modal và `start()` khi đóng** (`lockScroll`). Vùng tự cuộn bên trong (bộ lọc mobile, danh sách bản đồ) gắn `data-lenis-prevent`. Cuộn lập trình dùng `jumpTo()` / `scrollToEl()`, không gọi `window.scrollTo` trực tiếp.
- Leaflet (bản đồ) cũng nạp theo yêu cầu, có CDN dự phòng.

## 5. Cấu trúc SPA
Hash routes: `#/` · `#/search` · `#/property/:id` · `#/checkout` · `#/checkout/:orderCode` · `#/bookings`. State (số đêm, số khách, yêu thích, đơn đặt, voucher) lưu `localStorage` và dùng chung xuyên trang.

## 6. QUY TẮC BẤT BIẾN (không được phá khi chỉnh giao diện)
1. **Giỏ phòng & tính tiền:** `roomNightly`, `roomLine`, `calcTotals`, đặt cọc 30% / 100%, giữ phòng 15 phút.
2. **Chiết khấu theo số đêm:** 1 đêm −5% · 2 đêm −10% · 3+ đêm −15% (`getNightDiscountRate`); gói combo trọn gói không chiết khấu.
3. **Mã giảm giá:** `BANLA10` (−10%), `CLOUDVIP` (−300.000₫).
4. **VietQR MB Bank:** ngân hàng `MB`, số tài khoản `0901650888`, tên `BANLA NOMAD EXPEDITIONS`, tự điền số tiền + nội dung = mã đơn.
5. **Gửi Telegram (giữ nguyên 100%):** `postOrder()` / `markPaid()` gửi `POST` JSON `{ source: 'BanlaTravel OTA', order }` tới `DEFAULT_PROXY_WEBHOOK_URL` (Cloudflare Worker `/order`), có tự phục hồi về Worker khi URL local lỗi. Khóa của `order`: `orderCode, customer{name,phone,date,guests,note}, items[{id,name,priceVnd,priceUsd,qty}], voucherCode, discountVnd, totalVnd, totalUsd, paymentMethod, depositRatio, payNowVnd`. Chỉ được thêm cờ hiển thị, **không** đổi cấu trúc payload, không đụng `worker.js` / `bot_listener.py` khi chỉ sửa giao diện.
6. **Bảo mật:** không bao giờ ghi cứng `TG_BOT_TOKEN`, `GEMINI_API_KEY` hay bất kỳ bí mật nào vào frontend; bí mật chỉ nằm ở Cloudflare Secrets / `.env` (đã `.gitignore`).
7. **Header:** không hiện nhãn `@CSN1503_ai_Bot`; dùng nút "Hỗ trợ 24/7" (popover hotline `0358 341 934`, Zalo, Telegram).
8. **Giá/giảm giá/thông tin tài khoản** không được tự ý sửa khi chỉ làm giao diện.

## 7. Checklist nghiệm thu trước khi push
- [ ] Không lỗi console, không request lỗi (trừ khi cố ý chặn CDN để thử dự phòng).
- [ ] Payload gửi Telegram đúng 10 khóa như mục 6.5 (chặn request khi test, **không gửi đơn thật**).
- [ ] CDN Lenis/Motion bị chặn ⇒ trang vẫn hiển thị và đặt phòng bình thường.
- [ ] `prefers-reduced-motion: reduce` ⇒ không reveal/parallax/Lenis.
- [ ] Mobile 375–430px: không tràn ngang; bộ lọc toàn màn hình mở/đóng được; nút ≥ 36px.
- [ ] Lightbox mở ⇒ Lenis dừng; đóng ⇒ cuộn lại bình thường.
- [ ] Quét bí mật trong phần commit = 0; `.env` không bị theo dõi.
- [ ] Chữ trên nền sáng đạt WCAG AA (`#0F172A` / `#475569` trên Cloud White).
- [ ] CTA chính là Scarlet `#EB2F33`; brand/score/slider/ghim mặc định là Sky `#329DD2`.
- [ ] Chụp ảnh Desktop + Mobile của hero, thẻ tilt, bản đồ, lightbox, E-Voucher để xem bằng mắt.
