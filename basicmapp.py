import folium

# Create a map centered on Germany
m = folium.Map(location=[51.1657, 10.4515], zoom_start=6)
folium.Marker(
    location=[52.52, 13.405],  # Berlin
    popup="Berlin",
    icon=folium.Icon(color="yellow")
).add_to(m)

# Save the map to an HTML file
m.save("basic_map.html")