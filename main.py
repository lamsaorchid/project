from fastapi import FastAPI, Request
import requests
import os
import openai  # إذا أردت دعم AI

app = FastAPI()

# 🔐 التوكنات من Environment
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")  # رقم الحساب البيزنس على إنستغرام
IG_TOKEN = os.getenv("IG_TOKEN")  # توكن Facebook Graph API v25.0
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # اختياري للردود AI
openai.api_key = OPENAI_API_KEY

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

@app.get("/")
def home():
    return {"message": "🔥 AI Bot with Facebook Graph API is online"}

# 🔹 جلب بيانات الحساب
@app.get("/instagram")
def get_instagram():
    url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}"
    params = {"fields": "username,media_count", "access_token": IG_TOKEN}
    r = requests.get(url, params=params)
    return r.json()

# 🔹 جلب آخر 5 منشورات
@app.get("/instagram/latest")
def latest_instagram_posts():
    url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp",
        "access_token": IG_TOKEN,
        "limit": 5
    }
    r = requests.get(url, params=params).json()
    return r

# 🔹 Webhook تيليجرام
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

        reply = "استخدم /ig أو /latest أو ارسل أي سؤال للبوت AI"

        if text == "/start":
            reply = "🔥 البوت يعمل بنجاح! يمكنك الآن إدارة صفحتك عبر تيليجرام."

        elif text == "/ig":
            url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}"
            params = {"fields": "username,media_count", "access_token": IG_TOKEN}
            r = requests.get(url, params=params).json()
            if "username" in r:
                reply = f"👤 حسابك: {r['username']}\nعدد المنشورات: {r['media_count']}"
            else:
                reply = "❌ خطأ في التوكن أو الحساب"

        elif text == "/latest":
            url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
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
                    caption = p.get("caption", "بدون وصف")
                    permalink = p.get("permalink")
                    reply += f"📌 {caption}\n{permalink}\n\n"
        else:
            # أي رسالة أخرى → رد AI
            try:
                ai_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "أنت مساعد ذكي باللغة العربية"},
                        {"role": "user", "content": text}
                    ],
                    max_tokens=300
                )
                reply = ai_response['choices'][0]['message']['content']
            except Exception as e:
                print("❌ AI error:", e)
                reply = "حدث خطأ أثناء معالجة طلبك."

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
