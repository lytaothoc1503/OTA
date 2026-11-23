# BANLA // NOMAD — Bộ Mã Nguồn OTA & Telegram Bot (`@CSN1503_ai_Bot`)

Thư mục này được đóng gói sẵn để chạy ngay trên máy Windows 11 (Local) hoặc triển khai lên **Cloudflare Workers + GitHub Pages** an toàn tuyệt đối (không lộ Bot Token trên mã nguồn công khai).

---

## Cấu trúc thư mục

```text
banla-nomad-ota-bot-kit/
├── README.md                          # Tài liệu hướng dẫn sử dụng nhanh
├── .gitignore                         # Chặn đẩy nhầm .env và file log lên GitHub
├── frontend/
│   └── index.html                     # Giao diện đặt chỗ + VietQR + kết nối Proxy/Local Bot (Đã gỡ cứng Token)
├── cloudflare-worker/
│   ├── worker.js                      # Proxy ẩn Token + Xử lý nút [✅ Duyệt cọc] / [❌ Báo hết phòng] 24/7
│   └── wrangler.toml                  # File cấu hình Cloudflare Worker
├── local-telegram-bot/
│   ├── bot_listener.py                # Bot Python chạy trên máy tính (không cần cài thư viện ngoài)
│   ├── .env.example                   # File mẫu cấu hình Token & Chat ID
│   └── requirements.txt               # Ghi chú môi trường Python
└── prompts/
    └── grok_bot_deploy_handover.md    # Prompt chuẩn giao việc cho Grok Bot tự động mở Cloudflare & GitHub
```

---

## Cách 1: Chạy ngay trên máy tính Windows 11 (Local Python Bot có nút Duyệt cọc)

1. **Đổi lại Token mới để bảo mật:** Mở `@BotFather` trên Telegram -> gõ `/revoke` -> chọn `@CSN1503_ai_Bot` để lấy mã Token mới.
2. Vào thư mục `local-telegram-bot/`, nhân bản file `.env.example` thành `.env` và dán `TG_BOT_TOKEN` vào.
3. Mở Terminal / PowerShell tại thư mục `local-telegram-bot/` và chạy:
   ```bash
   python bot_listener.py
   ```
4. Mở Telegram `@CSN1503_ai_Bot` bấm `/start` -> cửa sổ Terminal sẽ tự nhận `TG_ADMIN_CHAT_ID` và mở cổng nhận đơn nội bộ tại `http://127.0.0.1:8787/order`.
5. Mở file `frontend/index.html` trên trình duyệt -> Tạo đơn thử -> Tin nhắn sẽ nổ về Telegram kèm 2 nút bấm trực tiếp:
   - **[✅ Duyệt cọc]**
   - **[❌ Báo hết phòng]**
   - **[💬 Mở Zalo khách]**
   *(Mọi lịch sử đơn và người bấm duyệt đều được lưu tự động vào `local-telegram-bot/orders_audit.jsonl`).*

---

## Cách 2: Đưa lên Online 24/7 bằng Cloudflare Worker + GitHub Pages (Dùng Grok Bot)

1. Mở file `prompts/grok_bot_deploy_handover.md`, copy toàn bộ nội dung dán cho **Grok Bot**.
2. Grok Bot sẽ dựng `cloudflare-worker/worker.js` lên Cloudflare, dừng lại ở các cổng **Checkpoint** để bạn nạp `TG_BOT_TOKEN` & `TG_CHAT_ID` vào mục Secret mã hóa, sau đó gắn URL Worker vào `frontend/index.html` và đẩy lên GitHub Pages an toàn.
