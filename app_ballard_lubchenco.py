# app_ballard_final_layout_wide.py
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # safe backend for server/cloud
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

# Page config: wide layout
st.set_page_config(page_title="Ballard+Lubchenco+APGAR+Downes")

# ---------------------------
# Title (centered visually but layout wide)
# ---------------------------
st.markdown(
    """
    <div style="text-align:center;">
        <h1 style="margin-bottom:2px;">👶 Aplikasi Ballard + Kurva Lubchenco (KMK/SMK/BMK) Transisi RSUD dr Mohamad Soewandhie</h1>
        <div style="color: #555;">💌Persembahan khusus dari Kami sebagai bentuk komitmen dalam optimalisasi pelayanan perinatologi dan neonatal care dengan Menilai usia kehamilan dari skor Ballard, menentukan status pertumbuhan bayi berdasarkan kurva Lubchenco</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")  # spacing

# ---------------------------
# Lubchenco data (calibrated)
# X: 24-43 wk, Y: 400-4600 g
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
# Ballard conversion table (official)
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
    for i in range(len(keys)-1):
        low, high = keys[i], keys[i+1]
        if low <= total_score <= high:
            ga_low, ga_high = BALLARD_TABLE[low], BALLARD_TABLE[high]
            ga = ga_low + (ga_high - ga_low) * ((total_score - low) / (high - low))
            return round(ga, 1)
    return None

# ---------------------------
# Ballard components (12 items)
# ---------------------------
BALLARD_ITEMS = [
    ("Sikap tubuh (Postur)", 0, 5),
    ("Persegi jendela (Square window / pergelangan)", 0, 5),
    ("Recoil lengan (Arm recoil)", 0, 5),
    ("Sudut popliteal (Popliteal angle)", 0, 5),
    ("Tanda selendang (Scarf sign)", 0, 5),
    ("Tumit ke telinga (Heel to ear)", 0, 5),
    ("Kulit (Skin)", 0, 5),
    ("Lanugo", 0, 5),
    ("Permukaan plantar (Plantar)", 0, 5),
    ("Payudara (Breast)", 0, 5),
    ("Mata & telinga (Eye & Ear)", 0, 5),
    ("Genitalia (Genital)", 0, 5),
]
MAX_BALLARD = sum([hi for _,_,hi in BALLARD_ITEMS])

# ---------------------------
# APGAR components
# ---------------------------
APGAR_COMPONENTS = [
    ("Appearance (Warna kulit)", 0, 2),
    ("Pulse (Denyut jantung)", 0, 2),
    ("Grimace (Refleks / respons)", 0, 2),
    ("Activity (Tonus otot)", 0, 2),
    ("Respiration (Pernapasan)", 0, 2),
]

# ---------------------------
# Downes components
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
# History file
# ---------------------------
HISTORY_FILE = "history_ballard_final_wide.csv"
def save_history(record: dict):
    df = pd.DataFrame([record])
    header = not os.path.exists(HISTORY_FILE)
    df.to_csv(HISTORY_FILE, mode='a', index=False, header=header, encoding='utf-8')
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

# ---------------------------
# Helper: classify KMK/SMK/BMK
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
# PDF util (ImageReader)
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
        line = f"{k}: {v}"
        c.drawString(50, y, line)
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
# UI: layout wide with columns for neatness
# ---------------------------
st.markdown("---")
# APGAR block (top)
st.subheader("1) APGAR Score (menit 1, 5, 10)")
apgar = {"1'": {}, "5'": {}, "10'": {}}
for minute in ["1'", "5'", "10'"]:
    st.markdown(f"**APGAR menit {minute}**")
    # vertical layout (no columns) for clear stacking
    for label, lo, hi in APGAR_COMPONENTS:
        key = f"apgar_{minute}_{label}"
        apgar[minute][label] = st.number_input(f"{label} ({minute})", min_value=lo, max_value=hi, value=2 if minute!="1'" else 1, step=1, key=key)
    total_apgar = sum(apgar[minute].values())
    if total_apgar <= 3:
        status = "Severely depressed (0-3)"
    elif total_apgar <= 6:
        status = "Moderately depressed (4-6)"
    else:
        status = "Excellent (7-10)"
    st.info(f"Total APGAR {minute}: {total_apgar} → {status}")

st.markdown("---")
# Downes block
st.subheader("2) Downes Score (penilaian pernapasan)")
downes_scores = {}
for label, lo, hi in DOWNES_ITEMS:
    key = f"downes_{label}"
    downes_scores[label] = st.number_input(f"{label} (0-2)", min_value=lo, max_value=hi, value=0, step=1, key=key)
downes_total = sum(downes_scores.values())
downes_note = downes_interpret(downes_total)
st.info(f"Total Downes: {downes_total} → {downes_note}")

st.markdown("---")
# Ballard block
st.subheader("3) Ballard Score (12 komponen)")
ballard_scores = {}
cols = st.columns(3)
for i, (label, lo, hi) in enumerate(BALLARD_ITEMS):
    with cols[i % 3]:
        ballard_scores[label] = st.number_input(label, min_value=lo, max_value=hi, value=2, step=1, key=f"ballard_{i}")
total_ballard = sum(ballard_scores.values())
ga_ballard = score_to_ga(total_ballard)
st.write(f"**Total Skor Ballard:** {total_ballard} / {MAX_BALLARD}")
st.write(f"**Estimasi Usia dari Ballard (minggu):** {ga_ballard}")

# Weight and optional GA override
st.markdown("---")
st.subheader("4) Berat Lahir & Pengaturan Usia untuk Analisis")
col_a, col_b = st.columns([2,1])
with col_a:
    berat = st.number_input("Masukkan Berat Lahir (gram)", min_value=400, max_value=4600, value=3000, step=50)
with col_b:
    ga_manual = st.checkbox("Override usia gestasi manual (opsional)")
    if ga_manual:
        ga_input = st.number_input("Usia gestasi manual (minggu)", min_value=24.0, max_value=43.0, value=float(ga_ballard), step=0.1)

ga_used = ga_input if ga_manual else ga_ballard

# Analyze & show results
st.markdown("")
if st.button("🔍 Hitung & Tampilkan Hasil"):
    kategori, ga_used_round, pers_row = classify_kategori(ga_used, berat)
    st.success(f"Usia gestasi yang digunakan: **{ga_used_round} minggu**")
    st.metric("Kategori (Lubchenco)", kategori)

    st.subheader("Nilai Persentil (usia yang digunakan)")
    st.table(pers_row[['P10','P25','P50','P75','P90']].to_frame().T)

    # APGAR summary
    st.subheader("Ringkasan APGAR")
    for minute in ["1'", "5'", "10'"]:
        total = sum(apgar[minute].values())
        label = ("Severely depressed" if total<=3 else ("Moderately depressed" if 4<=total<=6 else "Excellent (7-10)"))
        st.write(f"Apgar {minute}: {total} — {label}")

    # Downes summary
    st.subheader("Ringkasan Downes")
    st.write(f"Total Downes: **{downes_total}** → **{downes_note}**")

    # Plot Lubchenco
    st.subheader("Grafik Lubchenco — Berat Lahir menurut Usia Gestasi")
    fig, ax = plt.subplots(figsize=(9,6))
    ax.set_facecolor("#f9f9f9")
    ax.set_xlim(24, 43)
    ax.set_ylim(400, 4600)
    ax.set_xticks(range(24,44))
    ax.set_yticks(range(400,4601,500))
    ax.grid(which='both', linestyle='--', alpha=0.5)

    ax.plot(df_lub['GA_weeks'], df_lub['P10'], '--', color="#e74c3c", linewidth=2, label="P10")
    ax.plot(df_lub['GA_weeks'], df_lub['P25'], '-', color="#f39c12", linewidth=2, label="P25")
    ax.plot(df_lub['GA_weeks'], df_lub['P50'], '-', color="#3498db", linewidth=2.5, label="P50")
    ax.plot(df_lub['GA_weeks'], df_lub['P75'], '-', color="#27ae60", linewidth=2, label="P75")
    ax.plot(df_lub['GA_weeks'], df_lub['P90'], '--', color="#8e44ad", linewidth=2, label="P90")

    ax.scatter([ga_used_round], [berat], s=160, color="black", edgecolors="white", zorder=6, label="Bayi")
    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat Badan (gram)")
    ax.legend(loc="upper left")
    st.pyplot(fig)

    # Save history record
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
        "downes_total": downes_total,
        "downes_note": downes_note
    }
    try:
        save_history(record)
        st.info("Hasil tersimpan ke history lokal.")
    except Exception as e:
        st.warning(f"Gagal menyimpan history: {e}")

    # Create PDF (filename with date)
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
        "Downes total": f"{downes_total} ({downes_note})"
    }
    pdf_bytes = create_pdf(report, fig)
    # filename: Laporan_Bayi_YYYYMMDD.pdf
    filename = f"Laporan_Bayi_{datetime.now().strftime('%Y%m%d')}.pdf"
    st.download_button("⬇ Unduh Laporan PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")

# ---------------------------
# History section (bottom) + delete
# ---------------------------
st.markdown("---")
st.subheader("Riwayat Analisis (lokal)")
hist = load_history()
if hist.empty:
    st.info("Belum ada riwayat tersimpan.")
else:
    st.dataframe(hist.sort_values(by='timestamp', ascending=False))
    st.download_button("⬇ Unduh CSV Riwayat", data=hist.to_csv(index=False).encode('utf-8'), file_name="riwayat_ballard_full.csv", mime="text/csv")
    if st.button("🗑 Hapus Semua Riwayat"):
        try:
            os.remove(HISTORY_FILE)
            st.success("Riwayat berhasil dihapus.")
        except Exception as e:
            st.error(f"Gagal menghapus riwayat: {e}")
