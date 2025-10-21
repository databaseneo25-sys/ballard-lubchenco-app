# app_ballard_lubchenco_full.py
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # safe backend for server / Streamlit Cloud
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

st.set_page_config(page_title="Ballard + Lubchenco (Final - Ballard form)", layout="centered")

# ---------------------------
# DATA LUBCHENCO (DICALIBRASI)
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43],
    "P10": [500,600,700,800,900,1050,1200,1350,1500,1700,1900,2100,2300,2450,2550,2600,2600,2650,2700,2750],
    "P25": [600,700,850,950,1100,1250,1400,1600,1800,2000,2200,2400,2600,2750,2900,3000,3100,3150,3200,3250],
    "P50": [700,800,950,1100,1250,1400,1600,1800,2000,2200,2450,2700,2950,3100,3250,3400,3400,3450,3500,3550],
    "P75": [800,900,1050,1200,1350,1500,1700,1900,2100,2350,2600,2850,3100,3300,3550,3700,3900,3950,4000,4050],
    "P90": [900,1000,1150,1300,1500,1650,1850,2100,2350,2600,2850,3100,3350,3600,3850,4000,4300,4350,4400,4450]
}
df_lub = pd.DataFrame(DATA)

# ---------------------------
# HISTORY FILE
# ---------------------------
HISTORY_FILE = "history_ballard_lubchenco_full.csv"

def save_history(record: dict):
    df = pd.DataFrame([record])
    header = not os.path.exists(HISTORY_FILE)
    df.to_csv(HISTORY_FILE, mode='a', index=False, header=header, encoding='utf-8')

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

# ---------------------------
# Ballard components (New Ballard) - 12 items
# Each item: 0..5 score -> total max = 60
# Conversion: map 0..max_score -> 24..44 minggu (linear)
# ---------------------------
BALLARD_ITEMS = [
    ("Kulit (Skin)", 0, 5),
    ("Lanugo", 0, 5),
    ("Plantar (permukaan plantar)", 0, 5),
    ("Payudara (Breast)", 0, 5),
    ("Mata & Telinga (Eye & Ear)", 0, 5),
    ("Genitalia (Male/Female)", 0, 5),
    ("Postur (Posture)", 0, 5),
    ("Square window", 0, 5),
    ("Arm recoil", 0, 5),
    ("Popliteal angle", 0, 5),
    ("Scarf sign", 0, 5),
    ("Heel to ear", 0, 5),
]
MAX_BALLARD_SCORE = sum([item[2] for item in BALLARD_ITEMS])  # expected 60

def score_to_ga(total_score):
    """Map total Ballard score (0..MAX) to gestational age in weeks (24..44) linear."""
    ga = 24 + (total_score / MAX_BALLARD_SCORE) * 20.0
    return round(ga, 1)

# ---------------------------
# Lubchenco classification -> KMK / SMK / BMK
# ---------------------------
def classify_kategori(ga_weeks, berat_g):
    # pick nearest GA week available
    ga_near_idx = (df_lub['GA_weeks'] - ga_weeks).abs().argsort()[:1][0]
    row = df_lub.iloc[ga_near_idx]
    ga_used = int(row['GA_weeks'])
    p10, p25, p50, p75, p90 = row['P10'], row['P25'], row['P50'], row['P75'], row['P90']
    if berat_g < p10:
        kategori = "KMK (Kecil untuk Masa Kehamilan)"
    elif berat_g > p90:
        kategori = "BMK (Besar untuk Masa Kehamilan)"
    else:
        kategori = "SMK (Sedang untuk Masa Kehamilan)"
    return kategori, ga_used, row

# ---------------------------
# PDF report util (fixed ImageReader)
# ---------------------------
def create_pdf(report_data: dict, fig):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LAPORAN: Ballard + Lubchenco")

    # Metadata / results
    c.setFont("Helvetica", 10)
    y = height - 80
    for k, v in report_data.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 14
        if y < 120:
            c.showPage()
            y = height - 50

    # Draw figure
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150)
    img_buf.seek(0)
    image = ImageReader(img_buf)
    # place image
    c.drawImage(image, 40, 80, width=520, preserveAspectRatio=True, mask='auto')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.title("🍼 Aplikasi Ballard + Kurva Lubchenco (Final)")
st.markdown("Isi komponen Ballard (New Ballard) — hasil akan otomatis jadi skor, dikonversi ke usia gestasi, diplot ke kurva Lubchenco, dan ditentukan kategori KMK/SMK/BMK.")

with st.expander("ℹ️ Petunjuk singkat"):
    st.write("""
    - Isi tiap komponen Ballard (skor 0–5). Aplikasi menggunakan total max 60 → usia gestasi dipetakan ke 24–44 minggu.
    - Hanya input skor dan berat bayi diperlukan. Hasil = usia estimasi (Ballard), kategori KMK/SMK/BMK, grafik & PDF.
    """)

# Ballard form
st.subheader("1) Isi Komponen Ballard")
cols = st.columns(3)
ballard_values = {}
i = 0
for label, lo, hi in BALLARD_ITEMS:
    col = cols[i % 3]
    with col:
        ballard_values[label] = st.number_input(label, min_value=lo, max_value=hi, value=2, step=1, key=f"b_{i}")
    i += 1

total_ballard = sum(ballard_values.values())
ga_from_ballard = score_to_ga(total_ballard)

st.markdown(f"**Total Skor Ballard:** {total_ballard} / {MAX_BALLARD_SCORE}")
st.markdown(f"**Estimasi Usia Gestasi (Ballard):** **{ga_from_ballard} minggu**")

# Berat input
st.subheader("2) Input Berat Lahir")
col_a, col_b = st.columns(2)
with col_a:
    berat = st.number_input("Berat lahir (gram)", min_value=400, max_value=4600, value=3000, step=50)
with col_b:
    # also allow manual override of GA (optional)
    ga_manual = st.checkbox("Override usia gestasi manual (opsional)", value=False)
    if ga_manual:
        ga_input = st.number_input("Masukkan usia gestasi manual (minggu)", min_value=24.0, max_value=43.0, value=ga_from_ballard, step=0.1)

if ga_manual:
    ga_use = ga_input
else:
    ga_use = ga_from_ballard

# Analyze button
if st.button("🔍 Hitung & Tampilkan Hasil"):
    kategori, ga_used, pers_row = classify_kategori(ga_use, berat)

    st.success(f"Usia gestasi yang digunakan: **{ga_used} minggu**")
    st.metric("Kategori menurut Lubchenco", kategori)

    st.subheader("Nilai Persentil (usia yang digunakan)")
    st.table(pers_row[['P10','P25','P50','P75','P90']].to_frame().T)

    # Plot
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor("#f9f9f9")
    ax.set_xlim(24, 43)
    ax.set_ylim(400, 4600)
    # grid lines tiap 1 minggu / 500 gram
    ax.set_xticks(range(24,44,1))
    ax.set_yticks(range(400,4601,500))
    ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.6)

    # color lines
    ax.plot(df_lub['GA_weeks'], df_lub['P10'], '--', color="#e74c3c", linewidth=2.2, label="P10 (Merah)")
    ax.plot(df_lub['GA_weeks'], df_lub['P25'], '-', color="#f39c12", linewidth=2.2, label="P25 (Oranye)")
    ax.plot(df_lub['GA_weeks'], df_lub['P50'], '-', color="#3498db", linewidth=2.5, label="P50 (Biru)")
    ax.plot(df_lub['GA_weeks'], df_lub['P75'], '-', color="#27ae60", linewidth=2.2, label="P75 (Hijau)")
    ax.plot(df_lub['GA_weeks'], df_lub['P90'], '--', color="#8e44ad", linewidth=2.2, label="P90 (Ungu)")

    # plot baby
    ax.scatter([ga_used], [berat], s=160, color="black", edgecolors="white", zorder=6, label="Bayi")

    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat Badan (gram)")
    ax.set_title("Kurva Lubchenco — Berat Lahir menurut Usia Gestasi")
    ax.legend(loc="upper left", frameon=True)
    st.pyplot(fig)

    # Save history
    record = {
        "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "total_ballard": total_ballard,
        "ga_ballard": ga_from_ballard,
        "ga_used": ga_used,
        "berat_g": berat,
        "kategori": kategori
    }
    try:
        save_history(record)
        st.info("Hasil tersimpan ke history lokal.")
    except Exception as e:
        st.warning(f"Gagal menyimpan history: {e}")

    # PDF download
    report_data = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Total Skor Ballard": total_ballard,
        "Usia Estimasi (Ballard)": ga_from_ballard,
        "Usia Digunakan": ga_used,
        "Berat Lahir (g)": berat,
        "Kategori (KMK/SMK/BMK)": kategori
    }
    pdf_bytes = create_pdf(report_data, fig)
    st.download_button("⬇ Unduh Laporan PDF", data=pdf_bytes, file_name=f"laporan_ballard_lubchenco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

# ---------------------------
# HISTORY SECTION
# ---------------------------
st.markdown("---")
st.subheader("Riwayat Analisis (lokal)")
history_df = load_history()
if history_df.empty:
    st.info("Belum ada riwayat.")
else:
    st.dataframe(history_df.sort_values(by='timestamp', ascending=False))
    st.download_button("⬇ Unduh Semua Riwayat (CSV)", data=history_df.to_csv(index=False).encode('utf-8'), file_name="history_ballard_lubchenco.csv", mime="text/csv")
