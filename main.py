from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests, os, json
from datetime import datetime

app = FastAPI()

# 🔐 Environment Variables
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
IG_TOKEN = os.getenv("IG_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

MESSAGES_FILE = "messages.json"
RESPONSES_FILE = "responses.json"

# 🔹 تسجيل الرسائل والردود
def log_message(user, text):
    data = {"time": str(datetime.now()), "user": user, "text": text}
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(data)
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def log_response(chat_id, text):
    data = {"time": str(datetime.now()), "chat_id": chat_id, "text": text}
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(data)
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# 🔹 Webhook تيليجرام
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    user = message["from"]["username"]
    text = message.get("text", "")
    log_message(user, text)

    reply = f"تم استلام رسالتك: {text}"  # يمكن لاحقًا AI

    # إرسال الرد
    resp = requests.post(TELEGRAM_API, json={"chat_id": chat_id, "text": reply})
    log_response(chat_id, reply)

    return {"ok": True}

# 🔹 API endpoints للوحة التحكم
@app.get("/api/messages")
def get_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/api/responses")
def get_responses():
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/api/instagram/latest")
def latest_instagram_posts():
    url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,media_url,permalink,timestamp",
        "access_token": IG_TOKEN,
        "limit": 5
    }
    r = requests.get(url, params=params).json()
    return r.get("data", [])

# 🔹 صفحة لوحة التحكم
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <head>
        <title>لوحة تحكم البوت</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            h2 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2>📩 آخر الرسائل</h2>
        <div id="messages"></div>
        <h2>💬 آخر الردود</h2>
        <div id="responses"></div>
        <h2>📸 آخر منشورات Instagram</h2>
        <div id="instagram"></div>
        <script>
        async function loadData() {
            let msgs = await fetch('/api/messages').then(r => r.json());
            let resp = await fetch('/api/responses').then(r => r.json());
            let insta = await fetch('/api/instagram/latest').then(r => r.json());

            document.getElementById('messages').innerHTML = `<table>
                <tr><th>الوقت</th><th>المستخدم</th><th>النص</th></tr>` + msgs.map(m => `<tr><td>${m.time}</td><td>${m.user}</td><td>${m.text}</td></tr>`).join('') + `</table>`;

            document.getElementById('responses').innerHTML = `<table>
                <tr><th>الوقت</th><th>Chat ID</th><th>النص</th></tr>` + resp.map(r => `<tr><td>${r.time}</td><td>${r.chat_id}</td><td>${r.text}</td></tr>`).join('') + `</table>`;

            document.getElementById('instagram').innerHTML = `<ul>` + insta.map(p => `<li><a href="${p.permalink}" target="_blank">${p.caption || "بدون وصف"}</a></li>`).join('') + `</ul>`;
        }
        loadData();
        </script>
    </body>
    </html>
    """
