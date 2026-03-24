from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# 🔐 التوكنات
IG_TOKEN = os.getenv("IG_TOKEN")
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# 🔹 مسار رئيسي
@app.get("/")
def home():
    return {"message": "🔥 Advanced AI Bot is working"}

# 🔹 API لجلب بيانات الحساب الانستغرام
@app.get("/instagram")
def get_instagram():
    url = "https://graph.instagram.com/me"
    params = {"fields": "id,username,media_count", "access_token": IG_TOKEN}
    r = requests.get(url, params=params)
    return r.json()

# 🔹 API لجلب آخر 5 منشورات
@app.get("/instagram/latest")
def latest_instagram_posts():
    url = "https://graph.instagram.com/me/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp",
        "access_token": IG_TOKEN,
        "limit": 5
    }
    r = requests.get(url, params=params).json()
    return r

# 🔹 Webhook تيليجرام مع أوامر ذكية
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("📩 Incoming Telegram data:", data)

    try:
        if "message" not in data:
            return {"ok": True}

        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        if not text:
            return {"ok": True}

        reply = "استخدم /latest أو /ig"

        if text == "/start":
            reply = "🔥 البوت المتقدم يعمل بنجاح"

        elif text == "/ig":
            url = "https://graph.instagram.com/me"
            params = {"fields": "id,username,media_count", "access_token": IG_TOKEN}
            r = requests.get(url, params=params).json()
            if "username" in r:
                reply = f"👤 حسابك: {r['username']}\nعدد المنشورات: {r['media_count']}"
            else:
                reply = "❌ خطأ في التوكن أو الحساب"

        elif text == "/latest":
            url = "https://graph.instagram.com/me/media"
            params = {
                "fields": "id,caption,media_type,media_url,permalink,timestamp",
                "access_token": IG_TOKEN,
                "limit": 5
            }
            r = requests.get(url, params=params).json()
            posts = r.get("data", [])
            if not posts:
                reply = "لا توجد منشورات حالياً"
            else:
                reply = ""
                for p in posts:
                    media_type = p.get("media_type")
                    caption = p.get("caption", "بدون وصف")
                    permalink = p.get("permalink")
                    reply += f"📌 {caption}\n{permalink}\n\n"

        # إرسال الرد للبوت
        try:
            resp = requests.post(
                TELEGRAM_API,
                json={"chat_id": chat_id, "text": reply},
                timeout=5
            )
            print("📤 Telegram response:", resp.text)
        except Exception as e:
            print("❌ Telegram send error:", e)

    except Exception as e:
        print("❌ Webhook error:", e)

    return {"ok": True}
