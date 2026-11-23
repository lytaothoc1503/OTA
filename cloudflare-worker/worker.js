/**
 * BANLA // NOMAD — Cloudflare Worker Secure Telegram Proxy & Callback Handler
 * - Giấu kín hoàn toàn TG_BOT_TOKEN và TG_CHAT_ID trên Cloudflare Environment Secrets.
 * - Endpoint 1: POST /order  -> Nhận đơn từ GitHub Pages (index.html) & bắn về @CSN1503_ai_Bot kèm nút [✅ Duyệt cọc] / [❌ Báo hết phòng].
 * - Endpoint 2: POST /telegram-webhook -> Xử lý trực tiếp khi Admin bấm nút Duyệt/Hết phòng ngay trên điện thoại 24/7 (không cần bật máy tính).
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatVnd(amount) {
  return Math.round(Number(amount || 0)).toLocaleString('vi-VN') + '₫';
}

async function tgCall(token, method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    // Health check
    if (request.method === 'GET' && url.pathname === '/') {
      return new Response(
        JSON.stringify({ status: 'ok', service: 'BANLA // NOMAD Telegram Proxy' }),
        { headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' } }
      );
    }

    // Endpoint 2: Telegram Interactive Button Webhook (/telegram-webhook)
    if (request.method === 'POST' && url.pathname === '/telegram-webhook') {
      const upd = await request.json();
      if (upd.callback_query) {
        const cb = upd.callback_query;
        const parts = String(cb.data || '').split('|');
        const action = parts[0];
        const orderCode = parts[1] || 'N/A';
        const zaloPhone = parts[2] || '';
        const adminUser = cb.from?.username || cb.from?.first_name || 'Admin';
        const origText = cb.message?.text || '';

        const statusLine =
          action === 'approve'
            ? `✅ ĐÃ DUYỆT CỌC bởi @${adminUser}`
            : `❌ ĐÃ BÁO HẾT PHÒNG bởi @${adminUser}`;

        const cleanLines = origText.split('\n').filter((l) => !l.startsWith('⏳'));
        cleanLines.push(statusLine);

        await tgCall(env.TG_BOT_TOKEN, 'editMessageText', {
          chat_id: cb.message.chat.id,
          message_id: cb.message.message_id,
          text: cleanLines.join('\n'),
          reply_markup: zaloPhone
            ? { inline_keyboard: [[{ text: `💬 Mở Zalo khách (${zaloPhone})`, url: `https://zalo.me/${zaloPhone}` }]] }
            : { inline_keyboard: [] },
        });

        await tgCall(env.TG_BOT_TOKEN, 'answerCallbackQuery', {
          callback_query_id: cb.id,
          text: statusLine,
        });
      }
      return new Response('OK', { status: 200 });
    }

    // Endpoint 1: Receive Web Booking Order (POST / or POST /order)
    if (request.method === 'POST') {
      try {
        const body = await request.json();
        const order = body.order || body;
        const orderCode = order.orderCode || 'BNL-NEW';
        const cust = order.customer || {};
        const rawDigits = String(cust.phone || '').replace(/\D/g, '');
        const zaloPhone = rawDigits.startsWith('84') ? '0' + rawDigits.slice(2) : rawDigits;

        const textHtml =
          body.telegramHtml ||
          [
            `🔔 <b>ĐƠN ĐẶT CHỖ MỚI — ${escapeHtml(orderCode)}</b>`,
            `👤 <b>Khách:</b> ${escapeHtml(cust.name)} | 📞 <code>${escapeHtml(cust.phone)}</code>`,
            `📅 <b>Ngày đi:</b> ${escapeHtml(cust.date)} | 👥 ${escapeHtml(cust.guests)}`,
            `💰 <b>Tổng đơn:</b> <b>${formatVnd(order.totalVnd)}</b>`,
            `⏳ <b>Trạng thái:</b> <i>CHỜ ADMIN DUYỆT</i>`,
          ].join('\n');

        const finalHtml = textHtml.includes('⏳')
          ? textHtml
          : `${textHtml}\n⏳ <b>Trạng thái:</b> <i>CHỜ ADMIN DUYỆT (Human-in-the-loop)</i>`;

        const tgResult = await tgCall(env.TG_BOT_TOKEN, 'sendMessage', {
          chat_id: env.TG_CHAT_ID,
          parse_mode: 'HTML',
          disable_web_page_preview: true,
          text: finalHtml,
          reply_markup: {
            inline_keyboard: [
              [
                { text: '✅ Duyệt cọc', callback_data: `approve|${orderCode}|${zaloPhone}` },
                { text: '❌ Báo hết phòng', callback_data: `soldout|${orderCode}|${zaloPhone}` },
              ],
              [{ text: `💬 Mở Zalo khách (${zaloPhone})`, url: `https://zalo.me/${zaloPhone}` }],
            ],
          },
        });

        return new Response(JSON.stringify(tgResult), {
          status: tgResult.ok ? 200 : 502,
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: String(err) }), {
          status: 400,
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        });
      }
    }

    return new Response('Method Not Allowed', { status: 405, headers: CORS_HEADERS });
  },
};
