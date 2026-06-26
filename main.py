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
    
    # الآية محاطة بالأقواس القرآنية الفخمة ﴿ ﴾
    arabic_text = f"﴿ {res_data['text']} ﴾"
    
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": f"سورة {surah_name}",
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} — الآية ({ayah_num})"
    }

def get_clean_beige_background(width, height):
    """جلب الخلفية البيج بملمس الورق الفاخر الهادئ"""
    prompt = "premium warm old vintage paper texture, blank parchment paper background, rustic high resolution"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed=888"
    try:
        response = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS)
    except:
        # لون بيج دافئ كخيار طوارئ مضمون
        return Image.new("RGBA", (width, height), (232, 224, 207, 255))

def generate_image(ayah_data):
    # الأبعاد العريضة المتناسقة (1200x675)
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 54)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 32)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # اللون البني الداكن القرآني الفخم والمريح للعين
    quran_brown = (55, 40, 25, 255)

    # 1. تقسيم الآية الكريمة إلى سطور متناسقة
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 260:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب الارتفاع الإجمالي للكتلة (الأسطر + المسافة + المرجع الصغير)
    line_spacing = 90
    total_lines_height = len(lines) * line_spacing
    total_block_height = total_lines_height + 40 + 35 # 40 مسافة فاصلة، 35 حجم المرجع التقريبي
    
    # التمركز العمودي المثالي في السنتر (باستخدام الانتجر //)
    start_y = (height - total_block_height) // 2

    # 3. رسم أسطر الآية الكريمة متمركزة تماماً
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 4. رسم اسم السورة ورقم الآية تحت النص مباشرة بخط صغير وأنيق
    ref_y = start_y + total_lines_height + 30
    
    # لون بني أخف قليلاً للمرجع ليعطي تدرجاً بصرياً مريحاً
    ref_color = (110, 95, 80, 255)
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=ref_color, anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
    return img_path

async def run():
    ayah_data = fetch_random_ayah()
    img_path = generate_image(ayah_data)

    bot = Bot(token=TELEGRAM_TOKEN)

    caption = (
        f"🌙 *{ayah_data['ref']}*\n\n"
        f"{ayah_data['text']}\n"
    )

    with open(img_path, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )
    print("تم توليد التصميم البسيط والأنيق بنجاح!")

if __name__ == "__main__":
    asyncio.run(run())
