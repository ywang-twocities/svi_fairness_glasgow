'''generate 20m grid points within Glasgow boundary (glasgow_boundary.geojson)'''
# %%

import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import os

# ============================================================
# 1️⃣ 加载 Glasgow 边界
# ============================================================
boundary_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/boundary/glasgow_boundary.geojson"
glasgow_gdf = gpd.read_file(boundary_path)
glasgow_poly = glasgow_gdf.unary_union  # 合并为一个 polygon（避免 MultiPolygon 问题）

print("✅ Glasgow polygon 加载完成")
print(f"边界范围: {glasgow_gdf.total_bounds}")  # [minx, miny, maxx, maxy]

# ============================================================
# 2️⃣ 计算步长（约 20m）
# ============================================================
minx, miny, maxx, maxy = glasgow_gdf.total_bounds
ref_lat = (miny + maxy) / 2

# 南北方向距离（米）
north_south_dist = geodesic((maxy, ref_lat), (miny, ref_lat)).meters
# 东西方向距离（米）
east_west_dist = geodesic((ref_lat, minx), (ref_lat, maxx)).meters

lat_step = (maxy - miny) / (north_south_dist / 20)
lon_step = (maxx - minx) / (east_west_dist / 20)

print(f"步长: {lat_step:.7f}° (lat), {lon_step:.7f}° (lon)")

# ============================================================
# 3️⃣ 生成 20m 网格并裁剪到 Glasgow 边界内
# ============================================================
lat_vals = np.arange(miny, maxy, lat_step)
lon_vals = np.arange(minx, maxx, lon_step)

grid_points = []
for i, lat in enumerate(lat_vals):
    for j, lon in enumerate(lon_vals):
        p = Point(lon, lat)
        if glasgow_poly.contains(p):  # 在边界内
            grid_points.append((lat, lon))
    if i % 100 == 0:
        print(f"Row {i}/{len(lat_vals)} done, 当前累计点数: {len(grid_points)}")

print(f"\n✅ Glasgow 区域内生成 {len(grid_points)} 个 20m 网格中心点")

# ============================================================
# 4️⃣ 保存结果
# ============================================================
out_csv = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv"

df = pd.DataFrame(grid_points, columns=["query_lat", "query_lon"])
df["grid_id"] = range(len(df))

df.to_csv(out_csv, index=False)
print(f"✅ 已保存至 {out_csv}")

# %%
