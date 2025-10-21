\"\"\"
Streamlit app: Ballard + Lubchenco analyzer
- Input: Ballard component scores (or total score) -> estimate gestational age (weeks)
- Input: Birth weight (grams) and sex
- Uses built-in Lubchenco sample data for automatic classification
Usage:
1) Install streamlit: pip install streamlit pandas numpy scipy
2) Run: streamlit run app_ballard_lubchenco.py
Note: This tool is for educational / quick-reference only. For clinical decisions, use validated local growth charts and consult neonatology guidelines.
\"\"\"

import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

st.set_page_config(page_title=\"Ballard + Lubchenco Analyzer\", layout=\"centered\")
st.title(\"Gabungan: Ballard Score → Estimasi Usia Gestasi → Klasifikasi Lubchenco\")
st.markdown(\"Aplikasi sederhana untuk menghitung usia gestasi dari skor Ballard dan mengklasifikasikan berat lahir terhadap kurva Lubchenco. **Bukan pengganti keputusan klinis**. (Sumber: Ballard score, Lubchenco charts).\")


# Input method
st.header(\"1) Masukkan skor Ballard\")
mode = st.radio(\"Pilih metode input Ballard:\", (\"Total score (langsung)\", \"Masukkan 12 komponen (neuromuscular + physical)\"))

if mode == \"Total score (langsung)\":
    total_score = st.number_input(\"Total Ballard score (contoh: 30)\", value=30, step=1)
    # Use simple conversion formula for New Ballard: age_weeks = (2*score + 120)/5
    ga_weeks = (2 * total_score + 120) / 5.0
else:
    st.write(\"Masukkan nilai tiap komponen. Gunakan rentang -1..5 sesuai New Ballard jika perlu.\")
    cols = st.columns(2)
    neuromusc = ['Posture','Square window','Arm recoil','Popliteal angle','Scarf sign','Heel to ear']
    physical = ['Skin','Lanugo','Plantar surface','Breast','Eye/Ear','Genitals']
    neuros = []
    phys = []
    for i, name in enumerate(neuromusc):
        val = cols[0].number_input(f\"{name}\", value=2, step=1, key=f'n_{i}')
        neuros.append(val)
    for i, name in enumerate(physical):
        val = cols[1].number_input(f\"{name}\", value=2, step=1, key=f'p_{i}')
        phys.append(val)
    total_score = sum(neuros) + sum(phys)
    st.write(f\"Total Ballard score (otomatis): **{total_score}**\")
    ga_weeks = (2 * total_score + 120) / 5.0

st.success(f\"Estimasi usia gestasi dari Ballard: **{ga_weeks:.1f} minggu**\")


# Birth weight and sex
st.header(\"2) Masukkan berat lahir & jenis kelamin\")
weight = st.number_input(\"Berat lahir (gram)\", value=3000, step=10)
sex = st.selectbox(\"Jenis kelamin bayi:\", (\"Laki-laki\",\"Perempuan\",\"Tidak diketahui / campur\"))

# Built-in Lubchenco sample data (used for automatic classification)
lubchenco = pd.DataFrame({
    'week': [24,26,28,30,32,34,36,38,40,42],
    'p10':   [600,800,1000,1300,1600,2000,2500,2900,3100,3200],
    'p50':   [760,1050,1300,1600,2000,2400,2900,3300,3500,3600],
    'p90':   [900,1250,1600,2000,2600,3000,3500,3900,4200,4400]
})

st.header(\"3) Klasifikasi Lubchenco (menggunakan data bawaan)\")
st.write(\"Aplikasi akan menginterpolasi nilai percentil dari data Lubchenco bawaan untuk usia gestasi yang diperkirakan. Dataset internal ini untuk tujuan demo/edukasi. Untuk keputusan klinis, gunakan kurva lokal yang valid.\")

# interpolation
weeks = lubchenco['week'].values
f10 = interp1d(weeks, lubchenco['p10'].values, bounds_error=False, fill_value=(lubchenco['p10'].iloc[0], lubchenco['p10'].iloc[-1]))
f50 = interp1d(weeks, lubchenco['p50'].values, bounds_error=False, fill_value=(lubchenco['p50'].iloc[0], lubchenco['p50'].iloc[-1]))
f90 = interp1d(weeks, lubchenco['p90'].values, bounds_error=False, fill_value=(lubchenco['p90'].iloc[0], lubchenco['p90'].iloc[-1]))

est_p10 = float(f10(ga_weeks))
est_p50 = float(f50(ga_weeks))
est_p90 = float(f90(ga_weeks))

st.write(f\"Interpolasi percentil untuk GA {ga_weeks:.1f} minggu:\\n- 10th ≈ {est_p10:.0f} g\\n- 50th ≈ {est_p50:.0f} g\\n- 90th ≈ {est_p90:.0f} g\")

if weight < est_p10:
    classification = 'SGA (<10th percentile)'
elif weight > est_p90:
    classification = 'LGA (>90th percentile)'
else:
    classification = 'AGA (10th-90th percentile)'

st.metric(\"Klasifikasi menurut Lubchenco\", classification)

# Output summary
st.header(\"Hasil ringkasan\")
st.write(f\"- Usia gestasi (Ballard): **{ga_weeks:.1f} minggu**\")
st.write(f\"- Berat lahir: **{weight:.0f} g**\")
st.write(f\"- Klasifikasi Lubchenco (otomatis): **{classification}**\")

st.markdown(\"---\")
st.subheader(\"Catatan penting\")
st.write(\"\"\"
- Kurva Lubchenco adalah kurva historis yang dibuat dari populasi tertentu; hasil dapat berbeda bila dibandingkan kurva lokal/contemporary (mis. Fenton, INTERGROWTH-21).
- Aplikasi ini dimaksudkan sebagai alat bantu cepat; tidak menggantikan penilaian klinis.
- Sumber referensi: New Ballard Score (Ballard 1991) dan Lubchenco charts (Battaglia & Lubchenco).
\"\"\")

# provide sample csv as download
sample = lubchenco.copy()
st.download_button(label='Download contoh CSV Lubchenco (format)', data=sample.to_csv(index=False), file_name='lubchenco_sample.csv', mime='text/csv')
