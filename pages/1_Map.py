import streamlit as st
import geopandas as gpd
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd

@st.cache_data
def load_geojson(path):
    gdf = gpd.read_file(path)
    gdf["community"] = gdf["community"].str.title()
    return gdf


# Available years
years = {
    '1990': 'GeoJSONs/LUI1990g.geojson',
    '2001': 'GeoJSONs/LUI2001g.geojson',
    '2005': 'GeoJSONs/LUI2005g.geojson',
    '2010': 'GeoJSONs/LUI2010g.geojson',
    '2015': 'GeoJSONs/LUI2015g.geojson',
    '2020': 'GeoJSONs/LUI2020g.geojson',
    '2023': 'GeoJSONs/LUI2023g.geojson',
}

# Sidebar controls
st.sidebar.header("Map Controls")
selected_year = st.sidebar.selectbox("Select Year:", list(years.keys()))

# Load data
gdf = load_geojson(years[selected_year])

# Ensure numeric types for all land use columns
land_use_columns = [
    'Single Family Residential', 'Multi-Family Residential', 'Commercial',
    'Urban Mix with Residential Component', 'Institutional', 'Industrial',
    'TCU/Other', 'Agricultural', 'Open Space', 'Vacant',
    'Under Construction', 'Water', 'Total'
]

for col in land_use_columns:
    gdf[col] = pd.to_numeric(gdf[col], errors='coerce')

# Sidebar land use selector
selected_land_use = st.sidebar.selectbox("Select Land Use Group:", land_use_columns[:-1])  # exclude Total

# Compute percentage
gdf["percent_land_use"] = (gdf[selected_land_use] / gdf["Total"]) * 100
gdf["percent_land_use"] = gdf["percent_land_use"].fillna(0)

# App title and header
st.header(f"Percentage of {selected_land_use} parcels by Community Area in {selected_year}")

# Fix invalid geometries before centroids
gdf["geometry"] = gdf["geometry"].buffer(0)

# Create map
center_lat = gdf.geometry.centroid.y.mean()
center_lon = gdf.geometry.centroid.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=10, min_zoom=9, tiles='Cartodb.voyagernolabels')

# Add choropleth (percentage map)
folium.Choropleth(
    geo_data=gdf.to_json(),
    data=gdf,
    columns=['area_numbe', 'percent_land_use'],
    key_on='properties.area_numbe',
    fill_color='PuBuGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f"{selected_land_use} (% of total land use)",
    nan_fill_color='white'
).add_to(m)

# Add hover tooltip
folium.GeoJson(
    gdf,
    style_function=lambda feature: {
        'fillOpacity': 0,
        'color': 'black',
        'weight': 0.3   # <-- thinner outlines
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['community', 'percent_land_use'],
        aliases=['Community', f'{selected_land_use} (%)'],
        localize=True
    )
).add_to(m)

st_folium(m, width=700, height=500)
