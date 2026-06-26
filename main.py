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
        return Image.new("RGBA", (width, height), (232, 224, 207, 255))

def generate_image(ayah_data):
    # الأبعاد العريضة المتناسقة (1200x675)
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    # مقاسات الخطوط المتزنة والمضمونة لمنع توقف السكربت ولتغطية الفراغات
    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 68)  # حجم مثالي آمن وضخم لملء الشاشة
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)   # حجم واضح للمرجع
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # اللون البني الداكن القرآني الفخم (تم اعتماده للآية والمرجع معاً لزيادة الوضوح)
    quran_brown = (55, 40, 25, 255)

    # 1. تقسيم الآية الكريمة إلى سطور بشكل آمن وثابت
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        # ترك مسافة أمان جانبية 220 بكسل تضمن عدم خروج النص أو ضرب الكود
        if bbox[2] - bbox[0] > width - 220:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب الارتفاع الإجمالي للكتلة
    line_spacing = 105  # تباعد أسطر متناسق مع حجم الخط 68
    total_lines_height = len(lines) * line_spacing
    total_block_height = total_lines_height + 45 + 38
    
    # التمركز العمودي في المنتصف تماماً (انتجر //)
    start_y = (height - total_block_height) // 2

    # 3. رسم أسطر الآية الكريمة
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 4. رسم المرجع (اسم السورة والآية) بلون واضح وداكن أسفل النص مباشرة
    ref_y = start_y + total_lines_height + 40
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=quran_brown, anchor="mm")

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
    print("تم توليد التصميم وإرساله بنجاح تام!")

if __name__ == "__main__":
    asyncio.run(run())
