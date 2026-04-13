import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
import json

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="EWS Himawari", layout="wide")

st.title("🌩️ Early Warning System - Himawari")

# =========================
# LOAD / HANDLE FILE
# =========================
file_path = "riau_warning.geojson"

# kalau file tidak ada → buat dummy
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

# =========================
# READ DATA
# =========================
try:
    gdf = gpd.read_file(file_path)
except Exception as e:
    st.error("❌ Gagal membaca GeoJSON")
    st.write(e)
    st.stop()

# =========================
# INFO DATA
# =========================
st.subheader("📊 Informasi Data")
st.write("Jumlah wilayah:", len(gdf))

# =========================
# FUNGSI WARNA
# =========================
def get_color(status):
    if status == "EKSTREM":
        return "red"
    elif status == "WASPADA":
        return "orange"
    else:
        return "green"

# =========================
# BUAT PETA
# =========================
st.subheader("🗺️ Peta Early Warning")

m = folium.Map(location=[0, 102], zoom_start=6)

folium.GeoJson(
    gdf,
    style_function=lambda x: {
        'fillColor': get_color(x['properties'].get('status', 'AMAN')),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['KECAMATAN', 'temperature', 'status'],
        aliases=['Kecamatan:', 'Suhu (°C):', 'Status:']
    )
).add_to(m)

# =========================
# TAMPILKAN PETA (FIX)
# =========================
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
st.caption("📡 Data: Himawari (Simulasi / Dummy)")
