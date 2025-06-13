import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

# --- Helper function to stringify datetime columns for GeoJSON compatibility ---
def stringify_datetime_columns(gdf):
    for col, dtype in gdf.dtypes.items():
        if pd.api.types.is_datetime64_any_dtype(dtype):
            gdf[col] = gdf[col].astype(str)
    return gdf

# --- Function to add issue counts to GeoDataFrame ---
def add_issue_counts(gdf, join_col, group_col, issues):
    issues_group = issues.groupby(group_col).size().reset_index(name='issue_count')
    gdf = gdf.merge(issues_group, left_on=join_col, right_on=group_col, how='left')
    gdf['issue_count'] = gdf['issue_count'].fillna(0)
    return stringify_datetime_columns(gdf)

# --- Function to add choropleth + tooltip layers ---
def add_choropleth_with_tooltip(m, gdf, name, geojson_key, tooltip_fields, tooltip_aliases, color, legend):
    folium.Choropleth(
        geo_data=gdf.to_json(),
        name=name,
        data=gdf,
        columns=[geojson_key, 'issue_count'],
        key_on=f'feature.properties.{geojson_key}',
        fill_color=color,
        fill_opacity=0.7,
        line_opacity=0.7,
        line_color='black',  # Set border color to black
        legend_name=legend,
        overlay=True,
        control=True
    ).add_to(m)

    folium.GeoJson(
        gdf.to_json(),
        name=f'{name} Info',
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases, localize=True),
        style_function=lambda feature: {
            'color': 'black',  # Set border color to black
            'weight': 1,
            'fillOpacity': 0
        }
    ).add_to(m)

# --- Set page config ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# --- Load custom CSS ---


# --- Load data ---
issues_df = pd.read_csv('Data/complete_issues_data.csv')
issues_df['date'] = pd.to_datetime(issues_df['date'], errors='coerce')
issues_df['municipality_norm'] = issues_df['municipality'].str.lower().str.strip()

states = gpd.read_file("Data/VG5000_LAN.shp").to_crs("EPSG:4326")
districts = gpd.read_file("Data/VG5000_KRS.shp").to_crs("EPSG:4326")
municipalities = gpd.read_file("Data/VG5000_GEM.shp").to_crs("EPSG:4326")
municipalities['GEN_norm'] = municipalities['GEN'].str.lower().str.strip()

# --- Sidebar filters ---
st.sidebar.header("Filter Complaints")
view_level = st.sidebar.radio("Heatmap Granularity", options=["State", "District", "Municipality"])
date_range = st.sidebar.date_input("Date range", [])

# Create category options with icons
category_options = {
    'Umwelt': '🗑️',
    'Bildung': '🏫',
    'Verkehr': '🚗',
    'Digitalisierung': '💻',
    'Sicherheit': '🔒',
    'Gesundheit': '🏥',
    'Wirtschaft': '💼',
    'Migration': '🛂'
}
category = st.sidebar.multiselect(
    "Category",
    options=list(category_options.keys()),
    format_func=lambda x: f"{category_options[x]} {x}"
)

age_group = st.sidebar.multiselect("Age Group", issues_df['age_group'].unique())
gender = st.sidebar.multiselect("Gender", issues_df['gender'].unique())
origin = st.sidebar.multiselect("Origin", issues_df['origin'].unique())
state = st.sidebar.multiselect("State", issues_df['state'].unique())
entity_level = st.sidebar.multiselect("Entity Level", issues_df['responsible_entity_level'].unique())
show_markers = st.sidebar.checkbox("Show Markers", value=True)

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

# --- Prepare map ---
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

# --- Add issue counts to shapefiles ---
states_with_data = add_issue_counts(states, "GEN", "state", filtered)
districts_with_data = add_issue_counts(districts, "GEN", "district", filtered)
issues_per_municipality = filtered.groupby('municipality_norm').size().reset_index(name='issue_count')
municipalities_with_data = municipalities.merge(
    issues_per_municipality,
    left_on='GEN_norm',
    right_on='municipality_norm',
    how='left'
)
municipalities_with_data['issue_count'] = municipalities_with_data['issue_count'].fillna(0)
municipalities_with_data = stringify_datetime_columns(municipalities_with_data)

# --- Add choropleth based on selected view ---
if view_level == "State":
    add_choropleth_with_tooltip(
        m, states_with_data, "States", "GEN",
        ['GEN', 'issue_count'], ['State:', 'Issues:'],
        'YlOrRd', 'Number of Issues (States)'
    )
elif view_level == "District":
    add_choropleth_with_tooltip(
        m, districts_with_data, "Districts", "GEN",
        ['GEN', 'issue_count'], ['District:', 'Issues:'],
        'YlOrRd', 'Number of Issues (Districts)'
    )
elif view_level == "Municipality":
    add_choropleth_with_tooltip(
        m, municipalities_with_data, "Municipalities", "GEN_norm",
        ['GEN', 'issue_count'], ['Municipality:', 'Issues:'],
        'YlOrRd', 'Number of Issues (Municipalities)'
    )

# --- Marker Popups ---
# Define category colors globally
CATEGORY_COLORS = {
    'Category1': '#e74c3c',
    'Category2': '#f39c12',
    'Category3': '#27ae60',
}

def get_category_icon(category):
    # Map categories to Font Awesome icons based on actual issue types
    icon_mapping = {
        'Umwelt': 'trash',           # Trash icon for environmental issues
        'Bildung': 'school',         # School icon for education issues
        'Verkehr': 'car',           # Car icon for traffic/transportation issues
        'Digitalisierung': 'laptop', # Laptop icon for digital/online issues
        'Sicherheit': 'lock',   # Lightbulb icon for safety/lighting issues
        'Gesundheit': 'hospital',    # Hospital icon for health issues
        'Wirtschaft': 'briefcase',   # Briefcase icon for business/economic issues
        'Migration': 'passport',     # Passport icon for migration issues
    }
    # Default to a standard marker if category not found
    return icon_mapping.get(category, 'map-marker')

def make_popup_html(row):
    color = CATEGORY_COLORS.get(row['category'], '#3498db')
    html = f"""
    <div style="font-family: Arial; font-size: 12px;">
      <strong style="font-size:14px">{row['category']}</strong> 
      <span style="background-color:{color}; color:white; padding:2px 6px; border-radius:4px; margin-left:8px;">
        {row['date'].date()}
      </span><br>
      <em>{row['municipality'] if pd.notna(row['municipality']) else ''}</em><br>
      <p style="margin-top:5px;">{row['description']}</p>
    </div>
    """
    return html

# --- Show markers if enabled ---
if show_markers:
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in filtered.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            popup_html = make_popup_html(row)
            icon_name = get_category_icon(row['category'])
            icon = folium.Icon(
                icon=icon_name,
                color=CATEGORY_COLORS.get(row['category'], 'blue'),
                prefix='fa'
            )
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=icon
            ).add_to(marker_cluster)

# --- Show map ---
folium_static(m, width=1400, height=800)