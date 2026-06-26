import os
import requests
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
    arabic_text = r.json()["data"]["text"]
    surah_name = r.json()["data"]["surah"]["name"]

    return {
        "text": arabic_text,
        "surah": surah_name,
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} — آية {ayah_num}"
    }

def generate_background():
    places = ["mountains", "lake", "forest", "waterfall", "green valley"]
    times = ["sunrise", "golden hour", "misty morning", "sunset"]

    prompt = (
        f"A beautiful {random.choice(places)} during {random.choice(times)}, "
        "photorealistic, peaceful, soft light, no people, no buildings, no text, portrait"
    )

    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    
    # طلب الصورة مباشرة وتفادي الحفظ المؤقت لتسريع العملية وثبات الأبعاد
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return io.BytesIO(response.content)
    
def generate_image(ayah_data):
    # استخدام الأبعاد المثالية لـ Pinterest (نسبة 9:16) لظهور احترافي
    width, height = 1080, 1920
    background_data = generate_background()

    img = Image.open(background_data).convert("RGBA")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # إضافة تعتيم سينمائي خفيف (Overlay) لضمان وضوح الخط الأبيض فوق أي صورة طبيعية
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 70)) # شفافية مدروسة بنسبة 27%
    img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)

    # تحميل الخطوط مع التعامل الذكي في حال عدم وجود الملف
    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 75)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 42)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # تقسيم الآية لسطور بشكل متناسق ذكي
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        # ترك مسافة أمان (Padding) على الأطراف لجمالية التصميم
        if bbox[2] - bbox[0] > width - 180:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # ضبط التباعد بين السطور وحساب نقطة البداية ليكون النص متمركزاً عمودياً تماماً
    line_spacing = 115
    total_height = len(lines) * line_spacing
    start_y = (height - total_height) // 2 - 40 

    # إعدادات الظل الناعم للنص (Drop Shadow) ليعطي طابع الحسابات الكبرى
    shadow_offset = (3, 3)
    shadow_color = (0, 0, 0, 200)
    text_color = (255, 255, 255, 255)

    # رسم أسطر الآية (تعديل الخطأ السابق ورسم الـ line الفعلي)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        
        # الظل خلف النص
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        # النص الأساسي الأبيض
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # رسم المرجع (اسم السورة والآية) أسفل النص مباشرة بمسافة ثابتة وأنيقة
    ref_y = start_y + total_height + 40
    
    # ظل المرجع
    draw.text((width // 2 + 2, ref_y + 2), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    # نص المرجع بلون أبيض عاجي خفيف وجذاب
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=(240, 240, 240, 255), anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
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
