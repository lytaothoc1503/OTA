# GROK BOT HANDOVER SPECIFICATION — CLOUDFLARE WORKER & GITHUB DEPLOYMENT
**Project:** `BANLA // NOMAD` — Direct Booking & Telegram Order Bridge (`@CSN1503_ai_Bot`)
**Governance Mode:** STRICT HUMAN-IN-THE-LOOP (Cấm tự ý đẩy Secret công khai / Cấm sửa giá & số tài khoản ngân hàng)

---

## 1. MỤC TIÊU NHIỆM VỤ
Bạn là **DevOps & Browser Automation Agent** vận hành trên máy tính đám mây / trình duyệt. Nhiệm vụ của bạn là triển khai hệ thống nhận đơn đặt phòng từ `frontend/index.html` qua **Cloudflare Workers** (để giấu kín Bot Token) và xuất bản giao diện tĩnh lên **GitHub Pages** (`lytaothoc1503`), tuân thủ tuyệt đối các cổng dừng kiểm duyệt (Checkpoints) bên dưới.

---

## 2. QUY TẮC CHỐNG ẢO GIÁC & BẢO MẬT (ANTI-HALLUCINATION & SECURITY CONSTRAINTS)
1. **KHÔNG BAO GIỜ** ghi cứng `TG_BOT_TOKEN` vào `frontend/index.html`, `wrangler.toml`, commit message hay bất kỳ file nào đẩy lên GitHub.
2. **KHÔNG ĐƯỢC TỰ Ý SỬA** bảng giá VND niêm yết (`4.690.000₫`, `6.090.000₫`, `3.190.000₫`) hoặc thông tin tài khoản ngân hàng thụ hưởng VietQR khi chưa có lệnh xác nhận của Admin.
3. Trước khi bấm nút **Deploy** trên Cloudflare hoặc **git push** lên nhánh chính của GitHub, bắt buộc dừng lại ở **CHECKPOINT** và báo cáo thông số để Admin duyệt.

---

## 3. QUY TRÌNH THỰC THI TỪNG BƯỚC (STEP-BY-STEP WORKFLOW)

### BƯỚC 1 — Kiểm tra an toàn mã nguồn (`Secret Scan`)
- Đọc file `frontend/index.html` và `cloudflare-worker/worker.js`.
- Xác minh chuỗi token Telegram **không tồn tại** dưới dạng văn bản cứng trong `frontend/index.html`.
- Ghi nhận trạng thái `[SCAN PASS]` trước khi sang Bước 2.

### BƯỚC 2 — Triển khai Cloudflare Worker Proxy (`banla-order-bridge`)
1. Mở trình duyệt vào **Cloudflare Dashboard** -> mục **Workers & Pages** -> **Create Worker**.
2. Đặt tên Worker: `banla-order-bridge`.
3. Dán toàn bộ nội dung file `cloudflare-worker/worker.js` vào trình sửa code của Worker.
4. **🛑 CHECKPOINT 1 (DỪNG CHỜ ADMIN):**
   - Báo cho Admin đường dẫn Worker dự kiến: `https://banla-order-bridge.<subdomain>.workers.dev`.
   - Hướng dẫn hoặc mở sẵn mục **Settings -> Variables and Secrets -> Add Secret (Encrypted)** để nạp 2 biến bảo mật:
     - `TG_BOT_TOKEN` *(lấy mã mới sau khi đã `/revoke` trên `@BotFather`)*
     - `TG_CHAT_ID` *(Chat ID cá nhân hoặc nhóm nhận đơn của Admin)*
   - Chờ Admin gõ `"DUYỆT CF"` mới tiếp tục.

### BƯỚC 3 — Kích hoạt Webhook 2 chiều cho nút `[✅ Duyệt cọc]` / `[❌ Báo hết phòng]` (Tuỳ chọn Serverless 24/7)
- Nếu chạy 24/7 trên Cloudflare (không cần bật máy tính chạy `bot_listener.py`), gọi URL kích hoạt Webhook (chỉ chạy sau khi Admin đã duyệt):
  `https://api.telegram.org/bot<TG_BOT_TOKEN>/setWebhook?url=https://banla-order-bridge.<subdomain>.workers.dev/telegram-webhook`
- Kiểm tra phản hồi JSON trả về `{"ok": true, "result": true}`.

### BƯỚC 4 — Cập nhật Endpoint vào `frontend/index.html` & Đẩy lên GitHub (`lytaothoc1503`)
1. Trong `frontend/index.html`, gán hằng số `DEFAULT_PROXY_WEBHOOK_URL` bằng đúng URL Worker vừa tạo:
   `https://banla-order-bridge.<subdomain>.workers.dev/order`
2. Kiểm tra file `.gitignore` đã chặn `.env` và `*.jsonl`.
3. **🛑 CHECKPOINT 2 (DỪNG CHỜ ADMIN TRƯỚC KHI PUSH GITHUB):**
   - Hiển thị kết quả `git status` và `git diff` tóm tắt (tên repo đích, nhánh `main`, URL Worker đã gắn, xác nhận 0 secret rò rỉ).
   - Chờ Admin gõ `"DUYỆT PUSH"` rồi mới thực thi `git commit` & `git push` và bật **GitHub Pages**.

### BƯỚC 5 — Kiểm thử đầu-cuối (End-to-End Smoke Test)
- Mở trang GitHub Pages vừa xuất bản, tạo 1 đơn thử nghiệm với tên `TEST SYSTEM` và ghi chú `Smoke Test Grok Bot`.
- Xác nhận banner báo xanh `✓ Đã bắn đơn qua Proxy Webhook` và tin nhắn có nút `[✅ Duyệt cọc]` / `[❌ Báo hết phòng]` nổ về `@CSN1503_ai_Bot`.
