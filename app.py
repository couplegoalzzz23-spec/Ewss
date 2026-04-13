import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(page_title="CB Detection IR (Scientific Prototype)", layout="wide")

st.title("🌩️ Cumulonimbus Detection from Himawari IR")
st.caption("Scientific prototype based on cloud-top temperature proxy (NO RANDOM DATA)")

# =========================
# 🛰️ LOAD IMAGE BMKG
# =========================
@st.cache_data
def load_image():
    url = "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_IR/INA/thumbnail_AHI88_IR1.png"
    
    try:
        r = requests.get(url, timeout=10)
        img = Image.open(BytesIO(r.content)).convert("L")
        arr = np.array(img)

        # validasi sederhana
        if np.mean(arr) == 0:
            return None, "Empty image"

        return arr, None

    except Exception as e:
        return None, str(e)

img, error = load_image()

# =========================
# ❗ STOP jika data tidak valid
# =========================
if error or img is None:
    st.error("❌ Data satelit tidak tersedia atau tidak valid.")
    st.stop()

# =========================
# 🌡️ PROXY CLOUD TOP TEMPERATURE
# =========================
def pixel_to_ctt(pixel):
    # proxy saja (tidak diklaim real calibration)
    return -90 + (pixel / 255) * 100

ctt = pixel_to_ctt(img)

# =========================
# 🌩️ CB DETECTION (ROBUST SCIENTIFIC METHOD)
# =========================

# threshold berbasis percentile (lebih stabil dari fixed -70)
cold_threshold = np.percentile(ctt, 5)  # 5% terdingin dianggap cloud deep convection

cb_mask = ctt <= cold_threshold

coverage = np.sum(cb_mask) / cb_mask.size

if np.any(cb_mask):
    intensity = np.median(ctt[cb_mask])
else:
    intensity = None

# scoring ilmiah sederhana
score = coverage * 0.8

if intensity is not None:
    score += (abs(intensity) / 100) * 0.2

# =========================
# 🚨 CLASSIFICATION
# =========================
def classify(score):
    if score < 0.1:
        return "🟢 Low convective activity"
    elif score < 0.3:
        return "🟡 Developing convection"
    elif score < 0.6:
        return "🟠 Active convection (CB possible)"
    else:
        return "🔴 Strong deep convection (CB likely)"

status = classify(score)

# =========================
# 📊 DASHBOARD
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛰️ IR Satellite Image")
    st.image(img, use_container_width=True)

    st.subheader("🌩️ Cold Cloud Mask (Deep Convection)")
    st.image(cb_mask.astype(int) * 255, use_container_width=True)

with col2:
    st.subheader("📊 Analysis Result")

    st.metric("Convective Coverage", f"{coverage*100:.2f}%")
    st.metric("CB Score", f"{score:.3f}")
    st.metric("Status", status)

    if intensity is not None:
        st.metric("Median Cold Cloud Temp", f"{intensity:.2f} °C")

    st.write("### 🧠 Interpretation")
    st.write("""
    This system detects deep convective clouds (Cumulonimbus proxy)
    using cold cloud-top temperature distribution from IR satellite imagery.

    ⚠️ This is a scientific proxy model, not an operational BMKG product.
    """)

# =========================
# 📊 HISTOGRAM
# =========================
st.subheader("📊 Cloud Top Temperature Distribution")

fig, ax = plt.subplots()
ax.hist(ctt.flatten(), bins=30)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Pixel count")
ax.set_title("IR Cloud Top Temperature Proxy Distribution")

st.pyplot(fig)

# =========================
# 📌 DEBUG INFO
# =========================
st.subheader("📌 Diagnostics")

st.json({
    "mean_ctt": float(np.mean(ctt)),
    "min_ctt": float(np.min(ctt)),
    "max_ctt": float(np.max(ctt)),
    "cold_threshold_percentile": 5,
    "cb_pixel_fraction": float(coverage)
})
