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
        # لون بيج دافئ كخيار طوارئ
        return Image.new("RGBA", (width, height), (230, 220, 202, 255))

def generate_image(ayah_data):
    # الأبعاد العريضة الثابتة (1200x675)
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 50)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 30)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    # اللون البني القرآني الداكن والراقي للكتابة والإطارات
    quran_brown = (55, 40, 25, 255)

    # 📏 1. رسم برواز السورة (مفرغ وشفاف تماماً ليظهر ملمس الورق من خلفه) 📏
    # العرض والارتفاع المتناسق للبرواز
    pw, ph = 520, 75
    px1 = (width - pw) // 2
    py1 = 65
    px2 = px1 + pw
    py2 = py1 + ph

    # رسم المستطيل الخارجي المفرغ (بدون fill ليبقى الورق ظاهراً)
    draw.rectangle([px1, py1, px2, py2], fill=None, outline=quran_brown, width=2)
    # رسم خط داخلي رفيع ليعطي عمق المخطوطات والكتب العتيقة
    pad = 5
    draw.rectangle([px1 + pad, py1 + pad, px2 - pad, py2 - pad], fill=None, outline=quran_brown, width=1)
    
    # إضافة لمسة زخرفية بسيطة على الجانبين الأيمن والأيسر لكسر جمود المستطيل
    draw.line([(px1 - 15, py1 + ph//2), (px1, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px1 - 15, py1 + ph//2), (px1, py2 - 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + ph//2), (px2, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + ph//2), (px2, py2 - 15)], fill=quran_brown, width=2)

    # كتابة اسم السورة داخل البرواز المفرغ
    draw.text((width // 2, py1 + (ph // 2) - 2), ayah_data["surah"], font=font_surah, fill=quran_brown, anchor="mm")

    # 2. تقسيم الآية الكريمة إلى سطور متناسقة
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

    # 3. محاذاة لصيقة: ضبط بداية النص ليكون ملتحماً بالبرواز العلوي دون تباعد
    line_spacing = 85
    start_y = py2 + 45 # مسافة قريبة جداً ومدروسة أسفل البرواز مباشرة

    # رسم أسطر الآية الكريمة بانسيابية تامة فوق الورق البيج
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 4. رسم رقم الآية في الأسفل بشكل هادئ ومتناسق
    ref_y = start_y + (len(lines) * line_spacing) + 25
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
    print("تم إصلاح التصميم الجمالي بالكامل وبأداء مستقر آلياً!")

if __name__ == "__main__":
    asyncio.run(run())
