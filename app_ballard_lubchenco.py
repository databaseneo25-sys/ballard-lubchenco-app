import streamlit as st
import pandas as pd

# --------------------------
# Fungsi Klasifikasi Ballard
# --------------------------
def hitung_usia_gestasi_ballard(total_skor):
    # Rumus konversi skor Ballard ke usia gestasi
    usia_gestasi = (total_skor * 0.4) + 24
    return round(usia_gestasi)  # dibulatkan ke minggu terdekat

# --------------------------
# Fungsi Klasifikasi Lubchenco
# --------------------------
def klasifikasi_lubchenco(usia_gestasi, berat_badan, df):
    # Pastikan usia gestasi tersedia dalam data
    if usia_gestasi not in df['GA_weeks'].values:
        # jika tidak ada, cari usia terdekat
        usia_terdekat = df.iloc[(df['GA_weeks'] - usia_gestasi).abs().argsort()[:1]]['GA_weeks'].values[0]
        st.warning(f"Usia gestasi {usia_gestasi} minggu tidak ditemukan dalam tabel. "
                   f"Digunakan usia terdekat: {usia_terdekat} minggu.")
        usia_gestasi = usia_terdekat

    data_bayi = df[df['GA_weeks'] == usia_gestasi].iloc[0]
    batas_sga = data_bayi['P10']
    batas_lga = data_bayi['P90']

    if berat_badan < batas_sga:
        kategori = 'SGA (Small for Gestational Age)'
    elif berat_badan > batas_lga:
        kategori = 'LGA (Large for Gestational Age)'
    else:
        kategori = 'AGA (Appropriate for Gestational Age)'

    return kategori, batas_sga, batas_lga, usia_gestasi

# --------------------------
# Tampilan Streamlit
# --------------------------
st.title("🩺 Aplikasi Penilaian Usia Gestasi & Klasifikasi Bayi (Ballard + Lubchenco)")
st.write("Aplikasi ini menghitung usia gestasi dari skor Ballard dan mengklasifikasikan bayi berdasarkan kurva Lubchenco.")

# Upload File CSV
uploaded_file = st.file_uploader("📄 Upload file tabel Lubchenco (CSV format standar)", type=["csv"])

if uploaded_file:
    df_lubchenco = pd.read_csv(uploaded_file)
    st.success("File CSV berhasil diupload dan dibaca ✅")

    # Input Skor Ballard
    total_skor = st.number_input("🧮 Masukkan Total Skor Ballard", min_value=0, max_value=50, step=1)
    berat_badan = st.number_input("⚖️ Masukkan Berat Badan Bayi (gram)", min_value=300, max_value=6000, step=10)

    if st.button("🔎 Analisa"):
        usia_gestasi = hitung_usia_gestasi_ballard(total_skor)
        kategori, batas_sga, batas_lga, usia_final = klasifikasi_lubchenco(usia_gestasi, berat_badan, df_lubchenco)

        st.subheader("📊 Hasil Analisis")
        st.write(f"**Usia Gestasi (hasil Ballard):** {usia_gestasi} minggu")
        st.write(f"**Usia Gestasi yang digunakan (sesuai tabel):** {usia_final} minggu")
        st.write(f"**Berat Badan Bayi:** {berat_badan} gram")
        st.write(f"**Kategori Lubchenco:** 🟢 **{kategori}**")
        st.write(f"Batas SGA (P10): {batas_sga} g | Batas LGA (P90): {batas_lga} g")

else:
    st.info("📌 Silakan upload file CSV Lubchenco terlebih dahulu untuk melanjutkan.")
