'''generate 20m grid points within Glasgow boundary (glasgow_boundary.geojson)'''
# %%

import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import os

# ============================================================
# 1️⃣ Load Glasgow boundary
# ============================================================
boundary_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/boundary/glasgow_boundary.geojson"
glasgow_gdf = gpd.read_file(boundary_path)
glasgow_poly = glasgow_gdf.unary_union  # 

print("✅ Glasgow polygon loaded")
print(f"boundaries: {glasgow_gdf.total_bounds}")  # [minx, miny, maxx, maxy]

# ============================================================
# 2️⃣ step length calculation: 20m
# ============================================================
minx, miny, maxx, maxy = glasgow_gdf.total_bounds
ref_lat = (miny + maxy) / 2

# N-S meter
north_south_dist = geodesic((maxy, ref_lat), (miny, ref_lat)).meters
# E-W meter
east_west_dist = geodesic((ref_lat, minx), (ref_lat, maxx)).meters

lat_step = (maxy - miny) / (north_south_dist / 20)
lon_step = (maxx - minx) / (east_west_dist / 20)

print(f"step length:  {lat_step:.7f}° (lat), {lon_step:.7f}° (lon)")

# ============================================================
# 3️⃣ generate 20m grids and overlap with glasgow boundary
# ============================================================
lat_vals = np.arange(miny, maxy, lat_step)
lon_vals = np.arange(minx, maxx, lon_step)

grid_points = []
for i, lat in enumerate(lat_vals):
    for j, lon in enumerate(lon_vals):
        p = Point(lon, lat)
        if glasgow_poly.contains(p):  # make sure in grid
            grid_points.append((lat, lon))
    if i % 100 == 0:
        print(f"Row {i}/{len(lat_vals)} done, total grids: {len(grid_points)}")

print(f"\n✅ Glasgow generates {len(grid_points)} grids of 20m")

# ============================================================
# 4️⃣ save
# ============================================================
out_csv = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv"

df = pd.DataFrame(grid_points, columns=["query_lat", "query_lon"])
df["grid_id"] = range(len(df))

df.to_csv(out_csv, index=False)
print(f"✅ saved to {out_csv}")

# %%
