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
    
# ---------------------------------------------------------
# دالة إنشاء الصورة الجديدة كلياً - نظيفة واحترافية
# ---------------------------------------------------------
def generate_image(ayah_data):
    # استخدام أبعاد الـ Pinterest الذهبية (نسبة 9:16) لظهور مثالي
    width, height = 1080, 1920
    
    # جلب صورة طبيعية عشوائية
    background_data = generate_background()

    img = Image.open(background_data).convert("RGBA")
    # تغيير الحجم باستخدام أفضل خوارزمية جودة (LANCZOS)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # 🌟 الإضافة السحرية: طبقة تعتيم سينمائي خفيفة (Overlay) 🌟
    # هذه الطبقة السوداء الشفافة بنسبة 27% (70 من 255) 
    # تضمن أن النص الأبيض واضح ومقروء تماماً مهما كانت الخلفية فاتحة أو مظلمة.
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 70)) 
    img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)

    # تحميل الخطوط مع التعامل الذكي في حال عدم وجود الملف
    # يفضل استخدام خطوط عربية حديثة تدعم التشكيل مثل Cairo-Medium أو Tajawal
    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 75)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 42)
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # 1. تنسيق الآية: تقسيم تلقائي لسطور متناسقة (Text Wrap)
    # هذه الدالة تتكيف مع طول النص ليكون له هوامش مريحة
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        # ترك هامش أمان جانبي كبير لجمالية التصميم
        if bbox[2] - bbox[0] > width - 180:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب موقع التمركز العمودي المثالي
    line_spacing = 115
    total_text_height = len(lines) * line_spacing
    start_y = (height - total_text_height) // 2 - 40 

    # 3. إعدادات الظل الناعم للنص (Drop Shadow) لزيادة البروز
    shadow_offset = (3, 3)
    shadow_color = (0, 0, 0, 200) # ظل أسود داكن ناعم
    text_color = (255, 255, 255, 255) # نص أبيض ناصع

    # 4. رسم أسطر الآية (تعديل الخطأ السابق ورسم الـ line الفعلي)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        
        # رسم الظل خلف النص (لزيادة الوضوح)
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        # رسم النص الأساسي الأبيض
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # 5. تنسيق ورسم المرجع بأسلوب احترافي وهادئ
    # تم حذف التكرار "سورة سورة" وجعله "سورة نوح • آية 16"
    reference_text = f"سورة {ayah_data['surah']} • آية {ayah_data['ayah']}"
    ref_y = start_y + total_text_height + 40 # مسافة ثابتة أسفل الآية مباشرة
    
    # ظل المرجع
    draw.text((width // 2 + 2, ref_y + 2), reference_text, font=font_ref, fill=shadow_color, anchor="mm")
    # نص المرجع بلون أبيض خافت قليلاً ومريح للعين
    draw.text((width // 2, ref_y), reference_text, font=font_ref, fill=(240, 240, 240, 255), anchor="mm")

    img_path = "/tmp/ayah_image.png"
    # الحفظ بجودة عالية
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
