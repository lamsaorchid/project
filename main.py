from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

IG_TOKEN = os.getenv("IG_TOKEN")
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

@app.get("/")
def home():
    return {"message": "🔥 API is working"}

@app.get("/instagram")
def get_instagram():
    url = "https://graph.instagram.com/me"
    params = {
        "fields": "id,username",
        "access_token": IG_TOKEN
    }
    r = requests.get(url, params=params)
    return r.json()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("📩 Incoming Telegram data:", data)  # 🔹 لعرض الرسائل في logs

    try:
        if "message" not in data:
            return {"ok": True}  # تجاهل الرسائل غير النصية

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if not text:
            return {"ok": True}

        if text == "/start":
            reply = "🔥 البوت يعمل بنجاح"

        elif text == "/ig":
            url = "https://graph.instagram.com/me"
            params = {
                "fields": "id,username",
                "access_token": IG_TOKEN
            }
            r = requests.get(url, params=params).json()
            if "username" in r:
                reply = f"👤 حسابك: {r['username']}"
            else:
                reply = "❌ خطأ في التوكن"

        else:
            reply = "استخدم /ig"

        requests.post(TELEGRAM_API, json={
            "chat_id": chat_id,
            "text": reply
        }, timeout=5)

    except Exception as e:
        print("❌ Error:", e)

    return {"ok": True}
