import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# =========================
# ⚙️ CONFIG SAFE MODE
# =========================
st.set_page_config(
    page_title="Himawari CB Detection (Stable)",
    layout="wide"
)

st.title("🌩️ Cumulonimbus Detection System (Production Stable)")
st.caption("Safe-mode satellite IR analysis (no fake data, no crash system)")

# =========================
# 🛰️ SAFE IMAGE LOADER (ANTI ERROR TOTAL)
# =========================
def load_satellite_image():
    urls = [
        "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/thumbnail_AHI88_IR1.png",
        "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/latest.jpg"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=8)

            if r.status_code != 200:
                continue

            img = Image.open(BytesIO(r.content)).convert("L")
            arr = np.array(img)

            # validasi isi gambar
            if arr is None or arr.size == 0:
                continue

            if np.mean(arr) < 1:
                continue

            return arr, url

        except Exception:
            continue

    return None, None


img, source_url = load_satellite_image()

# =========================
# 🚨 SAFE HANDLING (NO CRASH)
# =========================
if img is None:
    st.error("❌ Tidak dapat mengambil data satelit saat ini.")
    st.info("""
    Kemungkinan penyebab:
    - Server BMKG sedang tidak merespons
    - Koneksi internet dibatasi (Streamlit Cloud)
    - Endpoint satelit berubah

    👉 Sistem tetap aman (tidak menggunakan data palsu)
    """)
    st.stop()

# =========================
# 🌡️ PROXY CLOUD TOP TEMP
# =========================
def pixel_to_temp(pixel):
    return -90 + (pixel / 255) * 100

ctt = pixel_to_temp(img)

# =========================
# 🌩️ CB DETECTION (ROBUST METHOD)
# =========================
def detect_cb(ctt_array):

    cold_threshold = np.percentile(ctt_array, 5)

    cb_mask = ctt_array <= cold_threshold

    coverage = np.sum(cb_mask) / cb_mask.size

    if np.any(cb_mask):
        intensity = np.median(ctt_array[cb_mask])
    else:
        intensity = None

    score = coverage * 0.8

    if intensity is not None:
        score += (abs(intensity) / 100) * 0.2

    return cb_mask, coverage, intensity, score, cold_threshold


cb_mask, coverage, intensity, score, threshold = detect_cb(ctt)

# =========================
# 🚨 CLASSIFICATION
# =========================
def classify(score):
    if score < 0.1:
        return "🟢 Low convection"
    elif score < 0.3:
        return "🟡 Developing"
    elif score < 0.6:
        return "🟠 Active CB possible"
    else:
        return "🔴 Strong CB / Severe convection"

status = classify(score)

# =========================
# 📊 DASHBOARD
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛰️ Satellite IR Image")
    st.image(img, use_container_width=True)
    st.caption(f"Source: {source_url}")

    st.subheader("🌩️ Cold Cloud Mask (CB)")
    st.image(cb_mask.astype(np.uint8) * 255, use_container_width=True)

with col2:
    st.subheader("📊 Analysis Result")

    st.metric("CB Score", f"{score:.3f}")
    st.metric("Coverage", f"{coverage*100:.2f}%")
    st.metric("Threshold (°C)", f"{threshold:.2f}")
    st.metric("Status", status)

    if intensity is not None:
        st.metric("Median Cold Cloud Temp", f"{intensity:.2f} °C")

    st.write("### 🧠 System Explanation")
    st.write("""
    Sistem ini mendeteksi potensi Cumulonimbus berdasarkan:
    - Distribusi suhu puncak awan terdingin (percentile 5%)
    - Luas area awan dingin (cold cloud coverage)
    - Intensitas suhu awan konvektif

    ⚠️ Ini adalah scientific proxy model (bukan produk operasional BMKG).
    """)

# =========================
# 📊 DISTRIBUTION
# =========================
st.subheader("📊 Cloud Temperature Distribution")

fig, ax = plt.subplots()
ax.hist(ctt.flatten(), bins=30)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Pixel Count")
ax.set_title("IR Cloud Top Temperature Distribution")

st.pyplot(fig)

# =========================
# 📌 DIAGNOSTIC PANEL
# =========================
with st.expander("🔍 System Diagnostics"):
    st.json({
        "mean_ctt": float(np.mean(ctt)),
        "min_ctt": float(np.min(ctt)),
        "max_ctt": float(np.max(ctt)),
        "cold_threshold_percentile": 5,
        "cb_pixel_fraction": float(coverage),
        "image_shape": list(img.shape)
    })
