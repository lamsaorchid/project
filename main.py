from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# 🔐 التوكنات من البيئة (Render Environment)
IG_TOKEN = os.getenv("IG_TOKEN")
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")

# رابط تيليجرام
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# API بسيط لاختبار الانستغرام
@app.get("/instagram")
def get_instagram():
    url = "https://graph.instagram.com/me"
    params = {
        "fields": "id,username",
        "access_token": IG_TOKEN
    }
    r = requests.get(url, params=params)
    return r.json()


# Webhook من تيليجرام
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()

    try:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            reply = "🔥 البوت يعمل بنجاح"

        elif text == "/ig":
            # جلب بيانات انستغرام
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
        })

    except Exception as e:
        print(e)

    return {"ok": True}