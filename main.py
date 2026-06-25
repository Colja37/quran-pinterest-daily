import os
import requests
import random
from PIL import Image, ImageDraw, ImageFont
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
PINTEREST_TOKEN = os.environ["PINTEREST_ACCESS_TOKEN"]
PINTEREST_BOARD_ID = os.environ["PINTEREST_BOARD_ID"]

def fetch_random_ayah():
    surah = random.randint(1, 114)
    response = requests.get(f"https://api.alquran.cloud/v1/surah/{surah}")
    data = response.json()
    total_ayahs = data["data"]["numberOfAyahs"]
    ayah_num = random.randint(1, total_ayahs)
    
    r = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah_num}/ar.alafasy")
    arabic_text = r.json()["data"]["text"]
    surah_name = r.json()["data"]["surah"]["name"]
    
    return {
        "text": arabic_text,
        "surah": surah_name,
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} — آية {ayah_num}"
    }

def generate_image(ayah_data):
    width, height = 1000, 1500
    img = Image.new("RGB", (width, height), color="#1a1a2e")
    draw = ImageDraw.Draw(img)
    
    # إطار زخرفي
    draw.rectangle([40, 40, width-40, height-40], outline="#c9a84c", width=3)
    draw.rectangle([55, 55, width-55, height-55], outline="#c9a84c", width=1)
    
    # خط عربي
    try:
        font_big = ImageFont.truetype("fonts/Amiri-Regular.ttf", 72)
        font_small = ImageFont.truetype("fonts/Amiri-Regular.ttf", 42)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big
        font_ref = font_big

    # كتابة بسم الله
    draw.text((width//2, 150), "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
              font=font_small, fill="#c9a84c", anchor="mm")

    # فاصل
    draw.line([(150, 220), (850, 220)], fill="#c9a84c", width=1)

    # الآية — تقسيم النص لسطور
    text = ayah_data["text"]
    words = text.split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        test_line = " ".join(current)
        bbox = draw.textbbox((0, 0), test_line, font=font_big)
        if bbox[2] - bbox[0] > width - 200:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    total_text_height = len(lines) * 100
    y_start = (height - total_text_height) // 2 - 50

    for line in lines:
        draw.text((width//2, y_start), line,
                  font=font_big, fill="#ffffff", anchor="mm")
        y_start += 100

    # فاصل
    draw.line([(150, height-280), (850, height-280)], fill="#c9a84c", width=1)

    # المرجع
    draw.text((width//2, height-200), ayah_data["ref"],
              font=font_ref, fill="#c9a84c", anchor="mm")

    # شعار القناة (اختياري)
    draw.text((width//2, height-120), "✦ آية اليوم ✦",
              font=font_ref, fill="#c9a84c", anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.save(img_path)
    return img_path

def post_to_pinterest(img_path, ayah_data):
    # رفع الصورة أولاً
    with open(img_path, "rb") as f:
        upload_resp = requests.post(
            "https://api.pinterest.com/v5/media",
            headers={"Authorization": f"Bearer {PINTEREST_TOKEN}"},
            files={"file": f},
            data={"media_type": "image"}
        )
    
    media_id = upload_resp.json().get("media_id")
    
    # إنشاء البين
    pin_data = {
        "board_id": PINTEREST_BOARD_ID,
        "title": f"{ayah_data['ref']} | آية قرآنية",
        "description": f"{ayah_data['text']}\n\n{ayah_data['ref']}\n\n#قرآن #آية_اليوم #إسلام #ذكر #قرآن_كريم",
        "media_source": {
            "source_type": "media_id",
            "media_id": media_id
        }
    }
    
    resp = requests.post(
        "https://api.pinterest.com/v5/pins",
        headers={
            "Authorization": f"Bearer {PINTEREST_TOKEN}",
            "Content-Type": "application/json"
        },
        json=pin_data
    )
    
    pin = resp.json()
    return f"https://pinterest.com/pin/{pin.get('id')}"

async def send_for_review(ayah_data, img_path):
    bot = Bot(token=TELEGRAM_TOKEN)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ نشر الآن", callback_data="approve"),
            InlineKeyboardButton("❌ آية ثانية", callback_data="reject")
        ]
    ])
    
    caption = f"*{ayah_data['ref']}*\n\n{ayah_data['text']}"
    
    with open(img_path, "rb") as photo:
        msg = await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    return msg.message_id

async def wait_for_decision(ayah_data, img_path):
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    result = {"decision": None}

    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        result["decision"] = query.data
        
        if query.data == "approve":
            await query.edit_message_caption("⏳ جاري النشر على بينترست...")
            pin_url = post_to_pinterest(img_path, ayah_data)
            await query.edit_message_caption(f"✅ تم النشر بنجاح!\n\n{pin_url}")
        else:
            await query.edit_message_caption("🔄 سيتم إرسال آية جديدة غداً...")
        
        app.stop_running()

    app.add_handler(CallbackQueryHandler(button_handler))
    await app.initialize()
    await app.start()
    await send_for_review(ayah_data, img_path)
    await app.updater.start_polling()
    await asyncio.sleep(300)  # ينتظر 5 دقائق للرد
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

async def main():
    ayah_data = fetch_random_ayah()
    img_path = generate_image(ayah_data)
    await wait_for_decision(ayah_data, img_path)

if __name__ == "__main__":
    asyncio.run(main())
