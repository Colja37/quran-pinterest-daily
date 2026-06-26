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

def get_base_assets(width, height):
    """جلب الخلفية البيج وصورة البرواز الزخرفي الخارجي الحقيقي عالي الجودة"""
    # 1. جلب الخلفية البيج بملمس ورقي ناعم
    bg_prompt = "premium warm beige paper texture, blank vintage parchment background, high resolution"
    bg_url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(bg_prompt) + f"?width={width}&height={height}&seed=777"
    
    try:
        bg_res = requests.get(bg_url, timeout=30)
        bg_img = Image.open(io.BytesIO(bg_res.content)).convert("RGBA")
    except:
        bg_img = Image.new("RGBA", (width, height), (235, 226, 208, 255))

    # 2. جلب صورة البرواز الإسلامي الزخرفي الشفاف (PNG) لعنوان السورة
    # نستخدم بروازاً زخرفياً ذهبياً/بني حقيقي ليعطي نفس مظهر المصحف تماماً
    frame_url = "https://raw.githubusercontent.com/A7med9/Quran-Assets/main/surah_frame.png"
    try:
        frame_res = requests.get(frame_url, timeout=20)
        frame_img = Image.open(io.BytesIO(frame_res.content)).convert("RGBA")
    except:
        # برواز بديل في حال تعذر الرابط الأول
        frame_img = Image.new("RGBA", (700, 110), (222, 197, 161, 200))
        
    return bg_img, frame_img

def generate_image(ayah_data):
    # الأبعاد العريضة المتناغمة (1200x675)
    width, height = 1200, 675
    
    # تحميل الخلفية والبرواز الخارجي الزخرفي
    img, frame_img = get_base_assets(width, height)
    
    # تغيير حجم البرواز الخارجي ليكون متناسقاً (700 عرض × 110 ارتفاع)
    frame_w, frame_h = 700, 110
    frame_img = frame_img.resize((frame_w, frame_h), Image.Resampling.LANCZOS)
    
    # دمج البرواز الزخرفي في أعلى الشاشة بالمنتصف تماماً
    frame_x = (width - frame_w) // 2
    frame_y = 50
    img.paste(frame_img, (frame_x, frame_y), frame_img)
    
    draw = ImageDraw.Draw(img)

    # إعداد الخطوط العربية الفخمة (يفضل تحميل خط مثل Amiri-Bold أو خط عثماني)
    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 38)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 52)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 32)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    dark_brown = (50, 35, 20, 255) # اللون البني الداكن القرآني

    # كتابة اسم السورة داخل البرواز الزخرفي الخارجي مباشرة
    draw.text((width // 2, frame_y + (frame_h // 2) - 2), ayah_data["surah"], font=font_surah, fill=dark_brown, anchor="mm")

    # تقسيم الآية الكريمة لسطور
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

    # 📏 حل مشكلة البعد: جعل المسافة قريبة جداً أسفل البرواز مباشرة 📏
    line_spacing = 85
    # الآية تبدأ بالظهور مباشرة بعد نهاية البرواز بمسافة قريبة (45 بكسل فقط) لتبدو متناسقة وملتحمة
    start_y = frame_y + frame_h + 45

    # رسم أسطر الآية الكريمة قريبة ومتراصة بشكل أنيق
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=dark_brown, anchor="mm")

    # رسم رقم الآية في الأسفل هادئ وقريب من النص أيضاً
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
    print("تم توليد التصميم بالزخارف الخارجية والمسافات القريبة!")

if __name__ == "__main__":
    asyncio.run(run())
