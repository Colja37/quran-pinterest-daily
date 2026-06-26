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
    
    # الآية محاطة بأقواس فخمة لجمالية النص
    arabic_text = f"﴿ {res_data['text']} ﴾"
    
    raw_surah_name = res_data["surah"]["name"]
    surah_name = raw_surah_name.replace("سُورَةُ", "").replace("سورة", "").strip()

    return {
        "text": arabic_text,
        "surah": f"سورة {surah_name}",
        "ayah": ayah_num,
        "ref": f"الآية ({ayah_num})"
    }

def get_paper_texture(width, height, template_type):
    """توليد خلفية بملمس ورقي حقيقي لتطابق الصور المرسلة"""
    if template_type == "mushaf_old":
        prompt = "old vintage paper texture background, blank beige parchment, grainy rustic, high resolution"
    else:
        prompt = "minimalist light grey concrete paper texture background, solid soft pattern"
        
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 5000)}"
    try:
        response = requests.get(url, timeout=40)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS)
    except:
        color = (235, 225, 210, 255) if template_type == "mushaf_old" else (225, 223, 218, 255)
        return Image.new("RGBA", (width, height), color)

def generate_nature_background(width, height):
    places = ["misty forest mountains", "calm autumn lake", "quiet golden valley"]
    prompt = f"A beautiful serene {random.choice(places)} sunrise, soft lighting, aesthetic landscape background"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 5000)}"
    try:
        response = requests.get(url, timeout=40)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 75))
        return Image.alpha_composite(img, overlay), (255, 255, 255, 255), (0, 0, 0, 180), (255, 255, 255, 40)
    except:
        return Image.new("RGBA", (width, height), (35, 40, 45, 255)), (255, 255, 255, 255), (0, 0, 0, 150), (255, 255, 255, 30)

def generate_image(ayah_data):
    # أبعاد العرض الاحترافية المتناسقة (1200x675)
    width, height = 1200, 675
    
    templates = ["mushaf_old", "mushaf_grey", "nature"]
    chosen_template = random.choice(templates)
    
    # إعداد الألوان والخصائص لكل تمبلت بناءً على اختيارك الجديد
    if chosen_template == "mushaf_old":
        img = get_paper_texture(width, height, "mushaf_old")
        text_color, shadow_color = (45, 40, 35, 255), (150, 140, 130, 30)
        panel_color = (215, 200, 180, 255)  # لون شريط السورة (بني فاتح متناسق)
        border_color = (140, 120, 95, 255)
    elif chosen_template == "mushaf_grey":
        img = get_paper_texture(width, height, "mushaf_grey")
        text_color, shadow_color = (50, 45, 40, 255), (170, 170, 170, 30)
        panel_color = (205, 203, 198, 255)  # لون شريط السورة (رمادي متناسق)
        border_color = (130, 130, 130, 255)
    else:
        img, text_color, shadow_color, panel_color = generate_nature_background(width, height)
        border_color = (255, 255, 255, 80)

    draw = ImageDraw.Draw(img)

    # إعداد أحجام الخطوط
    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 52)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 32)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    # 1. رسم شريط اسم السورة العلوي (مثل التمبلت الفخم المعتمد)
    panel_w, panel_h = 500, 75
    panel_x1 = (width - panel_w) // 2
    panel_y1 = 60
    panel_x2 = panel_x1 + panel_w
    panel_y2 = panel_y1 + panel_h
    
    # رسم شريط السورة مع إطار خفيف محيط به
    draw.rectangle([panel_x1, panel_y1, panel_x2, panel_y2], fill=panel_color, outline=border_color, width=2)
    
    # كتابة اسم السورة داخل الشريط في المنتصف تماماً
    draw.text((width // 2, panel_y1 + (panel_h // 2)), ayah_data["surah"], font=font_surah, fill=text_color, anchor="mm")

    # 2. تقسيم الآية لسطور متناسقة
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

    # 3. حساب الموقع العمودي المتمركز أسفل شريط السورة
    line_spacing = 85
    total_text_height = len(lines) * line_spacing
    
    # تبدأ كتابة الآية بعد شريط السورة بمسافة متزنة وتتمركز في المساحة المتبقية
    start_y = panel_y2 + ((height - panel_y2 - total_text_height) // 2) - 20

    # رسم أسطر الآية الكريمة
    shadow_offset = (1, 1) if "mushaf" in chosen_template else (2, 2)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # 4. رسم رقم الآية في الأسفل كمرجع نهائي هادئ
    ref_y = height - 70
    draw.text((width // 2 + 1, ref_y + 1), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    
    ref_color = (110, 100, 90, 255) if "mushaf" in chosen_template else (200, 200, 200, 255)
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=ref_color, anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
    return img_path

async def run():
    ayah_data = fetch_random_ayah()
    img_path = generate_image(ayah_data)

    bot = Bot(token=TELEGRAM_TOKEN)

    caption = (
        f"🌙 *{ayah_data['surah']} — {ayah_data['ref']}*\n\n"
        f"{ayah_data['text']}\n\n"
        f"─────────────────\n"
        f"📌 *للنشر على Pinterest:*\n"
        f"_{ayah_data['text']}_\n"
    )

    with open(img_path, "rb") as photo:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode="Markdown"
        )
    print("تم توليد التمبلت المعتمد والمطور بنجاح وإرساله!")

if __name__ == "__main__":
    asyncio.run(run())
