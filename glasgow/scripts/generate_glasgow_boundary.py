# %%
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

# Glasgow's relation id (str)
glasgow_id = "R1906767"   # find at https://wambachers-osm.website/boundaries/?map=12/55.85553/-4.232074&base=OSM&data=

# download glasgow polygon by OSM relation ID 
glasgow = ox.geocode_to_gdf(glasgow_id, by_osmid=True)

# save to GeoJSON
glasgow.to_file("glasgow_boundary.geojson", driver="GeoJSON")

# viz
glasgow.plot(edgecolor="black", facecolor="lightblue")
plt.title("Glasgow City Boundary (relation=1906767)")
plt.show()

print("✅ Glasgow City polygon saved as glasgow_boundary.geojson")

# %%
