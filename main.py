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
    
    # تنظيف اسم السورة لمنع التكرار
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": surah_name,
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} • آية {ayah_num}"
    }

def generate_nature_background(width, height):
    """قالب الطبيعة: يجلب خلفية عشوائية بالعرض من Pollinations"""
    places = ["mountains", "lake", "forest", "waterfall", "green valley"]
    times = ["sunrise", "golden hour", "misty morning", "sunset"]
    prompt = (
        f"A beautiful {random.choice(places)} during {random.choice(times)}, "
        "photorealistic, peaceful, soft light, no people, no buildings, no text, landscape"
    )
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    try:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # إضافة تعتيم خفيف لإبراز النص الأبيض
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 80)) 
        return Image.alpha_composite(img, overlay), (255, 255, 255, 255), (0, 0, 0, 200)
    except Exception as e:
        print(f"فشل جلب صورة الطبيعة، تحويل تلقائي للمينيمال: {e}")
        return generate_minimal_background(width, height)

def generate_mushaf_background(width, height):
    """قالب المصحف: خلفية كريمي كلاسيكية هادئة مع نص داكن"""
    # لون الورق القديم المريح للعين (Creamy/Beige)
    img = Image.new("RGBA", (width, height), (245, 240, 225, 255))
    draw = ImageDraw.Draw(img)
    
    # رسم إطار داخلي بسيط ورفيع يعطي طابع الكتب والمصاحف
    padding = 40
    draw.rectangle(
        [(padding, padding), (width - padding, height - padding)],
        outline=(160, 140, 110, 255),  # لون ذهبي خافت/بني
        width=3
    )
    # النص سيكون باللون البني الداكن الفاخر والظل خفيف جداً
    return img, (45, 40, 35, 255), (180, 170, 150, 100)

def generate_minimal_background(width, height):
    """قالب المينيمال: خلفية داكنة سادة وعصرية جداً تركز على النص"""
    # درجات الرمادي الداكن الساحر والأنيق
    dark_colors = [
        (25, 28, 36, 255),
        (33, 37, 41, 255),
        (20, 24, 33, 255)
    ]
    img = Image.new("RGBA", (width, height), random.choice(dark_colors))
    # نص أبيض ناصع مع ظل ناعم جداً
    return img, (255, 255, 255, 255), (0, 0, 0, 150)

def generate_image(ayah_data):
    # 🔄 تم تعديل الأبعاد لتصبح بالعرض (Landscape)
    width, height = 1920, 1080
    
    # 🎲 نظام اختيار القوالب العشوائي
    templates = ["nature", "mushaf", "minimal"]
    chosen_template = random.choice(templates)
    print(f"التمبلت المختار اليوم: {chosen_template}")
    
    if chosen_template == "nature":
        img, text_color, shadow_color = generate_nature_background(width, height)
        font_size_ayah = 65  # حجم خط مناسب لأبعاد العرض في الطبيعة
    elif chosen_template == "mushaf":
        img, text_color, shadow_color = generate_mushaf_background(width, height)
        font_size_ayah = 70
    else:  # minimal
        img, text_color, shadow_color = generate_minimal_background(width, height)
        font_size_ayah = 75

    draw = ImageDraw.Draw(img)

    # تحميل الخطوط
    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", font_size_ayah)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 38)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # تقسيم الآية لسطور متناسقة مع أبعاد العرض (المساحة الأفقية أكبر الآن)
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        # بما أن الصورة عريضة، نزيد مساحة أسطر النص (ترك 300 بكسل على الأطراف)
        if bbox[2] - bbox[0] > width - 400:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # حساب التمركز العمودي في المنتصف
    line_spacing = font_size_ayah + 40
    total_text_height = len(lines) * line_spacing
    start_y = (height - total_text_height) // 2 - 30

    # رسم أسطر الآية الكريمة بناءً على ألوان القالب المختار
    shadow_offset = (2, 2)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        
        # رسم الظل
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        # رسم النص الأساسي
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # رسم المرجع (اسم السورة والآية) أسفل النص بمسافة متناسقة
    ref_y = start_y + total_text_height + 25
    
    # ظل المرجع ونصه
    draw.text((width // 2 + 1, ref_y + 1), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    
    # تعديل طفيف للون المرجع ليناسب القالب الفاتح أو الداكن
    ref_text_color = (100, 90, 80, 255) if chosen_template == "mushaf" else (220, 220, 220, 255)
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=ref_text_color, anchor="mm")

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

    print("تم توليد الصورة بالعرض وتطبيق التمبلت العشوائي بنجاح!")

if __name__ == "__main__":
    asyncio.run(run())
