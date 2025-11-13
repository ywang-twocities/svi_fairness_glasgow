'''
retrieve streetview metadata for Glasgow grid points from grid/glasgow_grid_20m.csv
use streetview.py from advanced_streetview_stitch repo
the output csv is saved to results/glasgow_streetview_metadata_grid_20m.csv
'''
# %%
import os
import sys
import importlib.util
import pandas as pd
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2

# ============================================================
# 1️⃣ load streetview.py
# ============================================================
streetview_path = '/mnt/home/2715439w/sharedscratch/svi_bias/tiles_to_pano/advanced_streetview_stitch/streetview_utils/streetview.py'

spec = importlib.util.spec_from_file_location("streetview_local", streetview_path)
streetview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streetview)

# ============================================================
# 2️⃣ helper
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

def process_panoids_with_distance(panoids_list, query_lat, query_lon):
    records = []
    for item in panoids_list:
        panoid = item.get('panoid')
        lat = item.get('lat')
        lon = item.get('lon')
        year = item.get('year', None)
        month = item.get('month', None)
        distance = haversine(query_lat, query_lon, lat, lon)
        records.append({
            'query_lat': query_lat,
            'query_lon': query_lon,
            'panoid': panoid,
            'lat': lat,
            'lon': lon,
            'year': year,
            'month': month,
            'distance_m': distance
        })
    return pd.DataFrame(records)

# ============================================================
# 3️⃣ load Glasgow grid
# ============================================================
grid_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv"
df_grid = pd.read_csv(grid_path)
# grid_centers = list(zip(df_grid["query_lat"], df_grid["query_lon"]))
# print(f"✅ Loaded Glasgow grid，in total: {len(grid_centers)}")
grid_centers = list(zip(df_grid["grid_id"], df_grid["query_lat"], df_grid["query_lon"]))
print(f"✅ Loaded Glasgow grid, in total: {len(grid_centers)} with grid_id")

# ============================================================
# 4️⃣ output file 
# ============================================================
out_csv = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_streetview_metadata_grid_20m.csv"
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

# if output file exists, load existing to skip done points
if os.path.exists(out_csv):
    existing = pd.read_csv(out_csv, usecols=["query_lat", "query_lon"]).drop_duplicates()
    done_set = set(zip(existing["query_lat"], existing["query_lon"]))
    print(f"🔁 exiting {len(done_set)}, these points will be skipped")
else:
    done_set = set()

# ============================================================
# 5️⃣ Exp mode: test only N points
# ============================================================
EXPERIMENT_MODE = False
EXPERIMENT_N = 1000  

if EXPERIMENT_MODE:
    grid_centers = grid_centers[:EXPERIMENT_N]
    print(f"🧪 Exp mode is on: only test for {EXPERIMENT_N} points")

# ============================================================
# 6️⃣ write metadata for each grid center in real time, robust to errors
# ============================================================
save_every = 50  # write 50 point each time
batch = []

for i, (gid, clat, clon) in enumerate(grid_centers):
    if (clat, clon) in done_set:
        continue

    try:
        panoids = streetview.panoids(clat, clon)
        if panoids:
            df = process_panoids_with_distance(panoids, clat, clon)
            df["grid_id"] = gid  # ✅ added grid_id column
            batch.append(df)

        # write to disk every save_every points
        if len(batch) >= save_every:
            pd.concat(batch).to_csv(out_csv, mode='a', header=not os.path.exists(out_csv), index=False)
            print(f"💾 written {len(batch)} batches of data in {out_csv}")
            batch = []

        print(f"[{i+1}/{len(grid_centers)}] ✅ ({clat:.6f}, {clon:.6f}) {len(panoids)} panoids")

    except Exception as e:
        print(f"[{i+1}] ⚠️ Failed ({clat:.6f}, {clon:.6f}) — {e}")

# write remaining batch
if batch:
    pd.concat(batch).to_csv(out_csv, mode='a', header=not os.path.exists(out_csv), index=False)
    print(f"💾 remaining batch written, in total {len(batch)} batches")

print("\n✅ Task completed.")
# %%
