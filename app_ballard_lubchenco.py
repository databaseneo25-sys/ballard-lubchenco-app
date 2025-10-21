# app_full_with_apgar_downes.py
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

st.set_page_config(page_title="Ballard + Lubchenco + Apgar + Downes", layout="centered")

# ---------------------------
# DATA LUBCHENCO (calibrated)
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43],
    "P10": [500,600,700,800,900,1050,1200,1350,1500,1700,1900,2100,2300,2500,2600,2650,2600,2700,2750,2800],
    "P25": [600,750,900,1050,1200,1350,1500,1650,1800,2000,2200,2350,2500,2600,2800,2900,3000,3100,3150,3200],
    "P50": [700,850,1000,1150,1300,1500,1650,1800,2000,2200,2400,2550,2700,2900,3100,3200,3300,3400,3450,3500],
    "P75": [800,950,1100,1300,1450,1650,1800,2000,2200,2400,2600,2750,3000,3200,3400,3500,3600,3700,3750,3800],
    "P90": [900,1050,1200,1400,1600,1800,1950,2150,2350,2550,2750,2950,3300,3500,3700,3800,3900,4000,4050,4100],
}
df_lub = pd.DataFrame(DATA)

# ---------------------------
# BALLARD TABLE (official conversion)
# ---------------------------
BALLARD_TABLE = {
    -10: 20, -5: 22, 0: 24, 5: 26, 10: 28,
    15: 30, 20: 32, 25: 34, 30: 36, 35: 38,
    40: 40, 45: 42, 50: 44
}

def score_to_ga(total_score):
    keys = sorted(BALLARD_TABLE.keys())
    if total_score <= keys[0]:
        return BALLARD_TABLE[keys[0]]
    if total_score >= keys[-1]:
        return BALLARD_TABLE[keys[-1]]
    for i in range(len(keys) - 1):
        low, high = keys[i], keys[i + 1]
        if low <= total_score <= high:
            ga_low, ga_high = BALLARD_TABLE[low], BALLARD_TABLE[high]
            ga = ga_low + (ga_high - ga_low) * ((total_score - low) / (high - low))
            return round(ga, 1)
    return None

# ---------------------------
# Ballard items
# ---------------------------
BALLARD_ITEMS = [
    ("Sikap tubuh (Postur)", 0, 5),
    ("Persegi jendela (Square window)", 0, 5),
    ("Recoil lengan (Arm recoil)", 0, 5),
    ("Sudut popliteal (Popliteal angle)", 0, 5),
    ("Scarf sign", 0, 5),
    ("Heel to ear", 0, 5),
    ("Kulit (Skin)", 0, 5),
    ("Lanugo", 0, 5),
    ("Plantar (Permukaan plantar)", 0, 5),
    ("Payudara (Breast)", 0, 5),
    ("Mata & telinga (Eye & Ear)", 0, 5),
    ("Genitalia (Genital)", 0, 5),
]

# ---------------------------
# Classification KMK/SMK/BMK
# ---------------------------
def classify_kategori(ga_weeks, berat_g):
    idx = (df_lub['GA_weeks'] - ga_weeks).abs().argsort()[:1][0]
    row = df_lub.iloc[idx]
    ga_used = int(row['GA_weeks'])
    p10, p25, p50, p75, p90 = row['P10'], row['P25'], row['P50'], row['P75'], row['P90']
    if berat_g < p10:
        kategori = "KMK (Kecil untuk Masa Kehamilan)"
    elif berat_g > p90:
        kategori = "BMK (Besar untuk Masa Kehamilan)"
    else:
        kategori = "SMK (Sesuai Masa Kehamilan)"
    return kategori, ga_used, row

# ---------------------------
# Downes score helpers
# Downes: 5 items (0-2 each): resp rate/nares retraction/grunt/cyanosis/air entry
# We'll label components and provide interpretation.
# ---------------------------
DOWNES_ITEMS = [
    ("Frekuensi napas / inspirasi (Respiratory rate / distress)", 0, 2),
    ("Cyanosis (warna kulit/mukosa)", 0, 2),
    ("Retraksi (subcostal/intercostal)", 0, 2),
    ("Grunting (ekspirasi berbunyi)", 0, 2),
    ("Air entry (keterisian napas)", 0, 2)
]

def downes_total(scores_dict):
    return sum(scores_dict.values())

def downes_interpret(total):
    if total <= 3:
        return "Ringan"
    elif 4 <= total <= 6:
        return "Sedang"
    else:
        return "Berat / Risiko gagal nafas"

# ---------------------------
# PDF util
# ---------------------------
def create_pdf(report_data: dict, fig):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LAPORAN: Ballard + Lubchenco + Apgar + Downes")

    c.setFont("Helvetica", 10)
    y = height - 80
    for k, v in report_data.items():
        # wrap if long
        lines = str(v).split("\n")
        c.drawString(50, y, f"{k}: {lines[0]}")
        y -= 12
        for extra in lines[1:]:
            c.drawString(60, y, extra)
            y -= 12
        if y < 130:
            c.showPage()
            y = height - 50

    # save figure image
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150)
    img_buf.seek(0)
    image = ImageReader(img_buf)
    c.drawImage(image, 40, 80, width=520, preserveAspectRatio=True, mask='auto')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()

# ---------------------------
# History functions
# ---------------------------
HISTORY_FILE = "history_full_app.csv"

def save_history(record: dict):
    df = pd.DataFrame([record])
    header = not os.path.exists(HISTORY_FILE)
    df.to_csv(HISTORY_FILE, mode='a', index=False, header=header, encoding='utf-8')

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

# ---------------------------
# UI
# ---------------------------
st.title("🍼 Aplikasi Lengkap: Ballard + Lubchenco + Apgar + Downes")
st.caption("Isi komponen Ballard, Apgar, Downes — aplikasi akan menghitung usia (Ballard tabel), klasifikasi KMK/SMK/BMK, dan membuat laporan.")

with st.expander("ℹ️ Petunjuk singkat"):
    st.write("""
    - Isi semua komponen Ballard (0–5). Total dipetakan ke usia kehamilan berdasarkan tabel Ballard resmi.
    - Isi Apgar 1' dan 5' (0–10). Catatan: Apgar 5' < 7 → observasi lebih ketat.
    - Isi skor Downes (setiap komponen 0–2). Total 0–10 → interpretasi ringan/sedang/berat.
    """)

# Ballard inputs
st.subheader("1) Komponen Ballard (12 items)")
cols = st.columns(3)
ballard_scores = {}
for i, (label, lo, hi) in enumerate(BALLARD_ITEMS):
    with cols[i % 3]:
        ballard_scores[label] = st.number_input(label, min_value=lo, max_value=hi, value=2, step=1, key=f"ballard_{i}")

total_ballard = sum(ballard_scores.values())
ga_ballard = score_to_ga(total_ballard)

st.markdown(f"**Total Skor Ballard:** {total_ballard} / {sum([hi for _,_,hi in BALLARD_ITEMS])}")
st.markdown(f"**Usia Gestasi (Ballard table):** **{ga_ballard} minggu**")

# Apgar inputs
st.subheader("2) Apgar Score")
col1, col2 = st.columns(2)
with col1:
    apgar1 = st.number_input("Apgar 1 menit (0-10)", min_value=0, max_value=10, value=7, step=1)
with col2:
    apgar5 = st.number_input("Apgar 5 menit (0-10)", min_value=0, max_value=10, value=9, step=1)

# Downes inputs
st.subheader("3) Downes Score (respiratory assessment)")
downes_cols = st.columns(3)
downes_scores = {}
for i, (label, lo, hi) in enumerate(DOWNES_ITEMS):
    with downes_cols[i % 3]:
        downes_scores[label] = st.number_input(label + " (0-2)", min_value=lo, max_value=hi, value=0, step=1, key=f"downes_{i}")

downes_total_score = downes_total(downes_scores)
downes_note = downes_interpret(downes_total_score)
st.markdown(f"**Total Downes score:** {downes_total_score} → **{downes_note}**")

# Berat & optional manual GA
st.subheader("4) Berat Lahir & Pilihan Usia")
col_a, col_b = st.columns(2)
with col_a:
    berat = st.number_input("Berat lahir (gram)", min_value=400, max_value=4600, value=3000, step=50)
with col_b:
    ga_manual = st.checkbox("Override usia gestasi manual (opsional)", False)
    if ga_manual:
        ga_input = st.number_input("Masukkan usia gestasi manual (minggu)", min_value=24.0, max_value=43.0, value=ga_ballard, step=0.1)

ga_use = ga_input if ga_manual else ga_ballard

# Analyze
if st.button("🔍 Hitung & Tampilkan Hasil"):
    kategori, ga_used, pers_row = classify_kategori(ga_use, berat)

    st.success(f"Usia gestasi yang digunakan: **{ga_used} minggu**")
    st.metric("Kategori (Lubchenco)", kategori)

    st.subheader("Nilai Persentil (usia yang digunakan)")
    st.table(pers_row[['P10', 'P25', 'P50', 'P75', 'P90']].to_frame().T)

    # Interpretasi Apgar
    st.subheader("Interpretasi Apgar")
    st.write(f"Apgar 1 menit: **{apgar1}** — {'Beresiko, perhatikan' if apgar1 < 7 else 'Normal / memerlukan observasi'}")
    st.write(f"Apgar 5 menit: **{apgar5}** — {'Butuh intervensi / observasi lanjutan' if apgar5 < 7 else 'Normal'}")

    # Downes
    st.subheader("Interpretasi Downes")
    st.write(f"Total Downes: **{downes_total_score}** → **{downes_note}**")

    # Plot Lubchenco
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor("#f9f9f9")
    ax.set_xlim(24, 43)
    ax.set_ylim(400, 4600)
    ax.set_xticks(range(24,44))
    ax.set_yticks(range(400,4601,500))
    ax.grid(which='both', linestyle='--', alpha=0.5)

    ax.plot(df_lub['GA_weeks'], df_lub['P10'], '--', color="red", label="P10")
    ax.plot(df_lub['GA_weeks'], df_lub['P25'], '-', color="orange", label="P25")
    ax.plot(df_lub['GA_weeks'], df_lub['P50'], '-', color="blue", label="P50")
    ax.plot(df_lub['GA_weeks'], df_lub['P75'], '-', color="green", label="P75")
    ax.plot(df_lub['GA_weeks'], df_lub['P90'], '--', color="purple", label="P90")

    ax.scatter([ga_used], [berat], s=160, color="black", edgecolors="white", zorder=6, label="Bayi")

    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat Badan (gram)")
    ax.set_title("Kurva Lubchenco — Berat Lahir menurut Usia Gestasi")
    ax.legend(loc="upper left")
    st.pyplot(fig)

    # Save history
    record = {
        "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "total_ballard": total_ballard,
        "ga_ballard": ga_ballard,
        "ga_used": ga_used,
        "berat_g": berat,
        "kategori": kategori,
        "apgar1": apgar1,
        "apgar5": apgar5,
        "downes_total": downes_total_score,
        "downes_note": downes_note
    }
    try:
        save_history(record)
        st.info("Hasil tersimpan ke history lokal.")
    except Exception as e:
        st.warning(f"Gagal menyimpan history: {e}")

    # PDF
    report = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Total Skor Ballard": total_ballard,
        "Usia Estimasi (Ballard)": ga_ballard,
        "Usia Digunakan": ga_used,
        "Berat lahr (g)": berat,
        "Kategori (KMK/SMK/BMK)": kategori,
        "Apgar 1'": apgar1,
        "Apgar 5'": apgar5,
        "Downes total": f"{downes_total_score} ({downes_note})"
    }
    pdf_bytes = create_pdf(report, fig)
    st.download_button("⬇ Unduh Laporan PDF", data=pdf_bytes, file_name=f"laporan_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

# ---------------------------
# History section + delete button
# ---------------------------
st.markdown("---")
st.subheader("Riwayat Analisis (lokal)")
hist = load_history()
if hist.empty:
    st.info("Belum ada riwayat tersimpan.")
else:
    st.dataframe(hist.sort_values(by='timestamp', ascending=False))
    st.download_button("⬇ Unduh CSV Riwayat", data=hist.to_csv(index=False).encode('utf-8'), file_name="riwayat_full_app.csv", mime="text/csv")
    if st.button("🗑 Hapus Semua Riwayat"):
        try:
            os.remove(HISTORY_FILE)
            st.success("Riwayat berhasil dihapus.")
        except Exception as e:
            st.error(f"Gagal menghapus riwayat: {e}")
