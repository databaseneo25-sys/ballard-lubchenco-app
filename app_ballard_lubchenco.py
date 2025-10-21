# app_lubchenco_final.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------------------
# DATA LUBCHENCO (VERSI FINAL)
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43],
    "P10": [500,600,700,800,900,1050,1200,1350,1500,1700,1900,2100,2300,2450,2550,2600,2600,2650,2700,2750],
    "P25": [600,700,850,950,1100,1250,1400,1600,1800,2000,2200,2400,2600,2750,2900,3000,3100,3150,3200,3250],
    "P50": [700,800,950,1100,1250,1400,1600,1800,2000,2200,2450,2700,2950,3100,3250,3400,3400,3450,3500,3550],
    "P75": [800,900,1050,1200,1350,1500,1700,1900,2100,2350,2600,2850,3100,3300,3550,3700,3900,3950,4000,4050],
    "P90": [900,1000,1150,1300,1500,1650,1850,2100,2350,2600,2850,3100,3350,3600,3850,4000,4300,4350,4400,4450]
}
df = pd.DataFrame(DATA)

# ---------------------------
# BALLARD → USIA GESTASI
# ---------------------------
def ballard_to_ga(score):
    """Konversi skor Ballard menjadi usia gestasi (minggu)."""
    return round(24 + 0.4 * score, 1)

# ---------------------------
# KLASIFIKASI LUBCHENCO
# ---------------------------
def classify_lubchenco(ga_weeks, bb):
    """Menentukan kategori SGA / AGA / LGA."""
    ga_near = df.iloc[(df['GA_weeks'] - ga_weeks).abs().argsort()[:1]].iloc[0]
    ga_used = ga_near['GA_weeks']
    if bb < ga_near['P10']:
        kategori = "SGA (Small for Gestational Age)"
    elif bb > ga_near['P90']:
        kategori = "LGA (Large for Gestational Age)"
    else:
        kategori = "AGA (Appropriate for Gestational Age)"
    return kategori, ga_used, ga_near

# ---------------------------
# PDF LAPORAN
# ---------------------------
def create_pdf(data, fig):
    """Membuat laporan PDF berisi hasil analisis & grafik."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "LAPORAN BALLARD + LUBCHENCO")

    c.setFont("Helvetica", 10)
    y = height - 80
    for key, val in data.items():
        c.drawString(50, y, f"{key}: {val}")
        y -= 15

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=150)
    img_buf.seek(0)
    c.drawImage(img_buf, 40, 100, width=500, preserveAspectRatio=True, mask='auto')

    c.save()
    buf.seek(0)
    return buf.getvalue()

# ---------------------------
# STREAMLIT APP
# ---------------------------
st.set_page_config(page_title="Lubchenco Final", layout="centered")
st.title("🍼 Kurva Lubchenco – Berat Lahir terhadap Usia Gestasi (Final)")

col1, col2 = st.columns(2)
with col1:
    skor = st.number_input("Skor Ballard", 0, 50, 30)
with col2:
    bb = st.number_input("Berat lahir (gram)", 400, 6000, 3000)

if st.button("🔍 Analisa"):
    # Hitung usia gestasi & klasifikasi
    ga = ballard_to_ga(skor)
    kategori, ga_used, row = classify_lubchenco(ga, bb)

    # Hasil
    st.success(f"Usia Gestasi (Ballard): **{ga} minggu** (digunakan: {ga_used} minggu)")
    st.metric("Kategori", kategori)
    st.write("**Nilai Persentil (Lubchenco):**")
    st.table(row[['P10','P25','P50','P75','P90']].to_frame().T)

    # ---------------------------
    # GRAFIK (warna & grid mirip grafik asli)
    # ---------------------------
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor("#f9f9f9")
    ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.6)

    # Garis bantu tiap 1 minggu dan 500 gram
    ax.set_xticks(range(24, 44, 1))
    ax.set_yticks(range(400, 4601, 500))
    ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.6)

    # Garis persentil berwarna
    ax.plot(df["GA_weeks"], df["P10"], '--', color="#e74c3c", linewidth=2, label="P10 (Merah)")
    ax.plot(df["GA_weeks"], df["P25"], '-', color="#f39c12", linewidth=2, label="P25 (Oranye)")
    ax.plot(df["GA_weeks"], df["P50"], '-', color="#3498db", linewidth=2.5, label="P50 (Biru)")
    ax.plot(df["GA_weeks"], df["P75"], '-', color="#27ae60", linewidth=2, label="P75 (Hijau)")
    ax.plot(df["GA_weeks"], df["P90"], '--', color="#8e44ad", linewidth=2, label="P90 (Ungu)")

    # Titik bayi
    ax.scatter([ga_used], [bb], s=160, color="black", edgecolors="white", zorder=5, label="Bayi")

    # Batas sumbu
    ax.set_xlim(24, 43)
    ax.set_ylim(400, 4600)

    # Label dan gaya
    ax.set_xlabel("Usia Gestasi (minggu)", fontsize=11)
    ax.set_ylabel("Berat Badan (gram)", fontsize=11)
    ax.set_title("Kurva Lubchenco — Berat Lahir terhadap Usia Gestasi", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", frameon=True)
    st.pyplot(fig)

    # ---------------------------
    # PDF download
    # ---------------------------
    report_data = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Skor Ballard": skor,
        "Usia Gestasi (minggu)": ga,
        "Usia Digunakan": ga_used,
        "Berat Lahir (gram)": bb,
        "Kategori": kategori
    }
    pdf_bytes = create_pdf(report_data, fig)
    st.download_button(
        "⬇ Unduh Laporan PDF",
        data=pdf_bytes,
        file_name=f"laporan_lubchenco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )
