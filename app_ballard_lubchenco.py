# app_ballard_full_v5.py
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

st.set_page_config(page_title="Ballard+Lubchenco+APGAR+Downes (Final)", layout="centered")

# ---------------------------
# Lubchenco (kalibrasi final — pastikan P10 sekitar 2600 di 40 wk)
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
# BALLARD SCORE TABLE (resmi)
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
# BALLARD ITEMS (12 komponen)
# ---------------------------
BALLARD_ITEMS = [
    ("1. Sikap tubuh (Postur)", 0, 4),
    ("2. Persegi jendela (pergelangan tangan)", 0, 4),
    ("3. Rekoli lengan (Arm recoil)", 0, 4),
    ("4. Sudut popliteal", 0, 5),
    ("5. Tanda selendang (Scarf sign)", 0, 4),
    ("6. Tumit ke telinga (Heel to ear)", 0, 4),
    ("7. Kulit", 0, 5),
    ("8. Lanugo", 0, 4),
    ("9. Permukaan plantar (Plantar surface)", 0, 4),
    ("10. Payudara", 0, 4),
    ("11. Mata & telinga", 0, 4),
    ("12. Genitalia (L/P)", 0, 4),
]

# ---------------------------
# KLASIFIKASI KMK/SMK/BMK
# ---------------------------
def classify_kmk_smk_bmk(ga_weeks, berat):
    row = df_lub.iloc[(df_lub['GA_weeks'] - ga_weeks).abs().argsort()[:1]].iloc[0]
    ga_used = row['GA_weeks']
    if berat < row['P10']:
        kategori = "KMK (Kecil Masa Kehamilan)"
    elif berat > row['P90']:
        kategori = "BMK (Besar Masa Kehamilan)"
    else:
        kategori = "SMK (Sesuai Masa Kehamilan)"
    return kategori, int(ga_used), row
# ---------------------------
# APGAR components (5 items each minute)
# Each item 0..2
# ---------------------------
APGAR_COMPONENTS = [
    ("Appearance (Warna kulit)", 0, 2),
    ("Pulse (Denyut jantung)", 0, 2),
    ("Grimace (Refleks / respons)", 0, 2),
    ("Activity (Tonus otot)", 0, 2),
    ("Respiration (Pernapasan)", 0, 2),
]

# ---------------------------
# Downes score components (5 items, 0..2)
# ---------------------------
DOWNES_ITEMS = [
    ("Frekuensi napas / distress", 0, 2),
    ("Cyanosis", 0, 2),
    ("Retraksi", 0, 2),
    ("Grunting", 0, 2),
    ("Air entry", 0, 2),
]

def downes_interpret(total):
    if total <= 3:
        return "Ringan"
    elif 4 <= total <= 6:
        return "Sedang"
    else:
        return "Berat / Risiko gagal napas"

# ---------------------------
# Klasifikasi KMK / SMK / BMK
# ---------------------------
def classify_kategori(ga_weeks, berat_g):
    idx = (df_lub['GA_weeks'] - ga_weeks).abs().argsort()[:1][0]
    row = df_lub.iloc[idx]
    ga_used = int(row['GA_weeks'])
    p10, p90 = row['P10'], row['P90']
    if berat_g < p10:
        kategori = "KMK (Kecil untuk Masa Kehamilan)"
    elif berat_g > p90:
        kategori = "BMK (Besar untuk Masa Kehamilan)"
    else:
        kategori = "SMK (Sesuai Masa Kehamilan)"
    return kategori, ga_used, row

# ---------------------------
# PDF util (ImageReader safe)
# ---------------------------
def create_pdf(report_data: dict, fig):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LAPORAN: Ballard + Lubchenco + APGAR + Downes")

    c.setFont("Helvetica", 10)
    y = height - 80
    for k, v in report_data.items():
        text = f"{k}: {v}"
        c.drawString(50, y, text)
        y -= 12
        if y < 140:
            c.showPage()
            y = height - 50

    # embed figure
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
# History file
# ---------------------------
HISTORY_FILE = "history_ballard_full_v5.csv"

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
st.title("🍼 Aplikasi Lengkap: Ballard + Lubchenco + APGAR + Downes (Final)")
st.caption("Isi Ballard (12 item), APGAR 1',5',10', Downes — dapatkan usia (Ballard tabel), klasifikasi KMK/SMK/BMK, grafik & laporan PDF.")

with st.expander("📖 Petunjuk singkat"):
    st.write("""
    - Isi komponen Ballard (0–5) → total akan dipetakan ke usia kehamilan berdasarkan tabel Ballard resmi (interpolasi).
    - Isi APGAR lengkap di menit 1, 5, dan 10 (masing-masing 5 komponen 0–2).
    - Isi skor Downes (5 komponen, 0–2).
    - Masukkan berat lahir, klik 'Hitung' → tampil grafik, klasifikasi, interpretasi, dan PDF.
    """)

# --- Ballard inputs ---
st.subheader("1) Komponen Ballard (12 items)")
cols = st.columns(3)
ballard_scores = {}
for i, (label, lo, hi) in enumerate(BALLARD_ITEMS):
    with cols[i % 3]:
        ballard_scores[label] = st.number_input(label, min_value=lo, max_value=hi, value=2, step=1, key=f"ballard_{i}")

total_ballard = sum(ballard_scores.values())
ga_ballard = score_to_ga(total_ballard)
st.markdown(f"**Total Skor Ballard:** {total_ballard} / {MAX_BALLARD}")
st.markdown(f"**Estimasi Usia (Ballard tabel):** **{ga_ballard} minggu**")

# --- APGAR inputs (1', 5', 10') ---
st.subheader("2) APGAR Score (lengkap: menit 1, 5, 10)")
apgar = {"1'":{}, "5'":{}, "10'":{}}
for minute in ["1'", "5'", "10'"]:
    st.markdown(f"**Apgar menit {minute}**")
    cols = st.columns(3)
    for i, (label, lo, hi) in enumerate(APGAR_COMPONENTS):
        key = f"apgar_{minute}_{i}"
        with cols[i % 3]:
            apgar[minute][label] = st.number_input(f"{label} ({minute})", min_value=lo, max_value=hi, value=2 if minute!="1'" else 1, step=1, key=key)
    total = sum(apgar[minute].values())
    st.write(f"Total Apgar {minute}: **{total}** — ", end="")
    if total <= 3:
        st.write("Severely depressed (0–3)")
    elif 4 <= total <= 6:
        st.write("Moderately depressed (4–6)")
    else:
        st.write("Excellent (7–10)")

# --- Downes inputs ---
st.subheader("3) Downes score (respiratory assessment)")
downes_cols = st.columns(3)
downes_scores = {}
for i, (label, lo, hi) in enumerate(DOWNES_ITEMS):
    with downes_cols[i % 3]:
        downes_scores[label] = st.number_input(label + " (0-2)", min_value=lo, max_value=hi, value=0, step=1, key=f"downes_{i}")
downes_total_score = sum(downes_scores.values())
downes_level = downes_interpret(downes_total_score)
st.markdown(f"**Total Downes**: {downes_total_score} → **{downes_level}**")

# --- Berat & optional manual GA override ---
st.subheader("4) Berat lahir & pengaturan usia")
col_a, col_b = st.columns(2)
with col_a:
    berat = st.number_input("Masukkan berat lahir (gram)", min_value=400, max_value=4600, value=3000, step=50)
with col_b:
    ga_manual = st.checkbox("Override usia gestasi manual (opsional)")
    if ga_manual:
        ga_input = st.number_input("Masukkan usia gestasi manual (minggu)", min_value=24.0, max_value=43.0, value=float(ga_ballard), step=0.1)

ga_used_for_analysis = ga_input if ga_manual else ga_ballard

# --- Analyze button ---
if st.button("🔍 Hitung & Tampilkan Hasil"):
    kategori, ga_used_round, pers_row = classify_kategori(ga_used_for_analysis, berat)
    st.success(f"Usia gestasi yang digunakan: **{ga_used_round} minggu**")
    st.metric("Kategori (Lubchenco)", kategori)

    st.subheader("Nilai Persentil (usia yang digunakan)")
    st.table(pers_row[['P10','P25','P50','P75','P90']].to_frame().T)

    # Apgar summary
    st.subheader("Ringkasan APGAR")
    for minute in ["1'", "5'", "10'"]:
        total = sum(apgar[minute].values())
        label = ("Severely depressed" if total<=3 else ("Moderately depressed" if 4<=total<=6 else "Excellent (7-10)"))
        st.write(f"Apgar {minute}: {total} — {label}")

    # Downes summary
    st.subheader("Ringkasan Downes")
    st.write(f"Total Downes: **{downes_total_score}** → **{downes_level}**")

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

    ax.scatter([ga_used_round], [berat], s=160, color="black", edgecolors="white", zorder=6, label="Bayi")
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
        "ga_used": ga_used_round,
        "berat_g": berat,
        "kategori": kategori,
        "apgar1_total": sum(apgar["1'"].values()),
        "apgar5_total": sum(apgar["5'"].values()),
        "apgar10_total": sum(apgar["10'"].values()),
        "downes_total": downes_total_score,
        "downes_level": downes_level
    }
    try:
        save_history(record)
        st.info("Hasil tersimpan ke history lokal.")
    except Exception as e:
        st.warning(f"Gagal menyimpan history: {e}")

    # Create PDF
    report = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Total Skor Ballard": total_ballard,
        "Usia Estimasi (Ballard)": ga_ballard,
        "Usia Digunakan (analisis)": ga_used_round,
        "Berat lahir (g)": berat,
        "Kategori (KMK/SMK/BMK)": kategori,
        "APGAR 1'": sum(apgar["1'"].values()),
        "APGAR 5'": sum(apgar["5'"].values()),
        "APGAR 10'": sum(apgar["10'"].values()),
        "Downes total": f"{downes_total_score} ({downes_level})"
    }
    pdf_bytes = create_pdf(report, fig)
    st.download_button("⬇ Unduh Laporan PDF", data=pdf_bytes, file_name=f"laporan_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

# ---------------------------
# History + delete
# ---------------------------
st.markdown("---")
st.subheader("Riwayat Analisis (lokal)")
hist = load_history()
if hist.empty:
    st.info("Belum ada riwayat tersimpan.")
else:
    st.dataframe(hist.sort_values(by='timestamp', ascending=False))
    st.download_button("⬇ Unduh CSV Riwayat", data=hist.to_csv(index=False).encode('utf-8'), file_name="riwayat_ballard_full_v5.csv", mime="text/csv")
    if st.button("🗑 Hapus Semua Riwayat"):
        try:
            os.remove(HISTORY_FILE)
            st.success("Riwayat berhasil dihapus.")
        except Exception as e:
            st.error(f"Gagal menghapus riwayat: {e}")
