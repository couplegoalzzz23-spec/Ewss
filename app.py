import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium

# =========================
# 🌦️ CONFIG APP
# =========================
st.set_page_config(page_title="EWS Meteorologi Pro", layout="wide")

st.title("🌦️ Early Warning System Meteorologi (Pro Version)")
st.caption("Sistem berbasis indeks atmosfer: CAPE, Cloud Top Temperature, Humidity, Rain Rate")

# =========================
# 🧠 SIMULASI DATA ATMOSFER
# =========================
def generate_data(n=50):
    np.random.seed(42)
    
    data = pd.DataFrame({
        "lat": np.random.uniform(-11, 6, n),   # Indonesia region
        "lon": np.random.uniform(95, 141, n),
        "cape": np.random.uniform(200, 3500, n),  # J/kg
        "cloud_top_temp": np.random.uniform(-90, 10, n),  # °C
        "humidity": np.random.uniform(30, 100, n),  # %
        "rain_rate": np.random.uniform(0, 80, n)  # mm/h
    })
    return data

df = generate_data()

# =========================
# 🧮 NORMALISASI INDEX
# =========================
def normalize(x, min_val, max_val):
    return (x - min_val) / (max_val - min_val)

# =========================
# ⚡ METEOROLOGICAL INDEX
# =========================
def compute_index(row):
    cape_n = normalize(row["cape"], 0, 4000)
    ctt_n = normalize(abs(row["cloud_top_temp"]), 0, 100)
    hum_n = normalize(row["humidity"], 0, 100)
    rain_n = normalize(row["rain_rate"], 0, 100)

    score = (
        0.4 * cape_n +
        0.3 * ctt_n +
        0.2 * hum_n +
        0.1 * rain_n
    )

    return score

df["score"] = df.apply(compute_index, axis=1)

# =========================
# 🚨 KLASIFIKASI RISIKO
# =========================
def classify(score):
    if score < 0.3:
        return "🟢 Aman"
    elif score < 0.6:
        return "🟡 Waspada"
    elif score < 0.8:
        return "🟠 Siaga"
    else:
        return "🔴 Ekstrem"

df["status"] = df["score"].apply(classify)

# =========================
# 📊 SIDEBAR FILTER
# =========================
st.sidebar.header("⚙️ Filter Area")

status_filter = st.sidebar.multiselect(
    "Pilih Status",
    ["🟢 Aman", "🟡 Waspada", "🟠 Siaga", "🔴 Ekstrem"],
    default=["🟢 Aman", "🟡 Waspada", "🟠 Siaga", "🔴 Ekstrem"]
)

filtered_df = df[df["status"].isin(status_filter)]

# =========================
# 🗺️ PETA INTERAKTIF
# =========================
st.subheader("🗺️ Peta Risiko Cuaca")

m = folium.Map(location=[-2, 118], zoom_start=5)

for _, row in filtered_df.iterrows():
    color = {
        "🟢 Aman": "green",
        "🟡 Waspada": "orange",
        "🟠 Siaga": "darkorange",
        "🔴 Ekstrem": "red"
    }[row["status"]]

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=6,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=f"""
        Status: {row['status']}<br>
        Score: {row['score']:.2f}<br>
        CAPE: {row['cape']:.0f} J/kg<br>
        CTT: {row['cloud_top_temp']:.1f} °C<br>
        RH: {row['humidity']:.0f}%<br>
        Rain: {row['rain_rate']:.1f} mm/h
        """
    ).add_to(m)

st_data = st_folium(m, width=1200, height=500)

# =========================
# 📊 DASHBOARD STATISTIK
# =========================
st.subheader("📊 Statistik Kondisi Atmosfer")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Area", len(df))
col2.metric("Ekstrem", len(df[df["status"] == "🔴 Ekstrem"]))
col3.metric("Siaga", len(df[df["status"] == "🟠 Siaga"]))
col4.metric("Aman", len(df[df["status"] == "🟢 Aman"]))

st.bar_chart(df["status"].value_counts())

# =========================
# 🧠 DETAIL ANALISIS
# =========================
st.subheader("📍 Data Detail")

st.dataframe(filtered_df.sort_values("score", ascending=False))
