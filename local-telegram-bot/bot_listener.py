#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BANLA // NOMAD — Local Telegram Bot Listener & Order Bridge (@CSN1503_ai_Bot)
- Không phụ thuộc thư viện ngoài (chạy ngay bằng Python 3 trên Windows 11).
- Chức năng 1: Mở cổng HTTP nội bộ (mặc định http://127.0.0.1:8787/order) nhận đơn từ frontend/index.html.
- Chức năng 2: Đẩy tin nhắn đơn hàng kèm nút bấm Inline [✅ Duyệt cọc] / [❌ Báo hết phòng] / [💬 Mở Zalo].
- Chức năng 3: Human-in-the-loop — Lắng nghe thao tác bấm nút của Admin trên Telegram, chống bấm trùng (deduplication) và ghi log ra orders_audit.jsonl.
"""

import json
import os
import sys
import time
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

ICT = timezone(timedelta(hours=7))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
AUDIT_LOG_PATH = os.path.join(BASE_DIR, "orders_audit.jsonl")


def load_dotenv_simple(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv_simple(ENV_PATH)

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.environ.get("TG_ADMIN_CHAT_ID", "").strip()
LOCAL_PORT = int(os.environ.get("PORT_LOCAL_BRIDGE", "8787"))

PROCESSED_CALLBACKS = set()
PROCESSED_ORDERS = set()


def now_ict_str():
    return datetime.now(ICT).strftime("%Y-%m-%d %H:%M:%S ICT")


def append_audit_log(event_type, payload):
    record = {
        "timestamp": now_ict_str(),
        "event": event_type,
        "data": payload,
    }
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[WARN] Không ghi được file log: {exc}")


def tg_api_call(method, payload=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"[TG HTTP ERROR] {method}: {e.code} - {err_body}")
        return {"ok": False, "description": err_body}
    except Exception as exc:
        print(f"[TG NET ERROR] {method}: {exc}")
        return {"ok": False, "description": str(exc)}


def escape_html(val):
    return (
        str(val or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_vnd(amount):
    try:
        return f"{int(round(float(amount))):,}".replace(",", ".") + "₫"
    except Exception:
        return "0₫"


def build_order_card_and_buttons(order):
    order_code = order.get("orderCode", "BNL-UNKNOWN")
    cust = order.get("customer", {})
    name = cust.get("name", "Khách")
    phone = cust.get("phone", "")
    dep_date = cust.get("date", "")
    guests = cust.get("guests", "")
    note = cust.get("note", "")

    items = order.get("items", [])
    item_lines = []
    for idx, item in enumerate(items, 1):
        iname = escape_html(item.get("name", "Gói dịch vụ"))
        iqty = int(item.get("qty", 1))
        ivnd = float(item.get("priceVnd", 0)) * iqty
        item_lines.append(f"{idx}. <b>{iname}</b> × {iqty} — <code>{format_vnd(ivnd)}</code>")

    total_vnd = format_vnd(order.get("totalVnd", 0))
    pay_now_vnd = format_vnd(order.get("payNowVnd", 0))
    pay_method = order.get("paymentMethod", "vietqr")
    dep_ratio = order.get("depositRatio", 0.3)

    if pay_method == "vietqr":
        pay_str = f"VietQR MB Bank ({'Cọc 30%' if dep_ratio == 0.3 else '100%'}: <b>{pay_now_vnd}</b>)"
    elif pay_method == "vnpay":
        pay_str = f"Cổng VNPay / Thẻ (<b>{total_vnd}</b>)"
    else:
        pay_str = "Giữ chỗ 0₫ — Chờ tư vấn"

    raw_digits = "".join(ch for ch in phone if ch.isdigit())
    zalo_phone = ("0" + raw_digits[2:]) if raw_digits.startswith("84") else raw_digits

    text_lines = [
        f"🔔 <b>ĐƠN ĐẶT CHỖ MỚI — {escape_html(order_code)}</b>",
        "━━━━━━━━━━━━━━━━━━",
        f"👤 <b>Khách hàng:</b> {escape_html(name)}",
        f"📞 <b>SĐT / Zalo:</b> <code>{escape_html(phone)}</code>",
        f"📅 <b>Ngày khởi hành:</b> <b>{escape_html(dep_date)}</b>",
        f"👥 <b>Số khách:</b> {escape_html(guests)}",
        "━━━━━━━━━━━━━━━━━━",
        "📦 <b>CHI TIẾT HÀNH TRÌNH:</b>",
        "\n".join(item_lines) if item_lines else "• Chưa rõ gói",
        f"💰 <b>TỔNG ĐƠN:</b> <b>{total_vnd}</b>",
        f"💳 <b>Thanh toán:</b> {pay_str}",
        f"🏦 <b>Nội dung CK:</b> <code>{escape_html(order_code.replace('-', ' '))}</code>",
    ]
    if note:
        text_lines.append(f"📝 <b>Ghi chú:</b> <i>{escape_html(note)}</i>")

    text_lines.append("━━━━━━━━━━━━━━━━━━")
    text_lines.append("⏳ <b>Trạng thái:</b> <i>CHỜ ADMIN DUYỆT (Human-in-the-loop)</i>")

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Duyệt cọc", "callback_data": f"approve|{order_code}|{zalo_phone}"},
                {"text": "❌ Báo hết phòng", "callback_data": f"soldout|{order_code}|{zalo_phone}"},
            ],
            [
                {"text": f"💬 Mở Zalo khách ({zalo_phone})", "url": f"https://zalo.me/{zalo_phone}"}
            ],
        ]
    }
    return "\n".join(text_lines), reply_markup


class OrderBridgeHandler(BaseHTTPRequestHandler):
    def _send_cors(self, status=200):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        self._send_cors(200)

    def do_POST(self):
        global ADMIN_CHAT_ID
        if self.path not in ("/", "/order", "/webhook"):
            self._send_cors(404)
            self.wfile.write(json.dumps({"ok": False, "error": "Not Found"}).encode("utf-8"))
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            body = json.loads(raw_body)
        except Exception:
            self._send_cors(400)
            self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON"}).encode("utf-8"))
            return

        order = body.get("order") or body
        order_code = order.get("orderCode", "")

        # Deduplication filter
        if order_code and order_code in PROCESSED_ORDERS:
            self._send_cors(200)
            self.wfile.write(json.dumps({"ok": True, "deduplicated": True}).encode("utf-8"))
            return

        if order_code:
            PROCESSED_ORDERS.add(order_code)

        append_audit_log("NEW_ORDER_WEB", order)

        if not ADMIN_CHAT_ID:
            self._send_cors(503)
            self.wfile.write(
                json.dumps({"ok": False, "error": "Chưa có TG_ADMIN_CHAT_ID. Hãy gõ /start vào bot trước."}).encode("utf-8")
            )
            return

        html_text, markup = build_order_card_and_buttons(order)
        res = tg_api_call(
            "sendMessage",
            {
                "chat_id": ADMIN_CHAT_ID,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "text": html_text,
                "reply_markup": markup,
            },
        )
        self._send_cors(200 if res.get("ok") else 502)
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def log_message(self, fmt, *args):
        # Silent concise logging
        pass


def handle_callback_query(cb):
    cb_id = cb.get("id")
    data = cb.get("data", "")
    user = cb.get("from", {})
    admin_name = user.get("username") or user.get("first_name") or "Admin"
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    orig_text = msg.get("text", "")

    dedup_key = f"{chat_id}:{message_id}:{data}"
    if dedup_key in PROCESSED_CALLBACKS:
        tg_api_call("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Đơn này đã xử lý rồi!"})
        return
    PROCESSED_CALLBACKS.add(dedup_key)

    parts = data.split("|")
    action = parts[0] if parts else ""
    order_code = parts[1] if len(parts) > 1 else "N/A"
    zalo_phone = parts[2] if len(parts) > 2 else ""

    if action == "approve":
        status_badge = f"✅ ĐÃ DUYỆT CỌC bởi @{admin_name} ({now_ict_str()})"
        toast_text = f"Đã duyệt cọc đơn {order_code}"
    elif action == "soldout":
        status_badge = f"❌ ĐÃ BÁO HẾT PHÒNG bởi @{admin_name} ({now_ict_str()})"
        toast_text = f"Đã đánh dấu hết phòng đơn {order_code}"
    else:
        tg_api_call("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Thao tác không xác định"})
        return

    append_audit_log("ADMIN_DECISION", {"orderCode": order_code, "action": action, "by": admin_name})

    # Replace last status line cleanly
    lines = orig_text.split("\n")
    updated_lines = [ln for ln in lines if not ln.startswith("⏳")]
    updated_lines.append(status_badge)

    keep_zalo_kb = {
        "inline_keyboard": [
            [{"text": f"💬 Mở Zalo khách ({zalo_phone})", "url": f"https://zalo.me/{zalo_phone}"}]
        ]
    } if zalo_phone else {"inline_keyboard": []}

    tg_api_call(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": "\n".join(updated_lines),
            "reply_markup": keep_zalo_kb,
        },
    )
    tg_api_call("answerCallbackQuery", {"callback_query_id": cb_id, "text": toast_text})
    print(f"[ACTION] {status_badge}")


def poll_telegram_updates():
    global ADMIN_CHAT_ID
    # Ensure webhook is cleared when running in Local Long-Polling mode
    tg_api_call("deleteWebhook", {"drop_pending_updates": False})
    print(f"[BOT] Đang lắng nghe @CSN1503_ai_Bot (Long-Polling)... Thời gian: {now_ict_str()}")
    offset = 0

    while True:
        res = tg_api_call("getUpdates", {"offset": offset, "timeout": 25, "allowed_updates": ["message", "callback_query"]})
        if not res.get("ok"):
            time.sleep(3)
            continue

        for upd in res.get("result", []):
            offset = upd["update_id"] + 1

            if "callback_query" in upd:
                handle_callback_query(upd["callback_query"])
                continue

            msg = upd.get("message")
            if not msg:
                continue

            chat = msg.get("chat", {})
            cid = str(chat.get("id", ""))
            text = (msg.get("text") or "").strip()

            if text.startswith("/start") or text.startswith("/id"):
                if not ADMIN_CHAT_ID:
                    ADMIN_CHAT_ID = cid
                    print(f"[AUTO-BIND] Đã gán TG_ADMIN_CHAT_ID = {ADMIN_CHAT_ID}")
                tg_api_call(
                    "sendMessage",
                    {
                        "chat_id": cid,
                        "parse_mode": "HTML",
                        "text": (
                            f"✅ <b>BANLA // NOMAD BOT ONLINE</b>\n"
                            f"• Chat ID của bạn: <code>{cid}</code>\n"
                            f"• Local HTTP Bridge: <code>http://127.0.0.1:{LOCAL_PORT}/order</code>\n"
                            f"• Chế độ: Human-in-the-loop ([✅ Duyệt cọc] / [❌ Báo hết phòng])"
                        ),
                    },
                )


def main():
    if not BOT_TOKEN or "PASTE_YOUR" in BOT_TOKEN:
        print("[ERROR] Chưa cấu hình TG_BOT_TOKEN trong file local-telegram-bot/.env!")
        print("Hãy copy .env.example thành .env và điền mã Token từ @BotFather.")
        sys.exit(1)

    server = HTTPServer(("127.0.0.1", LOCAL_PORT), OrderBridgeHandler)
    http_thread = threading.Thread(target=server.serve_forever, daemon=True)
    http_thread.start()
    print(f"[HTTP] Local Order Webhook đang mở tại: http://127.0.0.1:{LOCAL_PORT}/order")

    try:
        poll_telegram_updates()
    except KeyboardInterrupt:
        print("\n[STOP] Đã dừng Bot an toàn.")


if __name__ == "__main__":
    main()
