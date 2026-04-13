import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(page_title="Cb Detection IR Himawari", layout="wide")

st.title("🌩️ Automatic Cumulonimbus Detection (Himawari IR)")
st.caption("Prototype berbasis citra satelit IR BMKG - pixel-based convective detection")

# =========================
# 🛰️ LOAD IMAGE BMKG IR
# =========================
@st.cache_data
def load_ir():
    url = "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/thumbnail_AHI88_IR1.png"
    
    try:
        r = requests.get(url, timeout=10)
        img = Image.open(BytesIO(r.content)).convert("L")
        return np.array(img), None
    except Exception as e:
        return None, str(e)

img, error = load_ir()

# fallback kalau gagal
if error or img is None:
    st.warning("⚠️ Gagal ambil data BMKG, menggunakan data simulasi.")
    img = np.random.randint(0, 255, (500, 500))

# =========================
# 🌡️ PIXEL → TEMPERATURE PROXY
# =========================
def pixel_to_temp(pixel):
    # proxy IR brightness → suhu (approximation)
    return -90 + (pixel / 255) * 100

ctt = pixel_to_temp(img)

# =========================
# 🌩️ CB DETECTION ENGINE
# =========================
def detect_cb(ctt_array):

    # cold cloud threshold (Cb candidate)
    cb_mask = ctt_array < -70

    # coverage (% area)
    coverage = np.sum(cb_mask) / cb_mask.size

    # intensity (rata-rata suhu awan dingin)
    if np.any(cb_mask):
        intensity = np.mean(ctt_array[cb_mask])
    else:
        intensity = -999

    # scoring system
    score = (coverage * 0.7)

    if intensity != -999:
        score += (abs(intensity + 70) / 70) * 0.3

    return cb_mask, coverage, intensity, score

cb_mask, coverage, intensity, score = detect_cb(ctt)

# =========================
# 🚨 CLASSIFICATION
# =========================
def classify(score):
    if score < 0.2:
        return "🟢 Tidak signifikan"
    elif score < 0.4:
        return "🟡 CB mulai berkembang"
    elif score < 0.6:
        return "🟠 CB aktif (hujan lebat)"
    else:
        return "🔴 CB sangat aktif (cuaca ekstrem)"

status = classify(score)

# =========================
# 📊 DASHBOARD
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛰️ Citra IR BMKG")
    st.image(img, use_container_width=True)

    st.subheader("🌩️ Deteksi CB (mask)")
    st.image(cb_mask.astype(np.uint8) * 255, use_container_width=True)

with col2:
    st.subheader("📊 Hasil Analisis")

    st.metric("CB Coverage", f"{coverage*100:.2f}%")
    st.metric("CB Score", f"{score:.2f}")
    st.metric("Status", status)

    if intensity == -999:
        st.warning("Tidak ada area CB terdeteksi")
    else:
        st.metric("CB Intensity (proxy °C)", f"{intensity:.2f}")

    st.write("### 🧠 Interpretasi")
    st.write("""
    Sistem ini mendeteksi Cumulonimbus berdasarkan:
    - Suhu puncak awan sangat dingin (< -70°C)
    - Luas area awan dingin (coverage)
    
    Semakin besar coverage + semakin dingin awan → semakin tinggi potensi badai.
    """)

# =========================
# 📊 HISTOGRAM SUHU
# =========================
st.subheader("📊 Distribusi Suhu Awan (Proxy CTT)")

fig, ax = plt.subplots()
ax.hist(ctt.flatten(), bins=30)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Pixel count")
ax.set_title("Cloud Top Temperature Distribution")

st.pyplot(fig)

# =========================
# 🔍 DETAIL NUMERIK
# =========================
st.subheader("📍 Statistik Tambahan")

st.write({
    "mean_temp": float(np.mean(ctt)),
    "min_temp": float(np.min(ctt)),
    "max_temp": float(np.max(ctt)),
    "cb_pixel_count": int(np.sum(cb_mask))
})
