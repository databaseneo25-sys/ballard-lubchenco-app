from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("images", exist_ok=True)

# ukuran gambar
W, H = 400, 300

def create_image(filename, title, desc, score):
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = None
        font_text = None

    draw.text((10, 10), title, fill="black", font=font_title)
    draw.text((10, 80), desc, fill="black", font=font_text)
    draw.text((10, 250), f"Score: {score}", fill="red", font=font_text)

    img.save(f"images/{filename}")

# =========================
# DATA BALLARD
# =========================

items = {
    "posture": [
        "Ekstensi penuh",
        "Sedikit fleksi",
        "Fleksi sedang",
        "Fleksi baik",
        "Fleksi kuat"
    ],
    "square": [
        ">90°",
        "90°",
        "60°",
        "45°",
        "30°"
    ],
    "arm": [
        "Tidak ada recoil",
        "Lambat",
        "Sedang",
        "Cepat",
        "Sangat kuat"
    ],
    "popliteal": [
        ">160°",
        "140°",
        "120°",
        "100°",
        "80°",
        "<60°"
    ],
    "scarf": [
        "Lewat garis tengah",
        "Mendekati",
        "Di tengah",
        "Tidak sampai",
        "Sangat kaku"
    ],
    "heel": [
        "Sangat mudah",
        "Mudah",
        "Sedikit tahanan",
        "Tahanan",
        "Tidak bisa"
    ],
    "skin": [
        "Transparan",
        "Tipis",
        "Halus",
        "Mengelupas",
        "Keriput",
        "Retak"
    ],
    "lanugo": [
        "Tidak ada",
        "Sedikit",
        "Sedang",
        "Banyak",
        "Menipis"
    ],
    "plantar": [
        "Tidak ada garis",
        "Anterior",
        "1/3",
        "2/3",
        "Seluruh"
    ],
    "breast": [
        "Tidak ada",
        "Kecil",
        "Areola datar",
        "Menonjol",
        "Jelas"
    ],
    "ear": [
        "Lunak",
        "Lambat balik",
        "Sedikit kartilago",
        "Baik",
        "Kaku"
    ],
    "genital": [
        "Imatur",
        "Sedikit berkembang",
        "Sedang",
        "Baik",
        "Matang"
    ]
}

# =========================
# GENERATE SEMUA GAMBAR
# =========================

for item, options in items.items():
    for i, desc in enumerate(options):
        filename = f"{item}_{i}.png"
        create_image(filename, item.upper(), desc, i)

print("✅ Semua gambar Ballard berhasil dibuat di folder 'images'")
