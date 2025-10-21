import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# DATA LUBCHENCO DITANAM LANGSUNG
# ==============================
data_lubchenco = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42],
    "P10": [550,637,750,875,1000,1119,1250,1413,1600,1797,2000,2206,2400,2568,2700,2792,2850,2883,2900],
    "P25": [600,712,850,1000,1150,1293,1450,1639,1850,2071,2300,2535,2750,2922,3050,3141,3200,3234,3250],
    "P50": [650,787,950,1125,1300,1468,1650,1864,2100,2344,2600,2865,3100,3272,3400,3509,3600,3666,3700],
    "P75": [700,860,1050,1252,1450,1637,1850,2119,2400,2650,2900,3182,3450,3653,3800,3914,4000,4061,4100],
    "P90": [750,933,1150,1379,1600,1805,2050,2374,2700,2955,3200,3500,3800,4033,4200,4318,4400,4457,4500]
}
df_lubchenco = pd.DataFrame(data_lubchenco)

# ==============================
# FUNGSI PERHITUNGAN BALLARD
# ==============================
def hitung_usia_gestasi_ballard(total_skor):
    usia_gestasi = (total_skor * 0.4) + 24
    return round(usia_gestasi)

# ==============================
# FUNGSI KLASIFIKASI BERAT BADAN
# ==============================
def klasifikasi_lubchenco(usia_gestasi, berat_badan):
    if usia_gestasi not in df_lubchenco['GA_weeks'].values:
        usia_terdekat = df_lubchenco.iloc[(df_lubchenco['GA_weeks'] - usia_gestasi).abs().argsort()[:1]]['GA_weeks'].values[0]
        st.warning(f"Usia {usia_gestasi} minggu tidak tersedia. Menggunakan usia terdekat: {usia_terdekat} minggu.")
        usia_gestasi = usia_terdekat

    row = df_lubchenco[df_lubchenco['GA_weeks'] == usia_gestasi].iloc[0]
    if berat_badan < row['P10']:
        kategori = "🔴 SGA (di bawah persentil 10)"
    elif berat_badan > row['P90']:
        kategori = "🟢 LGA (di atas persentil 90)"
    else:
        kategori = "🔵 AGA (normal, persentil 10-90)"
    return kategori, row, usia_gestasi
