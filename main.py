import os
import requests
import random
from PIL import Image, ImageDraw, ImageFont
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

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

    draw.rectangle([40, 40, width-40, height-40], outline="#c9a84c", width=3)
    draw.rectangle([55, 55, width-55, height-55], outline="#c9a84c", width=1)

    try:
        font_big = ImageFont.truetype("fonts/Amiri-Regular.ttf", 72)
        font_small = ImageFont.truetype("fonts/Amiri-Regular.ttf", 42)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big
        font_ref = font_big

    draw.text((width//2, 150), "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
              font=font_small, fill="#c9a84c", anchor="mm")
    draw.line([(150, 220), (850, 220)], fill="#c9a84c", width=1)

    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_big)
        if bbox[2] - bbox[0] > width - 200:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    y_start = (height - len(lines) * 100) // 2 - 50
    for line in lines:
        draw.text((width//2, y_start), line,
                  font=font_big, fill="#ffffff", anchor="mm")
        y_start += 100

    draw.line([(150, height-280), (850, height-280)], fill="#c9a84c", width=1)
    draw.text((width//2, height-200), ayah_data["ref"],
              font=font_ref, fill="#c9a84c", anchor="mm")
    draw.text((width//2, height-120), "✦ آية اليوم ✦",
              font=font_ref, fill="#c9a84c", anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.save(img_path)
    return img_path

async def run():
    ayah_data = fetch_random_ayah()
    img_path = generate_image(ayah_data)

    bot = Bot(token=TELEGRAM_TOKEN)

    caption = (
        f"🌙 *{ayah_data['ref']}*\n\n"
        f"{ayah_data['text']}\n\n"
        f"─────────────────\n"
        f"📌 *للنشر على Pinterest:*\n"
        f"١. حمّل الصورة\n"
        f"٢. ارفعها على Pinterest\n"
        f"٣. استخدم هذا الوصف:\n\n"
        f"_{ayah_data['text']}_\n"
        f"_{ayah_data['ref']}_\n\n"
        f"#قرآن #آية_اليوم #إسلام #ذكر #قرآن_كريم"
    )

    with open(img_path, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )

    print("تم الإرسال بنجاح")

if __name__ == "__main__":
    asyncio.run(run())
