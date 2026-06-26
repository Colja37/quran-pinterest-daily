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
    
    # إضافة أقواس التلاوة الفخمة حول الآية تلقائياً مثل الصورة الأولى ﴿ ... ﴾
    arabic_text = f"﴿ {res_data['text']} ﴾"
    
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": surah_name,
        "ayah": ayah_num,
        "ref": f"سورة {surah_name} — الآية ({ayah_num})"
    }

def get_paper_texture(width, height, template_type):
    """توليد خلفيات ملمس ورقي (Texture) حقيقي عبر الذكاء الاصطناعي لمنع الألوان السادة السيئة"""
    if template_type == "mushaf_old":
        # نفس الصورة الأولى: ورق قديم محبب بني فاتح
        prompt = "old vintage paper texture background, blank beige parchment, grainy rustic, high resolution, top view"
    else: # mushaf_grey
        # نفس الصورة الثانية: ورق رمادي/كريمي ناعم بملمس خفيف
        prompt = "minimalist light grey concrete paper texture background, clean rustic stone wall, solid soft pattern"
        
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 5000)}"
    try:
        response = requests.get(url, timeout=40)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS)
    except:
        # كود احتياطي في حال انقطاع السيرفر
        color = (235, 225, 210, 255) if template_type == "mushaf_old" else (225, 223, 218, 255)
        return Image.new("RGBA", (width, height), color)

def generate_nature_background(width, height):
    """قالب الطبيعة العريض بنسبة متناسقة"""
    places = ["misty forest mountains", "calm autumn lake", "quiet golden valley"]
    prompt = f"A beautiful serene {random.choice(places)} sunrise, soft lighting, cinematic, aesthetic landscape background"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 5000)}"
    try:
        response = requests.get(url, timeout=40)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        # تعتيم ناعم جداً ليبرز الخط الأبيض
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 65))
        return Image.alpha_composite(img, overlay), (255, 255, 255, 255), (0, 0, 0, 180)
    except:
        return Image.new("RGBA", (width, height), (35, 40, 45, 255)), (255, 255, 255, 255), (0, 0, 0, 150)

def generate_image(ayah_data):
    # 🔄 أبعاد العرض الاحترافية للمنشورات والمماثلة للصور المرسلة تماماً 🔄
    width, height = 1200, 675
    
    # اختيار عشوائي بين القوالب الثلاثة التي حددتها (2 ورق و 1 طبيعة)
    templates = ["mushaf_old", "mushaf_grey", "nature"]
    chosen_template = random.choice(templates)
    
    if chosen_template == "mushaf_old":
        img = get_paper_texture(width, height, "mushaf_old")
        text_color, shadow_color = (40, 35, 30, 255), (150, 140, 130, 40) # خط داكن مثل الصورة 1
    elif chosen_template == "mushaf_grey":
        img = get_paper_texture(width, height, "mushaf_grey")
        text_color, shadow_color = (50, 45, 40, 255), (160, 160, 160, 30) # خط داكن مثل الصورة 2
    else:
        img, text_color, shadow_color = generate_nature_background(width, height)

    draw = ImageDraw.Draw(img)

    # حساب حجم الخط تلقائياً بناءً على طول النص لملء الشاشة بذكاء وتجنب الفراغات
    text_length = len(ayah_data["text"])
    if text_length < 45:
        font_size = 65  # نص قصير -> خط كبير ليملأ المساحة أفقياً
    elif text_length < 90:
        font_size = 52
    else:
        font_size = 42  # نص طويل -> خط أصغر ليتناسق في سطرين أو ثلاثة

    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", font_size)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 34)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # تقسيم النص لسطور تتناسب مع العرض الجديد (ترك مسافة أمان مريحة للعين)
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 220:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # التوزيع العمودي المريح: وضع النص في المركز
    line_spacing = font_size + 30
    total_text_height = len(lines) * line_spacing
    
    # رفع النص قليلاً للأعلى ليترك مساحة متناسقة للمرجع في الأسفل
    start_y = (height - total_text_height) // 2 - 25

    # رسم أسطر الآية
    shadow_offset = (1, 1) if "mushaf" in chosen_template else (2, 2)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        
        # رسم الظل خلف الحروف
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        # رسم النص
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # رسم المرجع في الأسفل تماماً بمسافة مريحة وثابتة كالحسابات الاحترافية
    ref_y = height - 80
    draw.text((width // 2 + 1, ref_y + 1), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    
    # لون مرجع خافت وأنيق يتناسب مع الخلفية
    ref_color = (100, 90, 80, 255) if "mushaf" in chosen_template else (210, 210, 210, 255)
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
        f"{ayah_data['text']}\n\n"
        f"─────────────────\n"
        f"📌 *للنشر على Pinterest:*\n"
        f"_{ayah_data['text']}_\n"
        f"_{ayah_data['ref']}_\n"
    )

    with open(img_path, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )
    print("تم توليد الصورة بالعرض مع ملمس المصحف الورقي بنجاح!")

if __name__ == "__main__":
    asyncio.run(run())
