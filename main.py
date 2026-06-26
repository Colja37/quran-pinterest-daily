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

def get_premium_beige_background(width, height, chosen_template):
    """توليد خلفية بيج بملمس ورقي فخم (Texture) ثابت، أو دمج طبيعة سينمائية هادئة"""
    if chosen_template == "nature":
        # دمج الطبيعة مع الحفاظ على روح التصميم
        prompt = "serene misty mountains lake sunrise, soft aesthetic light, warm cinematic landscape background, 8k"
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 5000)}"
        try:
            response = requests.get(url, timeout=40)
            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            # تعتيم ناعم جداً ليبرز النص
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 40))
            return Image.alpha_composite(img, overlay), (255, 255, 255, 255), (0, 0, 0, 200)
        except:
            pass

    # القالب الأساسي الثابت: ورق بيج/كريمي دافئ ومحبب ومريح جداً للعين
    prompt = "premium warm beige paper texture, blank vintage parchment background, smooth rustic grainy paper, high resolution"
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + f"?width={width}&height={height}&seed={random.randint(1, 1000)}"
    try:
        response = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return img.resize((width, height), Image.Resampling.LANCZOS), (45, 40, 35, 255), (180, 170, 150, 40)
    except:
        # لون بيج سادة دافئ جداً كخطة بديلة طارئة
        img = Image.new("RGBA", (width, height), (245, 238, 221, 255))
        return img, (45, 40, 35, 255), (180, 170, 150, 40)

def generate_image(ayah_data):
    # أبعاد العرض المثالية والمطابقة للصور (1200x675)
    width, height = 1200, 675
    
    # اختيار القالب (التثبيت على البيج الفاخر، مع بقاء الطبيعة كخيار متجدد)
    chosen_template = random.choice(["beige_1", "beige_2", "nature"])
    img, text_color, shadow_color = get_premium_beige_background(width, height, chosen_template)
    
    draw = ImageDraw.Draw(img)

    # تحميل الخطوط العربية الأصيلة
    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 40)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 54)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 34)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    # 🌟 1. رسم إطار عنوان السورة المزخرف (الاحترافي) 🌟
    # قمنا ببرمجة إطار إسلامي كلاسيكي ناعم ومفتوح من الأطراف ليحاكي المخطوطات الحقيقية
    frame_w, frame_h = 520, 85
    fx1 = (width - frame_w) // 2
    fy1 = 65
    fx2 = fx1 + frame_w
    fy2 = fy1 + frame_h
    
    # رسم خطين متوازيين فخمين مع حواف زخرفية جانبية صغيرة بالرسم بدلاً من المستطيل المصمت المزعج
    draw.line([(fx1, fy1), (fx2, fy1)], fill=text_color, width=2)
    draw.line([(fx1, fy2), (fx2, fy2)], fill=text_color, width=2)
    # حواف جانبية كلاسيكية
    draw.line([(fx1, fy1), (fx1 + 15, fy1 + frame_h//2)], fill=text_color, width=2)
    draw.line([(fx1 + 15, fy1 + frame_h//2), (fx1, fy2)], fill=text_color, width=2)
    draw.line([(fx2, fy1), (fx2 - 15, fy1 + frame_h//2)], fill=text_color, width=2)
    draw.line([(fx2 - 15, fy1 + frame_h//2), (fx2, fy2)], fill=text_color, width=2)

    # كتابة اسم السورة داخل الخطوط المزخرفة في المنتصف تماماً
    draw.text((width // 2, fy1 + (frame_h // 2) - 2), ayah_data["surah"], font=font_surah, fill=text_color, anchor="mm")

    # 2. تقسيم الآية الكريمة لسطور متناسقة
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 240:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 3. حساب الموقع العمودي الذكي أسفل عنوان السورة
    line_spacing = 90
    total_text_height = len(lines) * line_spacing
    start_y = fy2 + ((height - fy2 - total_text_height) // 2) - 15

    # رسم أسطر الآية مع ظل ناعم جداً يكاد لا يرى ليعطي عمقاً طبيعياً للمخطوطة
    shadow_offset = (1, 1) if chosen_template != "nature" else (2, 2)
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2 + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_ayah, fill=shadow_color, anchor="mm")
        draw.text((width // 2, current_y), line, font=font_ayah, fill=text_color, anchor="mm")

    # 4. رسم رقم الآية في الأسفل بشكل هادئ ومنعزل
    ref_y = height - 75
    draw.text((width // 2 + 1, ref_y + 1), ayah_data["ref"], font=font_ref, fill=shadow_color, anchor="mm")
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=text_color, anchor="mm")

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
    print("تم توليد المخطوطة الإسلامية الفخمة بالخلفية البيج!")

if __name__ == "__main__":
    asyncio.run(run())
