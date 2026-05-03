import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")
st.title("👶 Ballard Visual + Lubchenco (KMK/SMK/BMK)")

# =========================
# LUBCHENCO DATA
# =========================
DATA = {
    "GA_weeks": list(range(24,44)),
    "P10": [500,600,700,800,900,1050,1200,1350,1500,1700,1900,2100,2300,2500,2600,2650,2600,2700,2750,2800],
    "P50": [700,850,1000,1150,1300,1500,1650,1800,2000,2200,2400,2550,2700,2900,3100,3200,3300,3400,3450,3500],
    "P90": [900,1050,1200,1400,1600,1800,1950,2150,2350,2550,2750,2950,3300,3500,3700,3800,3900,4000,4050,4100],
}
df_lub = pd.DataFrame(DATA)

# =========================
# BALLARD TABLE
# =========================
BALLARD_TABLE = {
    -10: 20, -5: 22, 0: 24, 5: 26, 10: 28,
    15: 30, 20: 32, 25: 34, 30: 36, 35: 38,
    40: 40, 45: 42, 50: 44
}

def score_to_ga(score):
    keys = sorted(BALLARD_TABLE.keys())
    for i in range(len(keys)-1):
        if keys[i] <= score <= keys[i+1]:
            low, high = keys[i], keys[i+1]
            return round(
                BALLARD_TABLE[low] +
                (BALLARD_TABLE[high]-BALLARD_TABLE[low]) *
                (score-low)/(high-low),1
            )

# =========================
# UI BALLARD DENGAN GAMBAR
# =========================
def ballard_ui(label, options, prefix):
    col1, col2 = st.columns([1,2])

    with col1:
        choice = st.selectbox(label, list(options.keys()))
    score = options[choice]

    with col2:
        path = f"images/{prefix}_{score}.png"
        if os.path.exists(path):
            st.image(path, caption=choice)
        else:
            st.info(f"Gambar: {prefix}_{score}.png")

    return score

st.subheader("Neuromuskular")

posture = ballard_ui("Postur", {
    "Ekstensi penuh":0,"Sedikit fleksi":1,"Fleksi sedang":2,"Fleksi baik":3,"Fleksi kuat":4
},"posture")

square = ballard_ui("Square Window", {
    ">90°":0,"90°":1,"60°":2,"45°":3,"30°":4
},"square")

arm = ballard_ui("Arm Recoil", {
    "Tidak ada":0,"Lambat":1,"Sedang":2,"Cepat":3,"Sangat kuat":4
},"arm")

popliteal = ballard_ui("Popliteal Angle", {
    ">160°":0,"140°":1,"120°":2,"100°":3,"80°":4,"<60°":5
},"popliteal")

scarf = ballard_ui("Scarf Sign", {
    "Lewat garis tengah":0,"Mendekati":1,"Di tengah":2,"Tidak sampai":3,"Sangat kaku":4
},"scarf")

heel = ballard_ui("Heel to Ear", {
    "Sangat mudah":0,"Mudah":1,"Sedikit tahanan":2,"Tahanan":3,"Tidak bisa":4
},"heel")

st.subheader("Fisik")

skin = ballard_ui("Kulit", {
    "Transparan":0,"Tipis":1,"Halus":2,"Mengelupas":3,"Keriput":4,"Retak":5
},"skin")

lanugo = ballard_ui("Lanugo", {
    "Tidak ada":0,"Sedikit":1,"Sedang":2,"Banyak":3,"Menipis":4
},"lanugo")

plantar = ballard_ui("Plantar Surface", {
    "Tidak ada garis":0,"Garis anterior":1,"1/3":2,"2/3":3,"Seluruh":4
},"plantar")

breast = ballard_ui("Payudara", {
    "Tidak ada":0,"Kecil":1,"Areola datar":2,"Areola menonjol":3,"Jelas":4
},"breast")

ear = ballard_ui("Mata & Telinga", {
    "Lunak":0,"Lambat balik":1,"Sedikit kartilago":2,"Baik":3,"Kaku":4
},"ear")

genital = ballard_ui("Genitalia", {
    "Imatur":0,"Sedikit berkembang":1,"Sedang":2,"Baik":3,"Matang":4
},"genital")

# =========================
# HITUNG
# =========================
total = sum([posture,square,arm,popliteal,scarf,heel,
             skin,lanugo,plantar,breast,ear,genital])

st.markdown("---")
st.success(f"Total Ballard: {total}")

ga = score_to_ga(total)
st.success(f"Usia Gestasi: {ga} minggu")

# =========================
# LUBCHENCO
# =========================
bb = st.number_input("Berat Lahir (gram)", 400, 4600, 3000)

if st.button("🔍 Analisa"):
    ga_round = int(round(ga))
    row = df_lub[df_lub["GA_weeks"]==ga_round].iloc[0]

    if bb < row["P10"]:
        status = "KMK (SGA)"
    elif bb > row["P90"]:
        status = "BMK (LGA)"
    else:
        status = "SMK (AGA)"

    st.success(f"Kategori: {status}")

    st.write("Referensi:")
    st.write(f"P10: {row['P10']} | P50: {row['P50']} | P90: {row['P90']}")

    # Grafik
    fig, ax = plt.subplots()
    ax.plot(df_lub["GA_weeks"], df_lub["P10"], "--")
    ax.plot(df_lub["GA_weeks"], df_lub["P50"])
    ax.plot(df_lub["GA_weeks"], df_lub["P90"], "--")
    ax.scatter(ga_round, bb, s=120)

    ax.set_xlabel("GA")
    ax.set_ylabel("BB")
    ax.grid()

    st.pyplot(fig)
