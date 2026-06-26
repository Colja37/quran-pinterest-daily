import os
import requests
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

def generate_background():
    places = [
        "mountains",
        "lake",
        "forest",
        "waterfall",
        "green valley"
    ]

    times = [
        "sunrise",
        "golden hour",
        "misty morning",
        "sunset"
    ]

    prompt = (
        f"A beautiful {random.choice(places)} during "
        f"{random.choice(times)}, "
        "photorealistic, peaceful, soft light, "
        "no people, no buildings, no text, portrait"
    )

    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)

    response = requests.get(url, timeout=90)
    response.raise_for_status()

    path = "/tmp/background.jpg"

    with open(path, "wb") as f:
        f.write(response.content)

    return path
    
def generate_image(ayah_data):
    width, height = 1000, 1500
    background = generate_background()

    img = Image.open(background).convert("RGB")
    img = img.resize((width, height))
    
    draw = ImageDraw.Draw(img)

    # تحويل الصورة إلى RGBA لدعم الشفافية
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
  

    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 80)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 44)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # تقسيم الآية لسطور
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 160:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # توسيط الآية عمودياً
    total_height = len(lines) * 110
    box_margin = 50

    box_top = (height - total_height) // 2 - 120
    box_bottom = box_top + total_height + 170
    
    overlay_draw.rounded_rectangle(
        (
            70,
            box_top,
            width - 70,
            box_bottom
        ),
        radius=35,
        fill=(0, 0, 0, 110)
    )
    
    # دمج المستطيل مع الصورة
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    y = (height - total_height) // 2 - 60

    for line in lines:
        draw.text((width // 2, y), line,
                  font=font_ayah, fill="white", anchor="mm")
        y += 110

    # اسم السورة في الأسفل
    draw.text((width // 2, height - 180), ayah_data["ref"],
              font=font_ref, fill="white", anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path)
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



