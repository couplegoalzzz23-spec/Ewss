import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import os
import json

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="EWS Himawari", layout="wide")

st.title("🌩️ Early Warning System - Himawari")
st.markdown("Deteksi dini cuaca ekstrem berbasis suhu awan (TBB)")

# =========================
# PILIH MODE
# =========================
mode = st.radio("📡 Pilih Sumber Data:", ["Dummy", "Himawari Real"])

# =========================
# DUMMY DATA (AMAN)
# =========================
def load_dummy():
    file_path = "riau_warning.geojson"

    if not os.path.exists(file_path):
        dummy = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[100, -1], [104, -1], [104, 1], [100, 1], [100, -1]]]
                    },
                    "properties": {
                        "KECAMATAN": "Riau Dummy",
                        "temperature": -75,
                        "status": "EKSTREM"
                    }
                }
            ]
        }
        with open(file_path, "w") as f:
            json.dump(dummy, f)

    return gpd.read_file(file_path)

# =========================
# HIMAWARI REAL (ANTI ERROR)
# =========================
def load_himawari():
    import requests
    from PIL import Image
    import io
    from shapely.geometry import Polygon

    try:
        url = "https://www.bmkg.go.id/asset/img/satelit/himawari-ir-enhanced.jpg"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        # validasi response
        if response.status_code != 200:
            raise Exception("Status bukan 200")

        if "image" not in response.headers.get("Content-Type", ""):
            raise Exception("Bukan gambar")

        img = Image.open(io.BytesIO(response.content))

        # resize biar ringan
        img = img.resize((100, 100))
        arr = np.array(img)

        # konversi ke suhu (approx)
        tbb = (arr[:, :, 0] / 255.0) * (-30 - (-80)) + (-80)

        lat = np.linspace(-10, 10, tbb.shape[0])
        lon = np.linspace(95, 140, tbb.shape[1])

        polygons = []
        temps = []

        for i in range(len(lat)-1):
            for j in range(len(lon)-1):
                poly = Polygon([
                    (lon[j], lat[i]),
                    (lon[j], lat[i+1]),
                    (lon[j+1], lat[i+1]),
                    (lon[j+1], lat[i])
                ])

                polygons.append(poly)
                temps.append(tbb[i, j])

        df = pd.DataFrame({'temperature': temps, 'geometry': polygons})
        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

        return gdf

    except Exception as e:
        st.warning("⚠️ Data real gagal diambil, fallback ke dummy")
        return load_dummy()

# =========================
# CLASSIFICATION
# =========================
def classify(temp):
    if temp <= -70:
        return "EKSTREM"
    elif temp <= -60:
        return "WASPADA"
    else:
        return "AMAN"

# =========================
# LOAD DATA
# =========================
if mode == "Dummy":
    gdf = load_dummy()
else:
    gdf = load_himawari()

# pastikan kolom ada
if 'temperature' not in gdf.columns:
    st.error("❌ Data tidak valid")
    st.stop()

gdf['status'] = gdf['temperature'].apply(classify)

# =========================
# DASHBOARD
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("Total Grid", len(gdf))
col2.metric("Ekstrem", len(gdf[gdf['status']=="EKSTREM"]))
col3.metric("Waspada", len(gdf[gdf['status']=="WASPADA"]))

# =========================
# WARNA
# =========================
def get_color(status):
    if status == "EKSTREM":
        return "red"
    elif status == "WASPADA":
        return "orange"
    else:
        return "green"

# =========================
# PETA
# =========================
st.subheader("🗺️ Peta Early Warning")

m = folium.Map(location=[0, 102], zoom_start=5)

folium.GeoJson(
    gdf,
    style_function=lambda x: {
        'fillColor': get_color(x['properties'].get('status', 'AMAN')),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['temperature', 'status'],
        aliases=['Suhu (°C):', 'Status:']
    )
).add_to(m)

st_folium(m, width=1000, height=600)

# =========================
# LEGEND
# =========================
st.markdown("""
### Keterangan:
- 🔴 EKSTREM (≤ -70°C)
- 🟠 WASPADA (≤ -60°C)
- 🟢 AMAN (> -60°C)
""")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("📡 Data: Himawari-8 | Mode real berbasis citra BMKG (fallback otomatis)")
