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

st.set_page_config(page_title="Ballard + Lubchenco Final", layout="centered")
st.title("🍼 Penilaian Neonatus: APGAR + Downes + Ballard + Lubchenco")

# ---------------------
# 1️⃣ APGAR SCORE
# ---------------------
st.subheader("1️⃣ APGAR Score (menit 1, 5, 10)")
apgar = {"1'": {}, "5'": {}, "10'": {}}
apgar_components = [
    "Appearance (Warna kulit)",
    "Pulse (Denyut jantung)",
    "Grimace (Respons refleks)",
    "Activity (Tonus otot)",
    "Respiration (Pernapasan)"
]

for minute in ["1'", "5'", "10'"]:
    st.markdown(f"**APGAR menit {minute}**")
    cols = st.columns(3)
    for i, comp in enumerate(apgar_components):
        with cols[i % 3]:
            apgar[minute][comp] = st.number_input(
                f"{comp} ({minute})",
                min_value=0, max_value=2, value=2 if minute != "1'" else 1, step=1, key=f"apgar_{minute}_{i}"
            )

# ---------------------
# 2️⃣ DOWNES SCORE
# ---------------------
st.subheader("2️⃣ Downes Score (Penilaian Respirasi)")
downes_items = [
    "Frekuensi napas / distress",
    "Cyanosis",
    "Retraksi",
    "Grunting",
    "Air entry"
]
downes_scores = {}
cols = st.columns(3)
for i, label in enumerate(downes_items):
    with cols[i % 3]:
        downes_scores[label] = st.number_input(
            f"{label} (0–2)", min_value=0, max_value=2, value=0, step=1, key=f"downes_{i}"
        )

downes_total = sum(downes_scores.values())
if downes_total <= 3:
    downes_note = "Ringan"
elif downes_total <= 6:
    downes_note = "Sedang"
else:
    downes_note = "Berat"
st.info(f"Total Downes: **{downes_total} → {downes_note}**")

# ---------------------------
# DATA LUBCHENCO
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43],
    "P10": [500,600,700,800,950,1100,1250,1400,1550,1700,1900,2100,2300,2500,2600,2650,2600,2700,2750,2800],
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
# PDF REPORT
# ---------------------------
def create_pdf(report_data, fig):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LAPORAN: BALLARD + LUBCHENCO")

    c.setFont("Helvetica", 10)
    y = height - 80
    for k, v in report_data.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 14

    # Simpan grafik
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
# HISTORY
# ---------------------------
HISTORY_FILE = "history_ballard_lubchenco.csv"

def save_history(record):
    df = pd.DataFrame([record])
    header = not os.path.exists(HISTORY_FILE)
    df.to_csv(HISTORY_FILE, mode='a', index=False, header=header, encoding='utf-8')

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.title("👶 Aplikasi Ballard + Kurva Lubchenco (KMK/SMK/BMK) Transisi RSUD dr Mohamad Soewandhie")
st.caption("💌Persembahan khusus dari Kami sebagai bentuk komitmen dalam optimalisasi pelayanan perinatologi dan neonatal care dengan Menilai usia kehamilan dari skor Ballard, menentukan status pertumbuhan bayi berdasarkan kurva Lubchenco.")

with st.expander("📖 Petunjuk Singkat"):
    st.write("""
    1. Isi semua komponen Ballard (0–4/5).
    2. Aplikasi menghitung total skor dan usia kehamilan (tabel resmi Ballard).
    3. Masukkan berat bayi → sistem menampilkan hasil KMK / SMK / BMK.
    4. Grafik Lubchenco dan laporan PDF akan otomatis tersedia.
    """)

# Form Ballard
st.subheader("🧠 Komponen Ballard")
cols = st.columns(3)
ballard_scores = {}
for i, (label, lo, hi) in enumerate(BALLARD_ITEMS):
    with cols[i % 3]:
        ballard_scores[label] = st.number_input(label, min_value=lo, max_value=hi, value=2, step=1, key=f"ballard_{i}")

total_score = sum(ballard_scores.values())
ga_ballard = score_to_ga(total_score)

st.markdown(f"**Total Skor Ballard:** {total_score}")
st.markdown(f"**Usia Kehamilan (tabel Ballard):** {ga_ballard} minggu")

# Berat input
st.subheader("⚖️ Berat Lahir")
berat = st.number_input("Masukkan berat lahir (gram)", min_value=400, max_value=4600, value=3000, step=50)

# Analisis
if st.button("🔍 Hitung & Tampilkan Hasil"):
    kategori, ga_used, row = classify_kmk_smk_bmk(ga_ballard, berat)

    st.success(f"Usia gestasi digunakan: **{ga_used} minggu**")
    st.metric("Kategori (Lubchenco)", kategori)
    st.table(row[['P10', 'P25', 'P50', 'P75', 'P90']].to_frame().T)

    # Plot grafik
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

    ax.scatter([ga_used], [berat], s=160, color="black", edgecolors="white", zorder=5, label="Bayi")

    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat Badan (gram)")
    ax.set_title("Kurva Lubchenco – Berat Lahir terhadap Usia Gestasi")
    ax.legend()
    st.pyplot(fig)

    # PDF
    report = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Total Skor Ballard": total_score,
        "Usia Gestasi (Ballard)": ga_ballard,
        "Usia digunakan (Lubchenco)": ga_used,
        "Berat lahir (g)": berat,
        "Kategori": kategori
    }
    pdf_bytes = create_pdf(report, fig)
    st.download_button("⬇ Unduh Laporan PDF", data=pdf_bytes, file_name=f"laporan_ballard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

    # History
    save_history({
        "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "total_ballard": total_score,
        "ga_ballard": ga_ballard,
        "ga_used": ga_used,
        "berat_g": berat,
        "kategori": kategori
    })

# History
st.markdown("---")
st.subheader("🧾 Riwayat Analisis")
hist = load_history()
if hist.empty:
    st.info("Belum ada riwayat tersimpan.")
else:
    st.dataframe(hist.sort_values(by='timestamp', ascending=False))
    st.download_button("⬇ Unduh CSV Riwayat", data=hist.to_csv(index=False).encode('utf-8'), file_name="riwayat_ballard_lubchenco.csv", mime="text/csv")
    # Tombol hapus riwayat
if not hist.empty:
    if st.button("🗑 Hapus Semua Riwayat"):
        try:
            os.remove(HISTORY_FILE)
            st.success("Riwayat analisis berhasil dihapus!")
        except Exception as e:
            st.error(f"Gagal menghapus riwayat: {e}")
