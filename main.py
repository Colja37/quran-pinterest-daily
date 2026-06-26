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
    
    # الآية محاطة بالأقواس القرآنية المزخرفة ﴿ ﴾
    arabic_text = f"﴿ {res_data['text']} ﴾"
    
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": f"سُورَةُ {surah_name}",
        "ayah": ayah_num,
        "ref": f"الآية ({ayah_num})"
    }

def get_beige_texture(width, height):
    """توليد خلفية بيج ثابتة بملمس ورقي ناعم وفخم يطابق تماماً صورة قرآن_3.jpg"""
    prompt = "premium warm beige paper texture, blank vintage parchment background, smooth rustic grainy paper, high resolution"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed=777"
    try:
        response = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS)
    except:
        # لون بيج دافئ جداً كخيار احتياطي في حال انقطاع السيرفر
        return Image.new("RGBA", (width, height), (232, 224, 207, 255))

def generate_image(ayah_data):
    # أبعاد العرض المثالية المتناسقة (1200x675)
    width, height = 1200, 675
    
    # جلب الخلفية البيج الورقية (تم إلغاء الطبيعة تماماً)
    img = get_beige_texture(width, height)
    draw = ImageDraw.Draw(img)

    # تحميل الخطوط العربية الأصيلة
    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 38)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 52)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 32)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    # الألوان المعتمدة بناءً على المخطوطة الأصلية في صورة قرآن_3.jpg
    dark_brown = (65, 43, 21, 255)       # لون الخط البني الداكن للآية والإطارات
    banner_fill = (222, 197, 161, 255)    # لون حشوة برواز السورة (بيج مصفر/ذهبي خافت)
    inner_line_color = (138, 99, 59, 255) # لون الخط الداخلي الرفيع للبرواز

    # 📏 1. بناء برواز السورة الفخم المتناسق مع صورة قرآن_3.jpg 📏
    panel_w, panel_h = 650, 80
    px1 = (width - panel_w) // 2
    py1 = 65
    px2 = px1 + panel_w
    py2 = py1 + panel_h
    
    # رسم المستطيل الخارجي لبرواز السورة مع حواف دائرية خفيفة
    draw.rounded_rectangle([px1, py1, px2, py2], radius=4, fill=banner_fill, outline=dark_brown, width=3)
    
    # رسم خط برواز داخلي رفيع ليعطي تأثير المصحف العتيق
    padding = 6
    draw.rounded_rectangle([px1 + padding, py1 + padding, px2 - padding, py2 - padding], radius=2, outline=inner_line_color, width=1)

    # كتابة اسم السورة في منتصف البرواز تماماً باللون الداكن الفاخر
    draw.text((width // 2, py1 + (panel_h // 2) - 2), ayah_data["surah"], font=font_surah, fill=dark_brown, anchor="mm")

    # 2. تقسيم الآية الكريمة لسطور متناسقة مع أبعاد العرض
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

    # 3. حساب الموقع العمودي المتمركز بدقة أسفل برواز السورة
    line_spacing = 90
    total_text_height = len(lines) * line_spacing
    start_y = py2 + ((height - py2 - total_text_height) // 2) - 15

    # رسم أسطر الآية الكريمة باللون البني الداكن (بدون ظلال سوداء مشوهة)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=dark_brown, anchor="mm")

    # 4. رسم رقم الآية في الأسفل (مثل شكل التشكيل الجانبي الصغير في المصاحف)
    ref_y = height - 70
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=(120, 100, 80, 255), anchor="mm")

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
    print("تم توليد قالب المصحف الشريف بالبرواز المعتمد بنجاح!")

if __name__ == "__main__":
    asyncio.run(run())
