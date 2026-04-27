import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_geojson(path):
    gdf = gpd.read_file(path)
    gdf["community"] = gdf["community"].str.title()
    return gdf

st.title("Land Use Change Analysis (1990–2023)")

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

# Land use groups (exclude Total)
land_use_columns = [
    'Single Family Residential', 'Multi-Family Residential', 'Commercial',
    'Urban Mix with Residential Component', 'Institutional', 'Industrial',
    'TCU/Other', 'Agricultural', 'Open Space', 'Vacant',
    'Under Construction', 'Water'
]

# Sidebar controls
st.sidebar.header("Change Map Controls")
year_a = st.sidebar.selectbox("Select Start Year:", list(years.keys()), index=0)
year_b = st.sidebar.selectbox("Select End Year:", list(years.keys()), index=6)
selected_land_use = st.sidebar.selectbox("Select Land Use Category:", land_use_columns)

if year_a == year_b:
    st.warning("Please select two different years.")
    st.stop()

# Load both years
gdf_a = load_geojson(years[year_a])
gdf_b = load_geojson(years[year_b])

# Ensure numeric
for col in land_use_columns + ["Total"]:
    gdf_a[col] = pd.to_numeric(gdf_a[col], errors="coerce")
    gdf_b[col] = pd.to_numeric(gdf_b[col], errors="coerce")

# Fix geometries
gdf_a["geometry"] = gdf_a["geometry"].buffer(0)
gdf_b["geometry"] = gdf_b["geometry"].buffer(0)

# Merge on community area ID
merged = gdf_a[["area_numbe", "community", selected_land_use, "Total", "geometry"]].merge(
    gdf_b[["area_numbe", selected_land_use, "Total"]],
    on="area_numbe",
    suffixes=("_A", "_B")
)

# Compute percent values for each year
merged["pct_A"] = (merged[f"{selected_land_use}_A"] / merged["Total_A"]) * 100
merged["pct_B"] = (merged[f"{selected_land_use}_B"] / merged["Total_B"]) * 100

# Compute percent change
merged["pct_change"] = ((merged["pct_B"] - merged["pct_A"]) / merged["pct_A"]) * 100
merged["pct_change"] = merged["pct_change"].replace([float("inf"), -float("inf")], 0).fillna(0)

# -------------------------
# FORMAT VALUES WITH + SIGN
# -------------------------
merged["pct_A_fmt"] = merged["pct_A"].apply(lambda x: f"{x:.1f}%")
merged["pct_B_fmt"] = merged["pct_B"].apply(lambda x: f"{x:.1f}%")
merged["pct_change_fmt"] = merged["pct_change"].apply(
    lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%"
)

# Force symmetric color scale around 0
max_abs = merged["pct_change"].abs().max()
vmin, vmax = -max_abs, max_abs

# Map center
center_lat = merged.geometry.centroid.y.mean()
center_lon = merged.geometry.centroid.x.mean()

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=10, min_zoom=9,tiles="Cartodb.voyagernolabels")

# Diverging choropleth with 0 as critical break
folium.Choropleth(
    geo_data=merged.to_json(),
    data=merged,
    columns=["area_numbe", "pct_change"],
    key_on="properties.area_numbe",
    fill_color="RdYlBu",
    fill_opacity=0.8,
    line_opacity=0.2,
    nan_fill_color="white",
    legend_name=f"% Change in {selected_land_use} ({year_a} → {year_b})",
    threshold_scale=[vmin, vmin*0.75, vmin*0.5, vmin*0.25, 0, vmax*0.25, vmax*0.5, vmax*0.75, vmax]
).add_to(m)

# Tooltip & pop up
folium.GeoJson(
    merged,
    style_function=lambda x: {"fillOpacity": 0, "color": "black", "weight": 0.3},
    tooltip=folium.GeoJsonTooltip(
        fields=["community", "pct_A_fmt", "pct_B_fmt", "pct_change_fmt"],
        aliases=[
            "Community",
            f"{selected_land_use} % in " + year_a,
            f"{selected_land_use} % in " + year_b,
            "Percent Change"
        ],
        localize=True
    )
).add_to(m)



st_folium(m, width=700, height=500)