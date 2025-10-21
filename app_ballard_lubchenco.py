import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Aman untuk Streamlit Cloud
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Judul
st.title("Grafik Lubchenco – Berat Badan Bayi Berdasarkan Usia Kehamilan")

# --- Data Lubchenco (berat janin vs usia kehamilan) ---
data = {
    "Usia (minggu)": list(range(24, 44)),
    "P10":  [500, 600, 700, 800, 950, 1100, 1250, 1400, 1550, 1700, 1900, 2100, 2300, 2500, 2650, 2750, 2850, 2950, 3000, 3050],
    "P25":  [550, 700, 850, 1000, 1150, 1300, 1500, 1650, 1850, 2050, 2250, 2450, 2650, 2850, 3000, 3150, 3250, 3350, 3400, 3450],
    "P50":  [600, 800, 950, 1100, 1300, 1500, 1700, 1900, 2100, 2300, 2550, 2750, 2950, 3150, 3300, 3450, 3550, 3650, 3700, 3750],
    "P75":  [700, 900, 1100, 1250, 1450, 1650, 1850, 2050, 2300, 2550, 2750, 2950, 3150, 3350, 3550, 3700, 3800, 3900, 3950, 4000],
    "P90":  [800, 1000, 1200, 1350, 1550, 1750, 1950, 2150, 2400, 2650, 2850, 3050, 3250, 3450, 3650, 3800, 3950, 4050, 4100, 4200],
}
df = pd.DataFrame(data)

# --- Input data pengguna ---
st.sidebar.header("Input Data Bayi")
usia = st.sidebar.number_input("Usia kehamilan (minggu)", min_value=24, max_value=43, value=40)
berat = st.sidebar.number_input("Berat bayi (gram)", min_value=400, max_value=4600, value=2600)

# --- Tentukan kategori ---
def tentukan_persentil(usia, berat):
    row = df[df["Usia (minggu)"] == usia]
    if row.empty:
        return "Data usia tidak tersedia"
    row = row.iloc[0]
    if berat < row["P10"]:
        return "<10 (Small for Gestational Age)"
    elif berat < row["P25"]:
        return "10–25"
    elif berat < row["P50"]:
        return "25–50"
    elif berat < row["P75"]:
        return "50–75"
    elif berat < row["P90"]:
        return "75–90"
    else:
        return ">90 (Large for Gestational Age)"

kategori = tentukan_persentil(usia, berat)

# --- Gambar grafik ---
fig, ax = plt.subplots(figsize=(7, 6))
plt.grid(True, linestyle="--", alpha=0.5)

# Warna tiap persentil
colors = {
    "P10": "red",
    "P25": "orange",
    "P50": "green",
    "P75": "blue",
    "P90": "purple"
}

for p, color in colors.items():
    ax.plot(df["Usia (minggu)"], df[p], label=f"{p}", color=color, linewidth=2)

# Plot titik bayi
ax.scatter(usia, berat, color="black", s=80, label="Bayi Anda")

ax.set_title("Grafik Berat Badan Bayi (Lubchenco)")
ax.set_xlabel("Usia Kehamilan (minggu)")
ax.set_ylabel("Berat (gram)")
ax.legend()
ax.set_xlim(24, 43)
ax.set_ylim(400, 4600)

# --- Tampilkan hasil ---
st.pyplot(fig)
st.success(f"📊 Hasil: Bayi usia {usia} minggu dengan berat {berat} g berada pada persentil **{kategori}**")

# --- Fungsi membuat PDF ---
def create_pdf(report_data, fig):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Simpan grafik ke buffer
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150)
    img_buf.seek(0)

    image = ImageReader(img_buf)

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, 800, "Laporan Grafik Lubchenco")

    c.setFont("Helvetica", 11)
    c.drawString(50, 770, f"Tanggal Cetak: {datetime.now().strftime('%d-%m-%Y %H:%M')}")

    # Data hasil input
    y_pos = 730
    for key, value in report_data.items():
        c.drawString(50, y_pos, f"{key}: {value}")
        y_pos -= 20

    # Tambahkan gambar grafik ke PDF
    c.drawImage(image, 40, 100, width=500, preserveAspectRatio=True, mask='auto')

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- Tombol unduh PDF ---
report_data = {
    "Usia kehamilan (minggu)": usia,
    "Berat badan (gram)": berat,
    "Persentil Lubchenco": kategori,
}

if st.button("📄 Unduh PDF Hasil"):
    pdf_bytes = create_pdf(report_data, fig)
    st.download_button(
        label="Klik untuk download laporan",
        data=pdf_bytes,
        file_name="Laporan_Lubchenco.pdf",
        mime="application/pdf"
    )
