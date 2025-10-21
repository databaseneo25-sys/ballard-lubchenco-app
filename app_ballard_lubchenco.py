import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats

"""
Aplikasi Analisa Score Ballard & Lubchenco
Educational use only. Tidak untuk penegakan diagnosa klinis.
"""

# === Fungsi Konversi Skor Ballard ke Usia Gestasi ===
def ballard_to_gestational_age(score):
    return round(24 + (score * 0.4), 1)

# === Load Data Lubchenco ===
@st.cache_data
def load_lubchenco_data():
    try:
        df = pd.read_csv("lubchenco_sample.csv")
        return df
    except:
        st.error("File 'lubchenco_sample.csv' tidak ditemukan. Pastikan sudah diupload.")
        return pd.DataFrame()

# === Fungsi Klasifikasi ===
def classify_lubchenco(gest_age, weight, sex, lubchenco_data):
    if lubchenco_data.empty:
        return "Data Lubchenco tidak tersedia."

    df = lubchenco_data[
        (lubchenco_data["Gestational_Age"] == int(round(gest_age))) &
        (lubchenco_data["Sex"].str.lower() == sex.lower())
    ]
    if df.empty:
        return "Data tidak tersedia untuk usia tersebut."

    p10 = df["P10"].values[0]
    p90 = df["P90"].values[0]

    if weight < p10:
        return "SGA (Small for Gestational Age)"
    elif weight > p90:
        return "LGA (Large for Gestational Age)"
    else:
        return "AGA (Appropriate for Gestational Age)"

# === Main App ===
def main():
    st.title("🍼 Analisa Skor Ballard & Kurva Lubchenco")
    st.write("Aplikasi untuk memperkirakan usia gestasi dan menentukan status pertumbuhan bayi baru lahir.")
    st.divider()

    score = st.number_input("Masukkan Total Skor Ballard", min_value=0, max_value=50, value=30)
    weight = st.number_input("Masukkan Berat Badan Lahir (gram)", min_value=300, max_value=6000, value=3000)
    sex = st.selectbox("Pilih Jenis Kelamin Bayi", ["Male", "Female"])

    if st.button("Analisa"):
        gest_age = ballard_to_gestational_age(score)
        st.info(f"Perkiraan Usia Gestasi: **{gest_age} minggu**")

        lubchenco_data = load_lubchenco_data()
        kategori = classify_lubchenco(gest_age, weight, sex, lubchenco_data)
        st.success(f"Hasil Klasifikasi Berat Lahir: **{kategori}**")

        st.caption("© 2025 | Edukasi Neonatologi")

if __name__ == "__main__":
    main()
