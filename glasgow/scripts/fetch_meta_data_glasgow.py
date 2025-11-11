'''retrieve streetview metadata for Glasgow grid points from grid/glasgow_grid_20m.csv'''
# %%
import os
import sys
import importlib.util
import pandas as pd
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2

# ============================================================
# 1️⃣ 加载 streetview.py
# ============================================================
streetview_path = '/mnt/home/2715439w/sharedscratch/svi_bias/tiles_to_pano/advanced_streetview_stitch/streetview_utils/streetview.py'

spec = importlib.util.spec_from_file_location("streetview_local", streetview_path)
streetview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streetview)

# ============================================================
# 2️⃣ 工具函数
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
# 3️⃣ 加载 Glasgow grid
# ============================================================
grid_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv"
df_grid = pd.read_csv(grid_path)
# grid_centers = list(zip(df_grid["query_lat"], df_grid["query_lon"]))
# print(f"✅ 载入 Glasgow grid，共 {len(grid_centers)} 个点")
grid_centers = list(zip(df_grid["grid_id"], df_grid["query_lat"], df_grid["query_lon"]))
print(f"✅ 载入 Glasgow grid，共 {len(grid_centers)} 个点（含 grid_id）")

# ============================================================
# 4️⃣ 输出文件 + 断点续传机制
# ============================================================
out_csv = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_streetview_metadata_grid_20m.csv"
os.makedirs(os.path.dirname(out_csv), exist_ok=True)

# 若文件已存在，读取已完成的点坐标
if os.path.exists(out_csv):
    existing = pd.read_csv(out_csv, usecols=["query_lat", "query_lon"]).drop_duplicates()
    done_set = set(zip(existing["query_lat"], existing["query_lon"]))
    print(f"🔁 已有 {len(done_set)} 个点已完成，将跳过这些点")
else:
    done_set = set()

# ============================================================
# 5️⃣ 实验模式：仅测试前 N 个点（如 1000）
# ============================================================
EXPERIMENT_MODE = False
EXPERIMENT_N = 1000  # 可调

if EXPERIMENT_MODE:
    grid_centers = grid_centers[:EXPERIMENT_N]
    print(f"🧪 实验模式启用：仅测试前 {EXPERIMENT_N} 个点")

# ============================================================
# 6️⃣ 主循环：实时写入 + 异常保护
# ============================================================
save_every = 50  # 每多少点写一次磁盘
batch = []

for i, (gid, clat, clon) in enumerate(grid_centers):
    if (clat, clon) in done_set:
        continue

    try:
        panoids = streetview.panoids(clat, clon)
        if panoids:
            df = process_panoids_with_distance(panoids, clat, clon)
            df["grid_id"] = gid  # ✅ 添加 grid_id
            batch.append(df)

        # 定期写入磁盘
        if len(batch) >= save_every:
            pd.concat(batch).to_csv(out_csv, mode='a', header=not os.path.exists(out_csv), index=False)
            print(f"💾 已写入 {len(batch)} 批数据到 {out_csv}")
            batch = []

        print(f"[{i+1}/{len(grid_centers)}] ✅ ({clat:.6f}, {clon:.6f}) {len(panoids)} panoids")

    except Exception as e:
        print(f"[{i+1}] ⚠️ Failed ({clat:.6f}, {clon:.6f}) — {e}")

# 写入剩余缓存
if batch:
    pd.concat(batch).to_csv(out_csv, mode='a', header=not os.path.exists(out_csv), index=False)
    print(f"💾 剩余批数据已写入，共 {len(batch)} 批")

print("\n✅ 全部任务完成")
# %%
