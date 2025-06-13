import geopandas as gpd
import pandas as pd
import folium

# Load data
issues_df = pd.read_csv('Data/complete_issues_data.csv')
states = gpd.read_file("Data/VG5000_LAN.shp")
states_wgs84 = states.to_crs("EPSG:4326")

# Count issues per state
issues_per_state = issues_df.groupby('state').size().reset_index(name='issue_count')

# Merge geodata with issues count
states_with_data = states_wgs84.merge(issues_per_state, left_on='GEN', right_on='state', how='left')

# Convert datetime columns to strings (if any)
for col in states_with_data.columns:
    if pd.api.types.is_datetime64_any_dtype(states_with_data[col]):
        states_with_data[col] = states_with_data[col].astype(str)

# Convert GeoDataFrame to GeoJSON string for folium
geojson_str = states_with_data.to_json()

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

# Add GeoJson layer with tooltip (pass geojson string, NOT the GeoDataFrame)
folium.GeoJson(
    geojson_str,
    name='State Info',
    tooltip=folium.GeoJsonTooltip(
        fields=['GEN', 'issue_count'],
        aliases=['State:', 'Issues:'],
        localize=True
    )
).add_to(m)

# Save to file
m.save('germany_issues_choropleth.html')
