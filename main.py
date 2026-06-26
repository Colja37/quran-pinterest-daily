import os
import requests
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import asyncio
import io
from telegram import Bot

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def fetch_random_ayah():
    surah = random.randint(1, 114)
    response = requests.get(f"https://api.alquran.cloud/v1/surah/{surah}")
    data = response.json()
    total_ayahs = data["data"]["numberOfAyahs"]
    ayah_num = random.randint(1, total_ayahs)

    r = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah_num}/ar.alafasy")
    res_data = r.json()["data"]
    
    arabic_text = f"﴿ {res_data['text']} ﴾"
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": f"سُورَةُ {surah_name}",
        "ayah": ayah_num,
        "ref": f"الآية ({ayah_num})"
    }

def get_clean_beige_background(width, height):
    """جلب الخلفية البيج بملمس الورق القديم الفاخر"""
    prompt = "premium warm old vintage paper texture, blank parchment paper background, rustic high resolution"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed=888"
    try:
        response = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS)
    except:
        return Image.new("RGBA", (width, height), (230, 220, 202, 255))

def generate_image(ayah_data):
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 50)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 30)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    quran_brown = (55, 40, 25, 255)

    # 1. تقسيم الآية الكريمة إلى سطور
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 280:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب أبعاد ومساحة المكونات بدقة (ضمان أرقام صحيحة انتجر //)
    panel_w, panel_h = 520, 75
    line_spacing = 85
    total_lines_height = len(lines) * line_spacing
    
    # الارتفاع الإجمالي لكتلة التصميم كاملة
    total_block_height = panel_h + 45 + total_lines_height + 25 + 30
    
    # استخدام القسمة المطورة // لضمان عدم خروج أرقام عشرية تسبب توقف السكربت
    block_start_y = (height - total_block_height) // 2

    # 3. رسم برواز السورة متمركز في السنتر عمودياً
    px1 = (width - panel_w) // 2
    py1 = block_start_y
    px2 = px1 + panel_w
    py2 = py1 + panel_h

    # رسم البرواز الشفاف
    draw.rectangle([px1, py1, px2, py2], fill=None, outline=quran_brown, width=2)
    pad = 5
    draw.rectangle([px1 + pad, py1 + pad, px2 - pad, py2 - pad], fill=None, outline=quran_brown, width=1)
    
    # الزخارف الجانبية للبرواز
    draw.line([(px1 - 15, py1 + panel_h//2), (px1, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px1 - 15, py1 + panel_h//2), (px1, py2 - 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + panel_h//2), (px2, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + panel_h//2), (px2, py2 - 15)], fill=quran_brown, width=2)

    # اسم السورة داخل البرواز
    draw.text((width // 2, py1 + (panel_h // 2) - 2), ayah_data["surah"], font=font_surah, fill=quran_brown, anchor="mm")

    # 4. رسم أسطر الآية الكريمة قريبة وتحت البرواز مباشرة
    start_y = py2 + 45 
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 5. رسم رقم الآية بالأسفل بشكل متناسق
    ref_y = start_y + total_lines_height + 25
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=(110, 95, 80, 255), anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
    return img_path

async def run():
    ayah_data = fetch_random_ayah()
    img_path = generate_image(ayah_data)

    bot = Bot(token=TELEGRAM_TOKEN)

    caption = (
        f"🌙 *{ayah_data['surah']} — {ayah_data['ref']}*\n\n"
        f"{ayah_data['text']}\n"
    )

    with open(img_path, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )
    print("تم الإصلاح وعاود السكربت الإرسال بنجاح بالهيكل الجديد!")

if __name__ == "__main__":
    asyncio.run(run())
