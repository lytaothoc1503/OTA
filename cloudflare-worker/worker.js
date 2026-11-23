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

    // Endpoint 2: Telegram Interactive Button & Gemini AI Assistant Webhook (/telegram-webhook)
    if (request.method === 'POST' && url.pathname === '/telegram-webhook') {
      const upd = await request.json();

      // 1. Xử lý nút bấm Inline [✅ Duyệt cọc] / [❌ Báo hết phòng]
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
        return new Response('OK', { status: 200 });
      }

      // 2. Xử lý tin nhắn chat từ người dùng -> Trợ lý AI Gemini
      if (upd.message && upd.message.text) {
        const msg = upd.message;
        const chatId = msg.chat.id;
        const userText = msg.text.trim();

        if (userText.startsWith('/start')) {
          await tgCall(env.TG_BOT_TOKEN, 'sendMessage', {
            chat_id: chatId,
            parse_mode: 'HTML',
            text: `👋 <b>Xin chào ${escapeHtml(msg.from?.first_name || 'bạn')}!</b>\n\nTôi là Trợ lý AI của <b>BANLA // NOMAD OTA</b> (Powered by Google Gemini).\n\n✨ Bạn có thể nhắn tin hỏi tôi bất kỳ thông tin nào về:\n• Các tour du lịch & homestay (Tà Xùa, Mộc Châu, Hà Giang...)\n• Kinh nghiệm săn mây, lịch trình gợi ý\n• Hoặc bất kỳ thắc mắc nào khác!\n\n<i>Cứ gửi câu hỏi, tôi sẽ giải đáp ngay nhé!</i>`,
          });
          return new Response('OK', { status: 200 });
        }

        if (env.GEMINI_API_KEY) {
          try {
            const geminiRes = await fetch(
              `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key=${env.GEMINI_API_KEY}`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  system_instruction: {
                    parts: [
                      {
                        text: 'Bạn là Trợ lý AI thông minh, nhiệt tình của BANLA // NOMAD OTA - nền tảng du lịch khám phá và homestay tại Việt Nam (Tà Xùa 3N2Đ: 4.690.000₫, Mộc Châu Retreat 2N1Đ: 3.190.000₫, Hà Giang Loop 4N3Đ: 6.090.000₫). Trả lời súc tích, lịch sự, thân thiện, dùng emoji phù hợp và tư vấn chu đáo bằng tiếng Việt.',
                      },
                    ],
                  },
                  contents: [
                    {
                      role: 'user',
                      parts: [{ text: userText }],
                    },
                  ],
                }),
              }
            );

            const geminiData = await geminiRes.json();
            const aiReply =
              geminiData.candidates?.[0]?.content?.parts?.[0]?.text ||
              'Xin lỗi, hiện tại tôi chưa thể phản hồi câu hỏi này. Bạn vui lòng thử lại nhé!';

            await tgCall(env.TG_BOT_TOKEN, 'sendMessage', {
              chat_id: chatId,
              text: aiReply,
            });
          } catch (err) {
            await tgCall(env.TG_BOT_TOKEN, 'sendMessage', {
              chat_id: chatId,
              text: `⚠️ Lỗi xử lý AI: ${err.message}`,
            });
          }
        }
        return new Response('OK', { status: 200 });
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
