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

      // 2. Xử lý tin nhắn chat từ người dùng -> Trợ lý AI Gemini Toàn Năng
      if (upd.message && upd.message.text) {
        const msg = upd.message;
        const chatId = msg.chat.id;
        const userText = msg.text.trim();
        const adminId = String(env.TG_CHAT_ID || '8369250562').trim();
        const isAdmin = String(chatId).trim() === adminId || String(chatId).trim() === '8369250562';

        if (userText.startsWith('/start')) {
          const welcomeText = isAdmin
            ? `👋 <b>Dạ em chào Sếp!</b>\n\nEm là <b>Trợ lý AI Toàn Năng (Co-pilot)</b> của Sếp. Em sẵn sàng nhận lệnh:\n• 💻 <b>Lập trình & Website:</b> Viết code (JS/Python/HTML/CSS), fix bug, tối ưu web, build dự án mới...\n• ⚙️ <b>Hạ tầng & Cloudflare:</b> Quản lý Worker, API, tự động hóa 24/7...\n• 🏨 <b>Hệ thống Banla OTA:</b> Đón đơn đặt phòng, quản lý duyệt cọc từ web...\n• 📊 <b>Công việc đa nhiệm:</b> Viết bài, lên kế hoạch kinh doanh, phân tích dữ liệu...\n\n<i>Sếp cần em làm gì hoặc code phần nào, cứ nhắn em ngay nhé! 🚀</i>`
            : `👋 <b>Xin chào ${escapeHtml(msg.from?.first_name || 'bạn')}!</b>\n\nTôi là Trợ lý AI của <b>BANLA // NOMAD OTA</b> (Google Gemini).\n\n✨ Bạn có thể hỏi tôi về:\n• Các tour & homestay (Tà Xùa săn mây, Mộc Châu, Hà Giang...)\n• Kinh nghiệm du lịch, thời tiết, lịch trình\n• Hướng dẫn đặt phòng và giữ chỗ trực tiếp!`;

          await tgCall(env.TG_BOT_TOKEN, 'sendMessage', {
            chat_id: chatId,
            parse_mode: 'HTML',
            text: welcomeText,
          });
          return new Response('OK', { status: 200 });
        }

        if (env.GEMINI_API_KEY) {
          try {
            const systemPrompt = `Bạn là Trợ lý AI Trí Tuệ Toàn Năng (AI Co-pilot & Senior Technical Advisor), trực tiếp đồng hành hỗ trợ Sếp (Admin ID: 8369250562, tên gọi Sếp / X Magic) và vận hành hệ thống OTA BANLA // NOMAD.

NGUYÊN TẮC XỬ LÝ THÔNG MINH (QUAN TRỌNG NHẤT):
1. Nhận diện Sếp (Admin):
   - Người chat hiện tại ${isAdmin ? 'CHÍNH LÀ SẾP (ADMIN / CHỦ DỰ ÁN)' : 'là khách hàng'}.
   - ${isAdmin ? 'Tuyệt đối KHÔNG BAO GIỜ coi Sếp là khách! Không chào mời Sếp mua tour hay giới thiệu tour nhảm nhí trừ khi Sếp hỏi! Luôn xưng hô chu đáo, thông minh: "Dạ sếp", "Em nghe sếp", "Em giải quyết ngay sếp nhé".' : 'Nếu là khách hàng, hãy tư vấn tour du lịch nhiệt tình, lịch sự, chu đáo.'}

2. Năng lực chuyên môn toàn diện:
   - Lập trình & Kỹ thuật: Viết code cực chuẩn (JavaScript, TypeScript, Python, HTML/CSS, React, Vue, Node.js, Cloudflare Workers, REST API, Git, SQL, Docker...). Fix bug chuẩn xác, giải thích dễ hiểu, cung cấp code hoàn chỉnh sẵn sàng copy-paste.
   - Phát triển Website: Hướng dẫn xây dựng tính năng, tối ưu SEO, tăng tốc độ tải trang, responsive mobile.
   - Vận hành Hệ thống: Nắm rõ hệ thống BANLA // NOMAD OTA hiện tại (Worker 24/7, Bot duyệt cọc, các gói tour: Tà Xùa 4.690.000₫, Mộc Châu 3.190.000₫, Hà Giang 6.090.000₫, VietQR MB Bank 0901650888).
   - Công việc đa nhiệm: Viết content truyền thông, soạn thảo email, xây dựng chiến lược kinh doanh, tóm tắt, dịch thuật chuyên sâu.

3. Phong cách phản hồi:
   - Thông minh, sắc sảo, tự nhiên như một kỹ sư phần mềm cao cấp và thư ký riêng đắc lực.
   - Trả lời thẳng vào trọng tâm, giải quyết vấn đề ngay, không dài dòng văn mẫu, định dạng markdown rõ ràng.`;

            const geminiRes = await fetch(
              `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key=${env.GEMINI_API_KEY}`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  system_instruction: {
                    parts: [{ text: systemPrompt }],
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
              'Dạ hiện tại em đang xử lý dữ liệu, sếp nhắn lại câu hỏi giúp em nhé!';

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
