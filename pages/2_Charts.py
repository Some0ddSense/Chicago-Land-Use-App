import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import altair as alt

@st.cache_data
def load_geojson(path):
    gdf = gpd.read_file(path)
    gdf["community"] = gdf["community"].str.title()
    return gdf


# Year selection only
years = {
    '1990': 'GeoJSONs/LUI1990g.geojson',
    '2001': 'GeoJSONs/LUI2001g.geojson',
    '2005': 'GeoJSONs/LUI2005g.geojson',
    '2010': 'GeoJSONs/LUI2010g.geojson',
    '2015': 'GeoJSONs/LUI2015g.geojson',
    '2020': 'GeoJSONs/LUI2020g.geojson',
    '2023': 'GeoJSONs/LUI2023g.geojson',
}

selected_year = st.sidebar.selectbox("Select Year:", list(years.keys()))
gdf = load_geojson(years[selected_year])

# Land use groups
land_use_columns = [
    'Single Family Residential', 'Multi-Family Residential', 'Commercial',
    'Urban Mix with Residential Component', 'Institutional', 'Industrial',
    'TCU/Other', 'Agricultural', 'Open Space', 'Vacant',
    'Under Construction', 'Water',
]

# -------------------------
# COMMUNITY AREA DROPDOWN
# -------------------------
areas = ["Total"] + sorted(gdf["community"].unique().tolist())
selected_area = st.sidebar.selectbox("Select Community Area:", areas)

# -------------------------
# FILTER DATA FOR BAR + DONUT
# -------------------------
if selected_area == "Total":
    totals = gdf[land_use_columns].sum().sort_values(ascending=False)
else:
    row = gdf[gdf["community"] == selected_area].iloc[0]
    totals = row[land_use_columns].sort_values(ascending=False)

percentages = (totals / totals.sum()) * 100

# -------------------------
# BAR CHART
# -------------------------
st.subheader(f"Land Use Percentage (%) Distribution in {selected_year} — {selected_area}")

fig1, ax1 = plt.subplots(figsize=(10, 6))
percentages.plot(kind='bar', ax=ax1, color='skyblue')
ax1.set_ylabel("Percentage of Total Land Use (%)")
ax1.set_title(f"Land Use Percentages in {selected_area} ({selected_year})")
ax1.set_ylim(0, percentages.max() * 1.15)

for i, v in enumerate(percentages):
    ax1.text(i, v + 0.5, f"{v:.1f}%", ha='center', fontsize=9)

plt.xticks(rotation=45, ha='right')
st.pyplot(fig1)

# -------------------------
# DONUT CHART
# -------------------------
st.subheader("Percentage Breakdown")

fig2, ax2 = plt.subplots(figsize=(8, 8))
colors = cm.get_cmap('tab20')(np.linspace(0, 1, len(totals)))

wedges, _ = ax2.pie(
    totals,
    startangle=90,
    wedgeprops=dict(width=0.4),
    colors=colors
)

labels_with_pct = [
    f"{label}: {pct:.1f}%" for label, pct in zip(totals.index, percentages)
]

ax2.legend(
    wedges,
    labels_with_pct,
    title="Land Use Types",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    fontsize=10
)

centre_circle = plt.Circle((0, 0), 0.60, fc='white')
fig2.gca().add_artist(centre_circle)

ax2.set_ylabel("")
plt.tight_layout()
st.pyplot(fig2)

# -------------------------
# MULTI-YEAR TREND CHART
# -------------------------
st.subheader(f"Multi-Year Trend — {selected_area}")

# Dropdown for land-use category
selected_lu = st.selectbox("Select Land Use Category for Trend:", land_use_columns)

# Build trend dataset
trend_records = []

for yr, path in years.items():
    gdf_year = load_geojson(path)

    if selected_area == "Total":
        totals_year = gdf_year[land_use_columns].sum()
    else:
        row_year = gdf_year[gdf_year["community"] == selected_area].iloc[0]
        totals_year = row_year[land_use_columns]

    pct_year = (totals_year / totals_year.sum()) * 100

    trend_records.append({
        "Year": int(yr),
        "Percent": pct_year[selected_lu]
    })

trend_df = pd.DataFrame(trend_records)

# Line chart
line_chart = alt.Chart(trend_df).mark_line(point=True).encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("Percent:Q", title=f"{selected_lu} (%)"),
    tooltip=["Year", "Percent"]
).properties(
    width=800,
    height=400,
    title=f"{selected_lu} Trend Over Time — {selected_area}"
)

st.altair_chart(line_chart, use_container_width=True)
