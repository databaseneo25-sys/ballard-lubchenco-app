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
# DATA LUBCHENCO (DITANAM)
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42],
    "P10": [550,637,750,875,1000,1119,1250,1413,1600,1797,2000,2206,2400,2568,2700,2792,2850,2883,2900],
    "P25": [600,712,850,1000,1150,1293,1450,1639,1850,2071,2300,2535,2750,2922,3050,3141,3200,3234,3250],
    "P50": [650,787,950,1125,1300,1468,1650,1864,2100,2344,2600,2865,3100,3272,3400,3509,3600,3666,3700],
    "P75": [700,860,1050,1252,1450,1637,1850,2119,2400,2650,2900,3182,3450,3653,3800,3914,4000,4061,4100],
    "P90": [750,933,1150,1379,1600,1805,2050,2374,2700,2955,3200,3500,3800,4033,4200,4318,4400,4457,4500]
}
df_lubchenco = pd.DataFrame(DATA)

# ---------------------------
# HELPERS: Ballard -> GA
# ---------------------------
def ballard_to_gestational_age(score):
    """
    Konversi sederhana: usia_minggu = 24 + 0.4 * score
    Dibulatkan ke 1 desimal untuk display, integer minggu untuk lookup tabel.
    """
    ga = 24 + 0.4 * score
    return round(ga, 1)

# ---------------------------
# KLASIFIKASI LUBCHENCO
# ---------------------------
def classify_lubchenco(ga_weeks, weight_g):
    """
    Mengembalikan: (kategori_text, row_series_used, used_ga_int)
    """
    # Round to nearest integer week for lookup preference
    ga_int = int(round(ga_weeks))
    if ga_int not in df_lubchenco['GA_weeks'].values:
        # pick nearest available GA
        ga_int = int(df_lubchenco.iloc[(df_lubchenco['GA_weeks'] - ga_weeks).abs().argsort()[:1]]['GA_weeks'].values[0])
        note = f"(usia terdekat yang digunakan: {ga_int} minggu)"
    else:
        note = ""
    row = df_lubchenco[df_lubchenco['GA_weeks'] == ga_int].iloc[0]
    p10 = row['P10']
    p90 = row['P90']
    if weight_g < p10:
        kategori = 'SGA (Small for Gestational Age)'
    elif weight_g > p90:
        kategori = 'LGA (Large for Gestational Age)'
    else:
        kategori = 'AGA (Appropriate for Gestational Age)'
    return kategori, row, ga_int, note

# ---------------------------
# INTERPRETASI KLINIS (WHO + IDAI style)
# ---------------------------
def interpret_clinical(kategori, weight_g, ga_weeks, length_cm=None, head_cm=None):
    """
    Kembalikan list string rekomendasi / interpretasi singkat berdasarkan kategori.
    Ini adalah rekomendasi umum, bukan pengganti pedoman resmi.
    """
    notes = []
    # general notes
    notes.append(f"Hasil kategori: {kategori}")
    notes.append(f"Berat lahir: {weight_g} g, Usia gestasi: {ga_weeks} minggu")

    if "SGA" in kategori:
        notes.append("SGA: Pertimbangkan evaluasi untuk IUGR (intrauterine growth restriction).")
        notes.append("Saran singkat: monitor termoregulasi, glukosa darah, pola pemberian nutrisi (breastfeeding/TPN jika perlu).")
        notes.append("Rujuk ke neonatologi jika ditemukan tanda distress atau hipoglikemia berulang.")
    elif "LGA" in kategori:
        notes.append("LGA: Waspadai risiko hipoglikemia pasca-lahir, trauma persalinan, dan kemungkinan kebutuhan observasi lebih lama.")
        notes.append("Saran singkat: monitor gula darah, pemeriksaan ortopedi bila ada tanda trauma.")
    else:
        notes.append("AGA: Berat sesuai dengan usia gestasi. Praktik rutin neonatal dianjurkan.")
    
    # ekstra berdasarkan panjang / kepala (sangat sederhana — untuk referensi)
    if length_cm is not None:
        notes.append(f"Panjang badan: {length_cm} cm (interpretasi standar memerlukan tabel WHO spesifik).")
    if head_cm is not None:
        notes.append(f"Lingkar kepala: {head_cm} cm (interpretasi memerlukan kurva kepala menurut usia).")
    # final disclaimer
    notes.append("Catatan: Ini rekomendasi umum (WHO+IDAI style) untuk referensi. Konsultasikan dengan tim neonatologi untuk keputusan klinis.")
    return notes

# ---------------------------
# HISTORY STORAGE (lokal file CSV)
# ---------------------------
HISTORY_FILE = "history_ballard_lubchenco.csv"

def save_history(record: dict):
    """Append record (dict) to local CSV (create if not exist)."""
    df = pd.DataFrame([record])
    try:
        # if file exists, append without header
        with open(HISTORY_FILE, 'a', encoding='utf-8', newline='') as f:
            df.to_csv(f, header=f.tell()==0, index=False)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan history: {e}")
        return False

def load_history_df():
    try:
        df = pd.read_csv(HISTORY_FILE)
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ---------------------------
# PDF GENERATION (reportlab)
# ---------------------------
def create_pdf_report(result_dict, fig=None):
    """
    result_dict: dict dengan fields seperti timestamp, score, ga, weight, length, head, kategori, note_list
    fig: matplotlib figure to embed (optional)
    returns: bytes of PDF
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, (height - 20*mm), "LAPORAN: Ballard + Lubchenco Analysis")

    # Metadata
    c.setFont("Helvetica", 10)
    y = height - 30*mm
    c.drawString(20*mm, y, f"Tanggal: {result_dict.get('timestamp')}")
    y -= 6*mm
    c.drawString(20*mm, y, f"User / Sumber: {result_dict.get('source','Streamlit App')}")
    y -= 8*mm

    # Main table
    fields = [
        ("Skor Ballard", result_dict.get('score')),
        ("Perkiraan Usia Gestasi (minggu)", result_dict.get('ga_est')),
        ("Usia yang digunakan (minggu)", result_dict.get('ga_used')),
        ("Berat Lahir (g)", result_dict.get('weight_g')),
        ("Panjang (cm)", result_dict.get('length_cm') or '—'),
        ("Lingkar Kepala (cm)", result_dict.get('head_cm') or '—'),
        ("Kategori", result_dict.get('kategori'))
    ]
    c.setFont("Helvetica", 10)
    for label, val in fields:
        c.drawString(20*mm, y, f"{label}: {val}")
        y -= 6*mm

    y -= 4*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, "Interpretasi / Rekomendasi:")
    y -= 6*mm
    c.setFont("Helvetica", 10)
    for line in result_dict.get('notes', []):
        # wrap text if necessary (simple)
        text = c.beginText(22*mm, y)
        max_width = width - 40*mm
        # naive wrap
        words = line.split()
        line_buf = ""
        for w in words:
            if c.stringWidth(line_buf + " " + w, "Helvetica", 10) < max_width:
                if line_buf == "":
                    line_buf = w
                else:
                    line_buf += " " + w
            else:
                text.textLine(line_buf)
                y -= 5*mm
                line_buf = w
        if line_buf != "":
            text.textLine(line_buf)
            y -= 5*mm
        c.drawText(text)
        if y < 40*mm:
            c.showPage()
            y = height - 20*mm
    # embed figure if exists
    if fig is not None:
        try:
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            c.showPage()
            c.drawImage(img_buffer, 15*mm, height/2 - 40*mm, width=180*mm, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            # ignore image errors
            pass

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------
# STREAMLIT APP UI
# ---------------------------
st.set_page_config(page_title="Ballard + Lubchenco Analyzer (Pro)", layout="centered")
st.title("🍼 Ballard + Lubchenco Analyzer — Pro")
st.markdown("Estimasi usia gestasi dari skor Ballard, klasifikasi berat lahir terhadap kurva Lubchenco, grafik multi-percentile, interpretasi klinis (WHO + IDAI style), penyimpanan riwayat, dan ekspor PDF.")

with st.expander("📌 TIPS & Disclaimer (baca singkat)"):
    st.write("""
    - Aplikasi ini untuk tujuan edukasi dan referensi cepat. Bukan pengganti keputusan klinis.
    - Data Lubchenco tertanam (populasi historis). Untuk keputusan klinis gunakan kurva lokal/terverifikasi.
    - Interpretasi klinis bersifat umum (WHO/IDAI style).
    """)

# Input panel
st.subheader("Input Data Bayi")
col1, col2, col3 = st.columns(3)
with col1:
    total_score = st.number_input("Total Skor Ballard", min_value=0, max_value=50, value=30, step=1)
    weight_g = st.number_input("Berat lahir (gram)", min_value=300, max_value=6000, value=3000, step=10)
with col2:
    length_cm = st.number_input("Panjang badan (cm) — opsional", min_value=20.0, max_value=70.0, value=50.0, step=0.1)
    head_cm = st.number_input("Lingkar kepala (cm) — opsional", min_value=20.0, max_value=50.0, value=34.0, step=0.1)
with col3:
    source_note = st.text_input("Sumber / catatan (mis. ruang / pasien id) — opsional", value="")

if st.button("🔍 Hitung & Analisa"):
    # compute GA
    ga_est = ballard_to_gestational_age(total_score)
    kategori, row, ga_used, note = classify_lubchenco(ga_est, weight_g)
    notes = interpret_clinical(kategori, weight_g, ga_est, length_cm=length_cm, head_cm=head_cm)

    # Show results
    st.success(f"Perkiraan Usia Gestasi (Ballard): **{ga_est} minggu**")
    if note:
        st.info(note)
    st.metric("Kategori Lubchenco", kategori)

    # Show percentile row table
    st.subheader("Nilai Persentil untuk usia yang digunakan")
    display_row = row[['P10','P25','P50','P75','P90']].rename({
        'P10':'P10','P25':'P25','P50':'P50','P75':'P75','P90':'P90'
    })
    st.table(display_row.to_frame().T)

    # Plotting
    st.subheader("Grafik Pertumbuhan (Lubchenco)")
    fig, ax = plt.subplots(figsize=(8,4.5))
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P10'], linestyle='--', label='P10', color='#d62728') # red
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P25'], linestyle='-', label='P25', color='#ff7f0e') # orange
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P50'], linestyle='-', label='P50', color='#1f77b4') # blue
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P75'], linestyle='-', label='P75', color='#2ca02c') # green
    ax.plot(df_lubchenco['GA_weeks'], df_lubchenco['P90'], linestyle='--', label='P90', color='#006400') # dark green

    # Baby marker
    ax.scatter([ga_used], [weight_g], s=120, edgecolors='black', facecolors='black', zorder=5, label='Posisi Bayi')
    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat Badan (gram)")
    ax.set_title("Lubchenco growth chart (P10-P90)")
    ax.grid(alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    # Clinical interpretation
    st.subheader("Interpretasi Klinis")
    for line in notes:
        if "SGA" in line:
            st.error(line)
        elif "LGA" in line:
            st.warning(line)
        else:
            st.info(line)

    # Save history record
    record = {
        "timestamp": datetime.now().isoformat(sep=' ', timespec='seconds'),
        "score": total_score,
        "ga_est": ga_est,
        "ga_used": ga_used,
        "weight_g": weight_g,
        "length_cm": length_cm,
        "head_cm": head_cm,
        "kategori": kategori,
        "source": source_note
    }
    ok = save_history(record)
    if ok:
        st.success("Hasil disimpan ke history lokal.")

    # Download PDF
    pdf_bytes = create_pdf_report({
        "timestamp": record['timestamp'],
        "score": total_score,
        "ga_est": ga_est,
        "ga_used": ga_used,
        "weight_g": weight_g,
        "length_cm": length_cm,
        "head_cm": head_cm,
        "kategori": kategori,
        "notes": notes,
        "source": source_note
    }, fig=fig)
    st.download_button("⬇ Download laporan PDF", data=pdf_bytes, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

# ---------------------------
# HISTORY SECTION
# ---------------------------
st.markdown("---")
st.subheader("Riwayat Analisis (History)")
history_df = load_history_df()
if history_df.empty:
    st.info("Riwayat kosong. Hasil analisis akan tersimpan otomatis ketika Anda menekan tombol 'Hitung & Analisa'.")
else:
    st.dataframe(history_df.sort_values(by='timestamp', ascending=False))
    csv_bytes = history_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download semua riwayat (CSV)", data=csv_bytes, file_name="history_ballard_lubchenco.csv", mime="text/csv")

# Footer
st.markdown("---")
st.caption("Catatan: Aplikasi untuk edukasi/referensi. Gunakan kurva lokal/verifikasi untuk keputusan klinis.")
