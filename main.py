import os
import requests
import openai
from flask import Flask, jsonify, request, make_response
import threading
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
PAGE_ID = str(os.environ.get('PAGE_ID', '')).strip()
OPENAI_KEY = os.environ.get('OPENAI_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'orchid_bot_verify_123').strip()

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

stats = {
    'total_replies': 0,
    'total_messages': 0,
    'total_comments': 0,
    'last_activity': 'لا يوجد نشاط بعد',
    'recent_activities': [],
    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'bot_running': True
}

replied_ids = set()

BUSINESS_CONTEXT = """
أنت مساعد ذكي لمتجر "لمسة أوركيد" (Lamt Orchid) في عدن، اليمن.
🌸 المنتجات: باقات ورد طبيعي وصناعي، تغليف هدايا، توزيعات مناسبات.
📍 الموقع: عدن مول - الدور الأول.
📞 واتساب: 783200063.
✨ أسلوب الرد: ودود، مهني، استخدم إيموجي، اذكر الواتساب (783200063) للطلب.
"""

def get_smart_reply(message_text):
    try:
        if not OPENAI_KEY: return "أهلاً بك في لمسة أوركيد 🌸 واتساب: 783200063"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": BUSINESS_CONTEXT}, {"role": "user", "content": message_text}],
            max_tokens=150, temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"ChatGPT Error: {e}")
        return "شكراً لتواصلك مع لمسة أوركيد ❤️ واتساب للطلب: 783200063"

# ═══════════════════════════════════════════════════════════
# Webhook Handling
# ═══════════════════════════════════════════════════════════

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return make_response(str(challenge), 200)
        return "Forbidden", 403

    if request.method == 'POST':
        data = request.json
        if stats['bot_running']:
            threading.Thread(target=process_payload, args=(data,)).start()
        return "EVENT_RECEIVED", 200

def process_payload(data):
    global stats
    try:
        if 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for event in entry['messaging']:
                        if 'sender' in event and 'message' in event:
                            sender_id = str(event['sender']['id'])
                            if sender_id == PAGE_ID: continue
                            if 'text' in event['message']:
                                mid = event['message']['id']
                                if mid not in replied_ids:
                                    msg_text = event['message']['text']
                                    reply = get_smart_reply(msg_text)
                                    send_reply(sender_id, reply)
                                    replied_ids.add(mid)
                                    stats['total_replies'] += 1
                                    stats['total_messages'] += 1
                                    update_history('رسالة', sender_id, msg_text, reply)

                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') in ['comments', 'comment']:
                            val = change.get('value', {})
                            cid = val.get('id')
                            if cid and cid not in replied_ids:
                                text = val.get('text', '')
                                reply = get_smart_reply(text)
                                send_comment_reply(cid, reply)
                                replied_ids.add(cid)
                                stats['total_replies'] += 1
                                stats['total_comments'] += 1
                                update_history('تعليق', val.get('from', {}).get('username', 'متابع'), text, reply)
    except Exception as e:
        logger.error(f"Error in process_payload: {e}")

def send_reply(recipient_id, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json={"recipient": {"id": recipient_id}, "message": {"text": text}})

def send_comment_reply(comment_id, text):
    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, data={"message": text})

def update_history(type, user, msg, reply):
    global stats
    stats['last_activity'] = datetime.now().strftime('%H:%M:%S')
    stats['recent_activities'].insert(0, {
        'type': type, 'user': user, 'msg': msg, 'reply': reply, 'time': stats['last_activity']
    })
    stats['recent_activities'] = stats['recent_activities'][:20]

# ═══════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    activities_html = "".join([f"""
        <div class="activity-card">
            <div class="activity-header">
                <div class="user-info">
                    <div class="user-avatar">{a['user'][0].upper()}</div>
                    <div>
                        <div class="username">{a['user']}</div>
                        <div class="time">{a['time']}</div>
                    </div>
                </div>
                <div class="badge">{a['type']}</div>
            </div>
            <div class="activity-body">
                <div class="msg-box"><b>التعليق:</b><br>{a['msg']}</div>
                <div class="reply-box"><b>🤖 رد البوت:</b><br>{a['reply']}</div>
            </div>
        </div>
    """ for a in stats['recent_activities']])

    return f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لمسة أوركيد | لوحة التحكم</title>
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #9b59b6;
                --primary-light: #f3e5f5;
                --secondary: #e91e63;
                --bg: #f8f9fe;
                --text: #2d3436;
            }}
            body {{
                font-family: 'Tajawal', sans-serif;
                background-color: var(--bg);
                margin: 0;
                color: var(--text);
                background-image: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
            }}
            .navbar {{
                background: white;
                padding: 15px 50px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            .logo-section {{ display: flex; align-items: center; gap: 10px; }}
            .logo-icon {{
                background: linear-gradient(45deg, var(--primary), var(--secondary));
                color: white; width: 40px; height: 40px; border-radius: 10px;
                display: flex; align-items: center; justify-content: center; font-size: 24px;
            }}
            .logo-text {{ font-weight: bold; font-size: 22px; color: var(--primary); }}

            .main-container {{
                display: grid;
                grid-template-columns: 1fr 350px;
                gap: 25px;
                padding: 30px 50px;
            }}

            .stats-row {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 25px;
            }}
            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 20px;
                display: flex;
                align-items: center;
                gap: 20px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.03);
                border-bottom: 4px solid var(--primary);
            }}
            .stat-icon {{
                width: 60px; height: 60px; border-radius: 15px;
                display: flex; align-items: center; justify-content: center;
                font-size: 25px;
            }}
            .icon-msg {{ background: #fff0f6; color: #d63384; }}
            .icon-comment {{ background: #f3f0ff; color: #6f42c1; }}
            .stat-info .value {{ font-size: 28px; font-weight: bold; }}
            .stat-info .label {{ color: #7f8c8d; font-size: 14px; }}

            .activities-section {{
                background: white;
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.03);
            }}
            .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 20px; display: flex; gap: 10px; align-items: center; }}

            .activity-card {{
                border: 1px solid #f1f1f1;
                border-radius: 15px;
                padding: 15px;
                margin-bottom: 15px;
                transition: 0.3s;
            }}
            .activity-card:hover {{ border-color: var(--primary); background: #fafafa; }}
            .activity-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
            .user-info {{ display: flex; gap: 12px; align-items: center; }}
            .user-avatar {{ width: 40px; height: 40px; background: #eee; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }}
            .username {{ font-weight: bold; font-size: 14px; }}
            .time {{ font-size: 12px; color: #999; }}
            .badge {{ background: var(--primary-light); color: var(--primary); padding: 4px 12px; border-radius: 20px; font-size: 12px; }}

            .msg-box {{ background: #f9f9f9; padding: 10px; border-radius: 10px; font-size: 14px; margin-bottom: 10px; }}
            .reply-box {{ background: #fdf2f8; border: 1px dashed var(--secondary); padding: 10px; border-radius: 10px; font-size: 14px; color: #d63384; }}

            .sidebar-card {{
                background: white;
                padding: 25px;
                border-radius: 20px;
                margin-bottom: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.03);
                text-align: center;
            }}
            .bot-status-ui {{
                margin: 20px 0;
            }}
            .status-circle {{
                width: 80px; height: 80px; border: 4px solid #eee; border-radius: 50%;
                display: flex; align-items: center; justify-content: center; margin: 0 auto 15px;
                font-size: 30px;
            }}
            .status-on {{ border-color: #2ecc71; color: #2ecc71; }}
            .btn-toggle {{
                background: linear-gradient(to right, var(--primary), var(--secondary));
                color: white; border: none; padding: 12px 30px; border-radius: 30px;
                font-family: 'Tajawal'; font-weight: bold; cursor: pointer; width: 100%;
            }}

            .info-item {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f9f9f9; font-size: 14px; }}
            .info-label {{ color: #95a5a6; }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="logo-section">
                <div class="logo-icon">✨</div>
                <div class="logo-text">لمسة أوركيد</div>
                <div style="font-size: 12px; color: #999; margin-top: 5px;">لوحة تحكم بوت الانستغرام الذكي</div>
            </div>
            <div style="background: #f8f9fe; padding: 8px 15px; border-radius: 10px; font-size: 14px;">
                🟢 البوت يعمل
            </div>
        </nav>

        <div class="main-container">
            <div class="content-area">
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-icon icon-msg">📧</div>
                        <div class="stat-info">
                            <div class="label">ردود الرسائل</div>
                            <div class="value">{stats['total_messages']}</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon icon-comment">💬</div>
                        <div class="stat-info">
                            <div class="label">ردود التعليقات</div>
                            <div class="value">{stats['total_comments']}</div>
                        </div>
                    </div>
                </div>

                <div class="activities-section">
                    <div class="section-title">📊 آخر النشاطات</div>
                    {activities_html if stats['recent_activities'] else "<div style='text-align:center; padding:40px; color:#ccc;'>في انتظار أول تفاعل...</div>"}
                </div>
            </div>

            <div class="sidebar">
                <div class="sidebar-card">
                    <h3>🤖 التحكم بالبوت</h3>
                    <div class="bot-status-ui">
                        <div class="status-circle status-on">✔️</div>
                        <h4>يعمل</h4>
                        <p style="font-size: 12px; color: #999;">البوت يقوم بالرد آلياً حالياً</p>
                    </div>
                    <button class="btn-toggle">تشغيل البوت</button>
                </div>

                <div class="sidebar-card" style="text-align: right;">
                    <h3>📸 معلومات الحساب</h3>
                    <div class="info-item">
                        <span class="info-label">معرف الحساب</span>
                        <span>{PAGE_ID[:10]}...</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">آخر تحقق</span>
                        <span>{stats['last_activity'] if stats['last_activity'] != 'لا يوجد نشاط بعد' else 'لم يتم بعد'}</span>
                    </div>
                    <div style="margin-top: 20px; text-align: center;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" width="20" style="vertical-align: middle;">
                        <span style="font-size: 12px; color: var(--primary);">متصل بـ Instagram</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // تحديث تلقائي كل 30 ثانية
            setTimeout(() => {{ location.reload(); }}, 30000);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
