# app_ballard_lubchenco.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# ---------------------------
# DATA LUBCHENCO (versi dikoreksi)
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42],
    "P10": [500,600,700,850,1000,1150,1300,1500,1700,1900,2100,2300,2500,2500,2550,2600,2600,2650,2700],
    "P25": [600,700,850,1000,1150,1300,1500,1700,1900,2100,2300,2500,2700,2800,2900,3000,3100,3150,3200],
    "P50": [700,800,950,1100,1300,1500,1700,1900,2100,2300,2500,2750,3000,3100,3200,3300,3400,3450,3500],
    "P75": [800,900,1050,1200,1400,1600,1800,2000,2250,2500,2700,2950,3200,3300,3400,3500,3700,3750,3800],
    "P90": [900,1000,1150,1300,1500,1700,1900,2100,2400,2650,2900,3150,3400,3500,3600,3700,4000,4050,4100],
}
df_lubchenco = pd.DataFrame(DATA)

# ---------------------------
# HELPERS: Ballard -> GA
# ---------------------------
def ballard_to_gestational_age(score):
    """Konversi sederhana Ballard → usia gestasi (minggu)."""
    ga = 24 + 0.4 * score
    return round(ga, 1)

# ---------------------------
# KLASIFIKASI LUBCHENCO
# ---------------------------
def classify_lubchenco(ga_weeks, weight_g):
    ga_int = int(round(ga_weeks))
    if ga_int not in df_lubchenco['GA_weeks'].values:
        ga_int = int(df_lubchenco.iloc[(df_lubchenco['GA_weeks'] - ga_weeks).abs().argsort()[:1]]['GA_weeks'].values[0])
        note = f"(usia terdekat yang digunakan: {ga_int} minggu)"
    else:
        note = ""
    row = df_lubchenco[df_lubchenco['GA_weeks'] == ga_int].iloc[0]
    p10, p90 = row['P10'], row['P90']
    if weight_g < p10:
        kategori = 'SGA (Small for Gestational Age)'
    elif weight_g > p90:
        kategori = 'LGA (Large for Gestational Age)'
    else:
        kategori = 'AGA (Appropriate for Gestational Age)'
    return kategori, row, ga_int, note

# ---------------------------
# INTERPRETASI KLINIS
# ---------------------------
def interpret_clinical(kategori, weight_g, ga_weeks, length_cm=None, head_cm=None):
    notes = []
    notes.append(f"Hasil kategori: {kategori}")
    notes.append(f"Berat lahir: {weight_g} g, Usia gestasi: {ga_weeks} minggu")

    if "SGA" in kategori:
        notes.append("SGA: Pertimbangkan evaluasi untuk IUGR (intrauterine growth restriction).")
        notes.append("Saran: monitor suhu, glukosa darah, serta pola nutrisi (ASI / TPN bila perlu).")
        notes.append("Rujuk neonatologi bila ada distress atau hipoglikemia berulang.")
    elif "LGA" in kategori:
        notes.append("LGA: Risiko hipoglikemia pasca-lahir dan trauma persalinan meningkat.")
        notes.append("Saran: monitor gula darah, pemeriksaan ortopedi bila ada trauma.")
    else:
        notes.append("AGA: Berat sesuai usia gestasi, lakukan perawatan neonatal rutin.")

    if length_cm:
        notes.append(f"Panjang badan: {length_cm} cm (interpretasi WHO memerlukan tabel tambahan).")
    if head_cm:
        notes.append(f"Lingkar kepala: {head_cm} cm (interpretasi berdasarkan kurva kepala WHO).")
    notes.append("Catatan: Rekomendasi umum WHO/IDAI — bukan keputusan klinis final.")
    return notes

# ---------------------------
# HISTORY STORAGE
# ---------------------------
HISTORY_FILE = "history_ballard_lubchenco.csv"

def save_history(record: dict):
    df = pd.DataFrame([record])
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8', newline='') as f:
            df.to_csv(f, header=f.tell()==0, index=False)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan history: {e}")
        return False

def load_history_df():
    try:
        return pd.read_csv(HISTORY_FILE)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ---------------------------
# PDF GENERATION
# ---------------------------
def create_pdf_report(result_dict, fig=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, (height - 20*mm), "LAPORAN: Ballard + Lubchenco Analysis")

    c.setFont("Helvetica", 10)
    y = height - 30*mm
    c.drawString(20*mm, y, f"Tanggal: {result_dict.get('timestamp')}")
    y -= 6*mm
    c.drawString(20*mm, y, f"Sumber: {result_dict.get('source','Streamlit App')}")
    y -= 8*mm

    fields = [
        ("Skor Ballard", result_dict.get('score')),
        ("Usia Gestasi (minggu)", result_dict.get('ga_est')),
        ("Usia yang digunakan (minggu)", result_dict.get('ga_used')),
        ("Berat Lahir (g)", result_dict.get('weight_g')),

    ]
    for label, val in fields:
        c.drawString(20*mm, y, f"{label}: {val}")
        y -= 6*mm

    y -= 4*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, "Interpretasi / Rekomendasi:")
    y -= 6*mm
    c.setFont("Helvetica", 10)
    for line in result_dict.get('notes', []):
        text = c.beginText(22*mm, y)
        max_width = width - 40*mm
        words, buf = line.split(), ""
        for w in words:
            if c.stringWidth(buf + " " + w, "Helvetica", 10) < max_width:
                buf = (buf + " " + w).strip()
            else:
                text.textLine(buf)
                y -= 5*mm
                buf = w
        if buf:
            text.textLine(buf)
            y -= 5*mm
        c.drawText(text)
        if y < 40*mm:
            c.showPage()
            y = height - 20*mm

    if fig:
        try:
            img_buf = BytesIO()
            fig.savefig(img_buf, format='png', bbox_inches='tight')
            img_buf.seek(0)
            c.showPage()
            c.drawImage(img_buf, 15*mm, height/2 - 40*mm, width=180*mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------
# STREAMLIT APP UI
# ---------------------------
st.set_page_config(page_title="Ballard + Lubchenco Analyzer (Pro)", layout="centered")
st.title("❤Persembahan khusus dari Ruang Transisi RSUD dr. Mohamad Soewandhie Surabaya sebagai bentuk komitmen dalam optimalisasi pelayanan perinatologi dan neonatal care")

with st.expander("📌 TIPS & Disclaimer"):
    st.write("""
    - Aplikasi ini untuk edukasi & referensi cepat (bukan keputusan klinis final).
    - Data kurva berdasar Lubchenco klasik + penyesuaian IDAI.
    - Gunakan kurva lokal/WHO untuk akurasi populasi setempat.
    """)

st.subheader("Input Data Bayi")
col1, col2, col3 = st.columns(3)
with col1:
    total_score = st.number_input("Total Skor Ballard", 0, 50, 30, 1)
    weight_g = st.number_input("Berat lahir (gram)", 300, 6000, 3000, 10)
with col2:
    length_cm = st.number_input("Panjang badan (cm)", 20.0, 70.0, 50.0, 0.1)
    head_cm = st.number_input("Lingkar kepala (cm)", 20.0, 50.0, 34.0, 0.1)
with col3:
    source_note = st.text_input("Sumber / catatan (opsional)", value="")

if st.button("🔍 Hitung & Analisa"):
    ga_est = ballard_to_gestational_age(total_score)
    kategori, row, ga_used, note = classify_lubchenco(ga_est, weight_g)
    notes = interpret_clinical(kategori, weight_g, ga_est, length_cm, head_cm)

    st.success(f"Usia Gestasi (Ballard): **{ga_est} minggu**")
    if note: st.info(note)
    st.metric("Kategori Lubchenco", kategori)

    st.subheader("Nilai Persentil (minggu digunakan)")
    st.table(row[['P10','P25','P50','P75','P90']].to_frame().T)

    st.subheader("Grafik Pertumbuhan (Lubchenco)")
    fig, ax = plt.subplots(figsize=(8,4.5))
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P10'], '--', label='P10', color='#d62728')
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P25'], '-', label='P25', color='#ff7f0e')
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P50'], '-', label='P50', color='#1f77b4')
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P75'], '-', label='P75', color='#2ca02c')
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P90'], '--', label='P90', color='#006400')
    ax.scatter([ga_used], [weight_g], s=120, edgecolors='black', facecolors='black', zorder=5, label='Bayi')
    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat (g)")
    ax.set_title("Kurva Lubchenco (P10–P90)")
    ax.grid(alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    st.subheader("Interpretasi Klinis")
    for line in notes:
        if "SGA" in line:
            st.error(line)
        elif "LGA" in line:
            st.warning(line)
        else:
            st.info(line)

    record = {
        "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "score": total_score, "ga_est": ga_est, "ga_used": ga_used,
        "weight_g": weight_g, "length_cm": length_cm, "head_cm": head_cm,
        "kategori": kategori, "source": source_note
    }
    if save_history(record): st.success("Tersimpan ke history lokal.")

    pdf_bytes = create_pdf_report({
        "timestamp": record['timestamp'], "score": total_score,
        "ga_est": ga_est, "ga_used": ga_used, "weight_g": weight_g,
        "length_cm": length_cm, "head_cm": head_cm,
        "kategori": kategori, "notes": notes, "source": source_note
    }, fig=fig)
    st.download_button("⬇ Download laporan PDF",
                       data=pdf_bytes,
                       file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                       mime="application/pdf")

st.markdown("---")
st.subheader("Riwayat Analisis")
history_df = load_history_df()
if history_df.empty:
    st.info("Belum ada riwayat.")
else:
    st.dataframe(history_df.sort_values("timestamp", ascending=False))
    st.download_button("⬇ Download Riwayat (CSV)",
                       data=history_df.to_csv(index=False).encode('utf-8'),
                       file_name="history_ballard_lubchenco.csv",
                       mime="text/csv")

st.markdown("---")
st.caption("Aplikasi edukasi — gunakan kurva lokal/WHO untuk keputusan klinis.")
