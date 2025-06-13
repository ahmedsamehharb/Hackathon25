import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# Load issues data
issues_df = pd.read_csv('Data/complete_issues_data.csv')

# Load and reproject shapefile to WGS84 for web mapping
states = gpd.read_file("Data/VG5000_LAN.shp")
states_wgs84 = states.to_crs("EPSG:4326")

# Count issues per state
issues_per_state = issues_df.groupby('state').size().reset_index(name='issue_count')

# Merge issues data with geodata
states_with_data = states_wgs84.merge(issues_per_state, left_on='GEN', right_on='state', how='left')

# Convert datetime columns in merged GeoDataFrame to strings
for col in states_with_data.columns:
    if pd.api.types.is_datetime64_any_dtype(states_with_data[col]):
        states_with_data[col] = states_with_data[col].astype(str)

# Convert to GeoJSON
geojson_str = states_with_data.to_json()

# --- Choropleth map with issues per state ---

# Create folium map
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

# Add choropleth layer
folium.Choropleth(
    geo_data=geojson_str,
    name='Issues by State',
    data=states_with_data,
    columns=['GEN', 'issue_count'],
    key_on='feature.properties.GEN',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Issues'
).add_to(m)

# Add tooltip layer
folium.GeoJson(
    geojson_str,
    name='State Info',
    tooltip=folium.GeoJsonTooltip(
        fields=['GEN', 'issue_count'],
        aliases=['State:', 'Issues:'],
        localize=True
    )
).add_to(m)

# Save first map
m.save('germany_issues_choropleth.html')

# --- Marker map with state boundaries and issue markers ---

# Create a new map
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

# Convert datetime columns in states_wgs84 to strings (if any)
for col in states_wgs84.columns:
    if pd.api.types.is_datetime64_any_dtype(states_wgs84[col]):
        states_wgs84[col] = states_wgs84[col].astype(str)

# Add state boundaries as GeoJson
folium.GeoJson(
    states_wgs84.to_json(),
    style_function=lambda x: {
        'fillColor': 'lightblue',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.1
    }
).add_to(m)

# Add clustered issue markers
marker_cluster = MarkerCluster().add_to(m)
for idx, row in issues_df.iterrows():
    folium.Marker(
        [row['latitude'], row['longitude']],
        popup=f"{row['category']}: {row['description'][:50]}..."
    ).add_to(marker_cluster)

# Save second map
m.save('germany_issues_markers.html')
