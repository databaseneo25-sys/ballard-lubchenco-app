# app_ballard_lubchenco_clean.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ballard + Lubchenco", layout="centered")

st.title("👶 Ballard → Lubchenco (KMK / SMK / BMK)")

# ---------------------------
# DATA LUBCHENCO
# ---------------------------
DATA = {
    "GA_weeks": [24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43],
    "P10": [500,600,700,800,900,1050,1200,1350,1500,1700,1900,2100,2300,2500,2600,2650,2600,2700,2750,2800],
    "P50": [700,850,1000,1150,1300,1500,1650,1800,2000,2200,2400,2550,2700,2900,3100,3200,3300,3400,3450,3500],
    "P90": [900,1050,1200,1400,1600,1800,1950,2150,2350,2550,2750,2950,3300,3500,3700,3800,3900,4000,4050,4100],
}
df_lub = pd.DataFrame(DATA)

# ---------------------------
# BALLARD TABLE
# ---------------------------
BALLARD_TABLE = {
    -10: 20, -5: 22, 0: 24, 5: 26, 10: 28,
    15: 30, 20: 32, 25: 34, 30: 36, 35: 38,
    40: 40, 45: 42, 50: 44
}

def score_to_ga(score):
    keys = sorted(BALLARD_TABLE.keys())
    if score <= keys[0]:
        return BALLARD_TABLE[keys[0]]
    if score >= keys[-1]:
        return BALLARD_TABLE[keys[-1]]

    for i in range(len(keys)-1):
        low, high = keys[i], keys[i+1]
        if low <= score <= high:
            ga_low, ga_high = BALLARD_TABLE[low], BALLARD_TABLE[high]
            return round(ga_low + (ga_high - ga_low) * ((score - low)/(high - low)), 1)

# ---------------------------
# KLASIFIKASI
# ---------------------------
def classify(ga, bb):
    ga_round = int(round(ga))

    row = df_lub[df_lub["GA_weeks"] == ga_round]
    if row.empty:
        return "Diluar range", ga_round, None

    row = row.iloc[0]
    p10, p90 = row["P10"], row["P90"]

    if bb < p10:
        status = "KMK (SGA)"
    elif bb > p90:
        status = "BMK (LGA)"
    else:
        status = "SMK (AGA)"

    return status, ga_round, row

# ---------------------------
# INPUT
# ---------------------------
st.subheader("Input Data Bayi")

ballard = st.number_input("Total Ballard Score", -10, 50, 30)
bb = st.number_input("Berat Lahir (gram)", 400, 4600, 3000)

# ---------------------------
# PROSES
# ---------------------------
if st.button("🔍 Hitung"):
    ga = score_to_ga(ballard)
    status, ga_used, row = classify(ga, bb)

    st.success(f"Usia Gestasi: {ga} minggu")
    st.success(f"Kategori: {status}")

    st.write("### Nilai Referensi Lubchenco")
    st.table(row[["P10","P50","P90"]].to_frame().T)

    # ---------------------------
    # GRAFIK
    # ---------------------------
    fig, ax = plt.subplots()

    ax.plot(df_lub["GA_weeks"], df_lub["P10"], "--", label="P10")
    ax.plot(df_lub["GA_weeks"], df_lub["P50"], "-", label="P50")
    ax.plot(df_lub["GA_weeks"], df_lub["P90"], "--", label="P90")

    ax.scatter(ga_used, bb, s=100, color="black")

    ax.set_xlabel("Usia Gestasi (minggu)")
    ax.set_ylabel("Berat (gram)")
    ax.legend()
    ax.grid()

    st.pyplot(fig)
