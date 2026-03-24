from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# 🔐 التوكنات من البيئة (Render Environment)
IG_TOKEN = os.getenv("IG_TOKEN")
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# 🔹 مسار رئيسي للاختبار
@app.get("/")
def home():
    return {"message": "🔥 API is working"}

# 🔹 API لاختبار الانستغرام
@app.get("/instagram")
def get_instagram():
    url = "https://graph.instagram.com/me"
    params = {
        "fields": "id,username",
        "access_token": IG_TOKEN
    }
    r = requests.get(url, params=params)
    return r.json()

# 🔹 Webhook من تيليجرام
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("📩 Incoming Telegram data:", data)  # لعرض كل الرسائل في logs

    try:
        # تجاهل الرسائل الغير نصية أو غير موجودة
        if "message" not in data:
            return {"ok": True}
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        if not text:
            return {"ok": True}

        # التعامل مع الأوامر
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
                reply = "❌ خطأ في التوكن أو الحساب"

        else:
            reply = "استخدم /ig"

        # إرسال الرد مع طباعة النتيجة لمراقبة الأخطاء
        try:
            resp = requests.post(TELEGRAM_API, json={
                "chat_id": chat_id,
                "text": reply
            }, timeout=5)
            print("📤 Telegram response:", resp.text)
        except Exception as e:
            print("❌ Telegram send error:", e)

    except Exception as e:
        print("❌ Webhook error:", e)

    return {"ok": True}
