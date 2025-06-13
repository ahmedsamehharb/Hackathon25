import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

# --- Set page config ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# --- Load data ---
issues_df = pd.read_csv('Data/complete_issues_data.csv')
states = gpd.read_file("Data/VG5000_LAN.shp").to_crs("EPSG:4326")

# --- Preprocessing ---
issues_df['date'] = pd.to_datetime(issues_df['date'], errors='coerce')
states.columns = states.columns.str.strip()

# --- Sidebar filters ---
st.sidebar.header("Filter Complaints")
date_range = st.sidebar.date_input("Date range", [])
category = st.sidebar.multiselect("Category", issues_df['category'].unique())
age_group = st.sidebar.multiselect("Age Group", issues_df['age_group'].unique())
gender = st.sidebar.multiselect("Gender", issues_df['gender'].unique())
origin = st.sidebar.multiselect("Origin", issues_df['origin'].unique())
state = st.sidebar.multiselect("State", issues_df['state'].unique())
entity_level = st.sidebar.multiselect("Entity Level", issues_df['responsible_entity_level'].unique())
search_municipality = st.sidebar.text_input("Search Municipality or District")

show_markers = st.sidebar.checkbox("Show Markers", value=True)
heatmap_level = st.sidebar.selectbox("Heatmap Granularity", ["State", "District", "Municipality"])

# --- Filter data ---
filtered = issues_df.copy()
if date_range:
    filtered = filtered[(filtered['date'] >= pd.to_datetime(date_range[0])) & (filtered['date'] <= pd.to_datetime(date_range[-1]))]
if category:
    filtered = filtered[filtered['category'].isin(category)]
if age_group:
    filtered = filtered[filtered['age_group'].isin(age_group)]
if gender:
    filtered = filtered[filtered['gender'].isin(gender)]
if origin:
    filtered = filtered[filtered['origin'].isin(origin)]
if state:
    filtered = filtered[filtered['state'].isin(state)]
if entity_level:
    filtered = filtered[filtered['responsible_entity_level'].isin(entity_level)]
if search_municipality:
    filtered = filtered[
        filtered['municipality'].str.contains(search_municipality, case=False, na=False) |
        filtered['district'].str.contains(search_municipality, case=False, na=False)
    ]

# --- Prepare map ---
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

if heatmap_level == "State":
    level_column = 'state'
elif heatmap_level == "District":
    level_column = 'district'
else:
    level_column = 'municipality'

counts = filtered.groupby(level_column).size().reset_index(name='count')

gdf = states.copy()
gdf = gdf.merge(counts, left_on='GEN', right_on=level_column, how='left')
gdf['count'] = gdf['count'].fillna(0)
gdf = gdf[['GEN', 'count', 'geometry']]

folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=['GEN', 'count'],
    key_on='feature.properties.GEN',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f"Complaints per {heatmap_level}",
    nan_fill_color='white',
).add_to(m)

def make_popup_html(row):
    cat_color = {
        'Category1': '#e74c3c',
        'Category2': '#f39c12',
        'Category3': '#27ae60',
    }
    color = cat_color.get(row['category'], '#3498db')
    html = f"""
    <div style="font-family: Arial; font-size: 12px;">
      <strong style="font-size:14px">{row['category']}</strong> 
      <span style="background-color:{color}; color:white; padding:2px 6px; border-radius:4px; margin-left:8px;">
        {row['date'].date()}
      </span><br>
      <em>{row['municipality'] if pd.notna(row['municipality']) else ''}</em><br>
      <p style="margin-top:5px;">{row['description'][:100]}...</p>
    </div>
    """
    return html

if show_markers:
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in filtered.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            popup_html = make_popup_html(row)
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(marker_cluster)

# --- Show map ---
folium_static(m, width=1400, height=800)

# --- Municipality stats ---
if search_municipality:
    st.subheader(f"Statistics for: {search_municipality}")
    muni_df = filtered[
        filtered['municipality'].str.contains(search_municipality, case=False, na=False) |
        filtered['district'].str.contains(search_municipality, case=False, na=False)
    ]
    st.write(f"Total complaints: {len(muni_df)}")
    st.write("Breakdown by category:")
    st.write(muni_df['category'].value_counts())
