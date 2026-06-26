def generate_image(ayah_data):
    # الأبعاد العريضة الثابتة (1200x675)
    width, height = 1200, 675
    img = get_clean_beige_background(width, height)
    draw = ImageDraw.Draw(img)

    try:
        font_surah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 36)
        font_ayah = ImageFont.truetype("fonts/Amiri-Regular.ttf", 50)
        font_ref = ImageFont.truetype("fonts/Amiri-Regular.ttf", 30)
    except:
        font_surah = font_ayah = font_ref = ImageFont.load_default()

    quran_brown = (55, 40, 25, 255)

    # 1. تقسيم الآية الكريمة إلى سطور أولاً لمعرفة حجمها الكلي
    words = ayah_data["text"].split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        bbox = draw.textbbox((0, 0), " ".join(current), font=font_ayah)
        if bbox[2] - bbox[0] > width - 280:
            current.pop()
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    # 2. حساب أبعاد ومساحة المكونات بدقة
    panel_w, panel_h = 520, 75
    line_spacing = 85
    total_lines_height = len(lines) * line_spacing
    
    # الارتفاع الإجمالي لكتلة التصميم كاملة (البرواز + المسافة الفاصلة + الأسطر + مسافة المرجع + المرجع)
    total_block_height = panel_h + 45 + total_lines_height + 25 + 30
    
    # حساب نقطة البداية العمودية الديناميكية ليكون التصميم متمركزاً في السنتر تماماً
    block_start_y = (height - total_block_height) // 2

    # 3. رسم برواز السورة بناءً على موقع التمركز الجديد
    px1 = (width - panel_w) // 2
    py1 = block_start_y
    px2 = px1 + panel_w
    py2 = py1 + panel_h

    # رسم البرواز الشفاف والمفرغ تماماً
    draw.rectangle([px1, py1, px2, py2], fill=None, outline=quran_brown, width=2)
    pad = 5
    draw.rectangle([px1 + pad, py1 + pad, px2 - pad, py2 - pad], fill=None, outline=quran_brown, width=1)
    
    # الزخارف الجانبية للبرواز
    draw.line([(px1 - 15, py1 + panel_h//2), (px1, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px1 - 15, py1 + panel_h//2), (px1, py2 - 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + panel_h//2), (px2, py1 + 15)], fill=quran_brown, width=2)
    draw.line([(px2 + 15, py1 + panel_h//2), (px2, py2 - 15)], fill=quran_brown, width=2)

    # اسم السورة داخل البرواز
    draw.text((width // 2, py1 + (panel_h // 2) - 2), ayah_data["surah"], font=font_surah, fill=quran_brown, anchor="mm")

    # 4. رسم أسطر الآية الكريمة (تبدأ مباشرة تحت البرواز بمسافة قريبة وموزونة)
    start_y = py2 + 45 
    for i, line in enumerate(lines):
        current_y = start_y + (i * line_spacing)
        draw.text((width // 2, current_y), line, font=font_ayah, fill=quran_brown, anchor="mm")

    # 5. رسم رقم الآية بالأسفل بشكل ملتحم وقريب من نهاية النص
    ref_y = start_y + total_lines_height + 25
    draw.text((width // 2, ref_y), ayah_data["ref"], font=font_ref, fill=(110, 95, 80, 255), anchor="mm")

    img_path = "/tmp/ayah_image.png"
    img.convert("RGB").save(img_path, "PNG", quality=95)
    return img_path
