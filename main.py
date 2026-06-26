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
    res_data = r.json()["data"]
    arabic_text = res_data["text"]
    
    # جلب اسم السورة وتصفيته من كلمة "سورة" لمنع التكرار
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": surah_name,
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} • آية {ayah_num}"
    }

def generate_background():
    places = ["mountains", "lake", "forest", "waterfall", "green valley"]
    times = ["sunrise", "golden hour", "misty morning", "sunset"]

    prompt = (
        f"A beautiful {random.choice(places)} during {random.choice(times)}, "
        "photorealistic, peaceful, soft light, no people, no buildings, no text, portrait"
    )

    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return io.BytesIO(response.content)
    
def generate_image(ayah_data):
    # أبعاد الـ Pinterest المثالية
    width, height = 1080, 1920
    background_data = generate_background()

    img = Image.open(background_data).convert("RGBA")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # طبقة تعتيم خفيفة جداً لإبراز الخط الأبيض
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 75)) 
    img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)

    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 75)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 44)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # تقسيم الآية لسطور متناسقة
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 180:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # حساب التمركز العمودي في المنتصف تماماً
    line_spacing = 120
    total_text_height = len(lines) * line_spacing
    start_y = (height - total_text_height) // 2 - 50 

    # إعدادات الظل الناعم (Drop Shadow)
    shadow_offset = (3, 3)
    shadow_color = (0, 0, 0, 220)
    text_color = (255, 255, 255, 255)

    # رسم أسطر الآية الكريمة
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        
        # الظل
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        # النص الأساسي
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # رسم المرجع الموحد والمنقح أسفل الآية مباشرة
    ref_y = start_y + total_text_height + 30
    
    # ظل المرجع
    draw.text((width // 2 + 2, ref_y + 2), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    # نص المرجع
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=(245, 245, 245, 255), anchor="mm")

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

    print("تم الإرسال بنجاح وتفادي تكرار الاسم!")

if __name__ == "__main__":
    asyncio.run(run())
