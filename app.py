import streamlit as st
import numpy as np
import requests
import cv2
from PIL import Image
import matplotlib.pyplot as plt

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(page_title="Himawari IR EWS", layout="wide")

st.title("🛰️ Himawari IR Real Decoder - Early Warning System")
st.caption("Menggunakan citra IR Enhanced BMKG untuk estimasi potensi cuaca ekstrem")

# =========================
# 🌐 AMBIL GAMBAR BMKG
# =========================
@st.cache_data
def load_image():
    # BMKG IR Enhanced (latest image endpoint biasanya berubah-ubah)
    url = "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/thumbnail_AHI88_IR1.png"

    response = requests.get(url, timeout=10)
    img = Image.open(BytesIO(response.content)).convert("L")
    return np.array(img)

# fallback safer method
def load_image_safe():
    url = "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/thumbnail_AHI88_IR1.png"
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("L")
        return np.array(img), None
    except Exception as e:
        return None, str(e)

from io import BytesIO

img, error = load_image_safe()

if error:
    st.error("Gagal mengambil data BMKG. Menggunakan fallback demo image.")
    img = np.random.randint(0, 255, (500, 500))

# =========================
# 🌡️ KONVERSI PROXY SUHU
# =========================
def pixel_to_ctt(pixel):
    # IR grayscale → proxy temperature
    return -90 + (pixel / 255) * 100  # approx -90 to +10°C

ctt = pixel_to_ctt(img)

# =========================
# ⚡ DETEKSI KONVEKTIF
# =========================
def ews_index(ctt_value):
    # semakin dingin → semakin berbahaya
    if ctt_value < -70:
        return 0.9
    elif ctt_value < -60:
        return 0.75
    elif ctt_value < -40:
        return 0.55
    elif ctt_value < -20:
        return 0.30
    else:
        return 0.10

index = np.mean(ews_index(ctt))

# =========================
# 🚨 CLASSIFICATION
# =========================
def classify(i):
    if i < 0.3:
        return "🟢 Aman"
    elif i < 0.6:
        return "🟡 Waspada"
    elif i < 0.8:
        return "🟠 Siaga"
    else:
        return "🔴 Ekstrem"

status = classify(index)

# =========================
# 🗺️ DISPLAY
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛰️ Citra IR BMKG")
    st.image(img, use_container_width=True)

with col2:
    st.subheader("🌡️ Analisis Atmosfer")
    st.metric("EWS Index", f"{index:.2f}")
    st.metric("Status", status)

    st.write("### 📘 Interpretasi")
    if status == "🟢 Aman":
        st.write("Atmosfer stabil, tidak ada indikasi awan konvektif signifikan.")
    elif status == "🟡 Waspada":
        st.write("Mulai terbentuk awan hujan lokal.")
    elif status == "🟠 Siaga":
        st.write("Awan konvektif kuat, potensi hujan lebat.")
    else:
        st.write("⚠️ Cumulonimbus aktif, potensi hujan ekstrem & angin kencang.")

# =========================
# 📊 HISTOGRAM SUHU AWAN
# =========================
st.subheader("📊 Distribusi Estimasi Suhu Puncak Awan")

fig, ax = plt.subplots()
ax.hist(ctt.flatten(), bins=30)
ax.set_title("Cloud Top Temperature Proxy")
ax.set_xlabel("°C")
ax.set_ylabel("Pixel Count")

st.pyplot(fig)
