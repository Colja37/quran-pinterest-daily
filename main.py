def generate_image(ayah_data):
    # الأبعاد العريضة المتناسقة (1200x675)
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    # 📏 تكبير أحجام الخطوط لملء المساحات الفاضية بشكل احترافي 📏
    try:
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 75)  # تم التكبير من 54 إلى 75
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 38)   # تم التكبير من 32 إلى 38
    except:
        font_ayah = ImageFont.load_default()
        font_ref = font_ayah

    # اللون البني الداكن القرآني الفخم
    quran_brown = (55, 40, 25, 255)

    # 1. تقسيم الآية الكريمة إلى سطور (مع إعطاء مساحة عرضية أكبر لتملأ الشاشة)
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        # ترك هامش أمان جانبي متناسق (200 بكسل فقط بدلاً من 260) ليمتد النص عرضياً
        if bbox[2] - bbox[0] > width - 200:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب الارتفاع الإجمالي الجديد للكتلة بعد تكبير الخط
    line_spacing = 115  # زيادة التباعد بين السطور لتتناسب مع حجم الخط الجديد 75
    total_lines_height = len(lines) * line_spacing
    total_block_height = total_lines_height + 50 + 40  # 50 مسافة فاصلة، 40 حجم المرجع الجديد
    
    # التمركز العمودي المثالي في السنتر تماماً
    start_y = (height - total_block_height) // 2

    # 3. رسم أسطر الآية الكريمة بحجمها الضخم والواضح
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 4. رسم اسم السورة ورقم الآية تحت النص مباشرة بمسافة وثيقة وأنيقة
    ref_y = start_y + total_lines_height + 40
    
    # لون بني ملكي متناسق للمرجع
    ref_color = (100, 85, 70, 255)
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=ref_color, anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
    return img_path
