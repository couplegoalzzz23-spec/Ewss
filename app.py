import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
import json

st.set_page_config(page_title="EWS Himawari", layout="wide")

st.title("🌩️ Early Warning System - Himawari")

# =========================
# DEBUG: cek isi folder
# =========================
st.write("📂 Isi folder:", os.listdir())

# =========================
# LOAD GEOJSON (AMAN)
# =========================
file_path = "riau_warning.geojson"

# kalau file tidak ada → buat dummy otomatis
if not os.path.exists(file_path):
    st.warning("⚠️ File tidak ditemukan, membuat data dummy...")

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
# BACA DATA
# =========================
try:
    gdf = gpd.read_file(file_path)
    st.success("✅ Data berhasil dimuat")

except Exception as e:
    st.error("❌ Gagal membaca file")
    st.write(e)
    st.stop()

# =========================
# BUAT PETA
# =========================
m = folium.Map(location=[0, 102], zoom_start=6)

def get_color(status):
    if status == "EKSTREM":
        return "red"
    elif status == "WASPADA":
        return "orange"
    else:
        return "green"

folium.GeoJson(
    gdf,
    style_function=lambda x: {
        'fillColor': get_color(x['properties']['status']),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['KECAMATAN', 'temperature', 'status'],
        aliases=['Kecamatan:', 'Suhu:', 'Status:']
    )
).add_to(m)

# =========================
# TAMPILKAN
# =========================
st_folium(m, width=900, height=500)

st.markdown("---")
st.markdown("📡 Data: Himawari (simulasi)")
st.markdown("⚠️ Status berdasarkan suhu awan (TBB)")
