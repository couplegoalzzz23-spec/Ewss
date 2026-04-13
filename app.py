import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.title("🌩️ Early Warning System - Himawari")

# Load data
gdf = gpd.read_file("riau_warning.geojson")

# Map
m = folium.Map(location=[0, 102], zoom_start=6)

folium.GeoJson(
    gdf,
    style_function=lambda x: {
        'fillColor': 'red' if x['properties']['status']=="EKSTREM"
                     else 'orange' if x['properties']['status']=="WASPADA"
                     else 'green',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['KECAMATAN', 'temperature', 'status']
    )
).add_to(m)

st_folium(m, width=700, height=500)
