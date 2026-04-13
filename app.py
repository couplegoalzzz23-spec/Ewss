import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(page_title="EWS Meteorologi Explainable", layout="wide")

st.title("🌦️ Early Warning System Meteorologi (Explainable AI Version)")
st.caption("Sistem berbasis indeks atmosfer + penjelasan threshold agar mudah dipahami")

# =========================
# 🧪 SIMULASI DATA (STABIL & REALISTIS)
# =========================
@st.cache_data
def generate_data(n=60):
    np.random.seed(7)

    df = pd.DataFrame({
        "lat": np.random.uniform(-11, 6, n),
        "lon": np.random.uniform(95, 141, n),

        # atmosfer realistis
        "cape": np.random.uniform(100, 4000, n),  # J/kg
        "cloud_top_temp": np.random.uniform(-90, 20, n),  # °C
        "humidity": np.random.uniform(30, 100, n),  # %
        "rain_rate": np.random.uniform(0, 100, n)  # mm/h
    })

    return df

df = generate_data()

# =========================
# 🧮 NORMALISASI AMAN
# =========================
def norm(x, min_v, max_v):
    return np.clip((x - min_v) / (max_v - min_v), 0, 1)

# =========================
# ⚡ METEOROLOGICAL INDEX
# =========================
def compute_score(row):
    cape_n = norm(row["cape"], 0, 4000)
    ctt_n = norm(abs(row["cloud_top_temp"]), 0, 90)
    hum_n = norm(row["humidity"], 0, 100)
    rain_n = norm(row["rain_rate"], 0, 100)

    score = (0.4 * cape_n) + (0.3 * ctt_n) + (0.2 * hum_n) + (0.1 * rain_n)
    return score

df["score"] = df.apply(compute_score, axis=1)

# =========================
# 🚨 THRESHOLD CLASSIFICATION
# =========================
def classify(score):
    if score < 0.30:
        return "🟢 Aman"
    elif score < 0.60:
        return "🟡 Waspada"
    elif score < 0.80:
        return "🟠 Siaga"
    else:
        return "🔴 Ekstrem"

df["status"] = df["score"].apply(classify)

# =========================
# 🧠 EXPLANATION ENGINE (INTI EDUKASI)
# =========================
def explain(row):
    alasan = []

    if row["cape"] > 2000:
        alasan.append("CAPE tinggi → atmosfer sangat labil (potensi badai)")
    elif row["cape"] > 1000:
        alasan.append("CAPE sedang → mulai ada potensi konveksi")

    if row["cloud_top_temp"] < -60:
        alasan.append("Awan sangat tinggi (Cumulonimbus kuat)")
    elif row["cloud_top_temp"] < -40:
        alasan.append("Awan konvektif berkembang")

    if row["humidity"] > 80:
        alasan.append("Kelembapan tinggi → mendukung pembentukan awan hujan")

    if row["rain_rate"] > 40:
        alasan.append("Hujan intensitas tinggi terdeteksi")

    return alasan

# =========================
# 📊 SIDEBAR THRESHOLD EXPLANATION
# =========================
st.sidebar.header("📘 Penjelasan Threshold")

st.sidebar.markdown("""
### 🟢 Aman (0.00 – 0.30)
- Atmosfer stabil
- Hampir tidak ada awan konvektif

### 🟡 Waspada (0.30 – 0.60)
- Awal pembentukan awan hujan
- Hujan lokal mungkin terjadi

### 🟠 Siaga (0.60 – 0.80)
- Atmosfer labil
- Potensi hujan lebat & petir

### 🔴 Ekstrem (0.80 – 1.00)
- Awan Cumulonimbus aktif
- Hujan lebat & angin kencang
""")

# =========================
# 🔍 FILTER
# =========================
status_filter = st.sidebar.multiselect(
    "Filter Status",
    ["🟢 Aman", "🟡 Waspada", "🟠 Siaga", "🔴 Ekstrem"],
    default=["🟢 Aman", "🟡 Waspada", "🟠 Siaga", "🔴 Ekstrem"]
)

filtered = df[df["status"].isin(status_filter)]

# =========================
# 📊 METRIC DASHBOARD
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Area", len(df))
col2.metric("Ekstrem", len(df[df["status"] == "🔴 Ekstrem"]))
col3.metric("Siaga", len(df[df["status"] == "🟠 Siaga"]))
col4.metric("Aman", len(df[df["status"] == "🟢 Aman"]))

# =========================
# 🗺️ MAP
# =========================
st.subheader("🗺️ Peta Risiko Cuaca")

m = folium.Map(location=[-2, 118], zoom_start=5)

for _, r in filtered.iterrows():
    color = {
        "🟢 Aman": "green",
        "🟡 Waspada": "orange",
        "🟠 Siaga": "darkorange",
        "🔴 Ekstrem": "red"
    }[r["status"]]

    explanation = explain(r)

    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=6,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(
            f"""
            <b>Status:</b> {r['status']}<br>
            <b>Score:</b> {r['score']:.2f}<br><br>

            <b>Parameter:</b><br>
            CAPE: {r['cape']:.0f} J/kg<br>
            CTT: {r['cloud_top_temp']:.1f} °C<br>
            RH: {r['humidity']:.0f}%<br>
            Rain: {r['rain_rate']:.1f} mm/h<br><br>

            <b>Kenapa?</b><br>
            {"<br>".join(explanation)}
            """,
            max_width=300
        )
    ).add_to(m)

st_folium(m, width=1200, height=520)

# =========================
# 📊 DETAIL TABLE
# =========================
st.subheader("📍 Data Detail (Explainable Output)")

filtered["explanation"] = filtered.apply(explain, axis=1)

st.dataframe(
    filtered.sort_values("score", ascending=False),
    use_container_width=True
)
