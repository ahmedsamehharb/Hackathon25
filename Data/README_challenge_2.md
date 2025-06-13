# Challenge 2: Politische Heatmap – Problemvisualisierung mit Filterfunktion

## Task
Build an interactive map (e.g., with Google Maps) that spatially displays citizen concerns. Implement meaningful filter options – e.g., by submission date, gender of submitters, problem category, or region.

## Goal
A clickable map dashboard that allows politicians to visually analyze citizen concerns, recognize trends, and zoom into specific areas or topics.

## Data Structure

All data for this challenge is in `../data/challenge_2/`:

### Available Files

1. **`complete_issues_data.csv`** - All citizen issues with full details
   - Contains every issue with timestamps, locations, categories, and demographics
   - Use this for maximum flexibility in filtering and visualization

2. **`daily_aggregated.csv`** - Pre-aggregated by day and location
   - Columns: date, latitude, longitude, category, municipality, district, state, issue_count
   - Useful for time-series visualizations

3. **`weekly_aggregated.csv`** - Pre-aggregated by week
   - Similar structure, aggregated by calendar week

4. **`monthly_aggregated.csv`** - Pre-aggregated by month
   - Similar structure, aggregated by month

### Key Fields in Complete Dataset
- **Location**: `latitude`, `longitude`, `municipality`, `district`, `state`
- **Time**: `timestamp` (datetime), plus derived fields like `hour`, `day_of_week`
- **Category**: `category` (Verkehr, Bildung, Umwelt, etc.)
- **Demographics**: `age_group`, `gender`, `origin`
- **Issue Details**: `issue_id`, `description` (German text)

## 🗺️ IMPORTANT: Use Administrative Boundaries for Professional Visualizations

To create professional, accurate political heatmaps, **we strongly encourage you to use the official German administrative boundaries** provided in the geodata folder. These shapefiles contain exact borders for all German states, districts, and municipalities.

### Available Geodata Files

German administrative boundaries are available in:
- `../public_data/vg5000_12-31.gk3.shape.ebenen/vg5000_ebenen_1231/`
  - `VG5000_LAN.shp` - Federal states (Bundesländer) - 16 states
  - `VG5000_KRS.shp` - Districts (Kreise) - 400+ districts
  - `VG5000_GEM.shp` - Municipalities (Gemeinden) - 11,000+ municipalities

### Why Use Administrative Boundaries?

1. **Professional Appearance**: Show data within actual political boundaries, not just as scattered points
2. **Aggregation by Region**: Calculate statistics per state/district/municipality
3. **Choropleth Maps**: Color regions by issue density or category dominance
4. **Political Context**: Politicians think in terms of their constituencies
5. **Accurate Representation**: Respect actual administrative divisions

### Example: Creating a Choropleth Map by State

```python
import geopandas as gpd
import pandas as pd
import folium

# Load issues data
issues_df = pd.read_csv('../data/challenge_2/complete_issues_data.csv')

# Load state boundaries and convert to web-friendly projection
states = gpd.read_file("../public_data/vg5000_12-31.gk3.shape.ebenen/vg5000_ebenen_1231/VG5000_LAN.shp")
states_wgs84 = states.to_crs("EPSG:4326")

# Count issues per state
issues_per_state = issues_df.groupby('state').size().reset_index(name='issue_count')

# Merge with geodata
states_with_data = states_wgs84.merge(issues_per_state, left_on='GEN', right_on='state', how='left')

# Create choropleth map
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

folium.Choropleth(
    geo_data=states_with_data.to_json(),
    name='Issues by State',
    data=states_with_data,
    columns=['GEN', 'issue_count'],
    key_on='feature.properties.GEN',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Issues'
).add_to(m)

# Add tooltips
folium.features.GeoJson(
    states_with_data,
    name='State Info',
    tooltip=folium.features.GeoJsonTooltip(
        fields=['GEN', 'issue_count'],
        aliases=['State:', 'Issues:'],
        localize=True
    )
).add_to(m)

m.save('germany_issues_choropleth.html')
```

### Advanced: Combine Points with Boundaries

```python
# Create base map with state boundaries
m = folium.Map(location=[51.0, 10.0], zoom_start=6)

# Add state boundaries as base layer
folium.GeoJson(
    states_wgs84.to_json(),
    style_function=lambda x: {
        'fillColor': 'lightblue',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.1
    }
).add_to(m)

# Add individual issues as markers on top
marker_cluster = MarkerCluster().add_to(m)
for idx, row in issues_df.iterrows():
    folium.Marker(
        [row['latitude'], row['longitude']],
        popup=f"{row['category']}: {row['description'][:50]}..."
    ).add_to(marker_cluster)
```

### Tips for Using Geodata

1. **Performance**: Simplify geometries for web use: `geometry.simplify(0.01)`
2. **Projection**: Always convert to WGS84 (EPSG:4326) for web maps
3. **File Size**: Consider converting large shapefiles to GeoJSON or TopoJSON
4. **Matching**: The 'GEN' field in shapefiles contains the region name
5. **Hierarchy**: Start with states (LAN), then drill down to districts (KRS) or municipalities (GEM)

## Evaluation Criteria
- **Intuitive visualization** - Is it easy to understand the data at a glance?
- **Meaningful filters** - Can users explore different aspects of the data?
- **Performance** - Does it handle the full dataset smoothly?
- **Insights** - Does it help identify patterns and trends?
- **Design** - Is it visually appealing and professional?

## Tips
- Start with the pre-aggregated files for quick prototypes
- Use the complete dataset for advanced filtering by demographics
- Consider clustering for better performance with many points
- Add time animation to show trends over time
- Use color coding to distinguish categories
- Include summary statistics alongside the map
- Test with different zoom levels and regions
- Consider mobile responsiveness for politicians on the go

## Libraries and Tools
- **Python**: folium, plotly, streamlit, geopandas
- **JavaScript**: Leaflet, Mapbox GL JS, D3.js
- **Low-code**: Tableau, Power BI, Google Data Studio