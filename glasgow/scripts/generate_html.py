# %%
'''visualize the count of unique year-month combinations for each 20m x 20m grid cell'''
import pandas as pd
import folium
import branca.colormap as cm
from folium.plugins import Fullscreen
import numpy as np

from matplotlib import cm as mpl_cm
import branca.colormap as bcm
import numpy as np


# 1️⃣ 读取数据
csv_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/metadata/glasgow_streetview_metadata_grid_20m_cleaned.csv"
df = pd.read_csv(csv_path).dropna(subset=["query_lat", "query_lon"])

# 2️⃣ 统计每个 grid 的唯一 year-month 组合数量
df_count = (
    df.dropna(subset=["year", "month"])
      .drop_duplicates(subset=["query_lat", "query_lon", "year", "month"])
      .groupby(["query_lat", "query_lon"])
      .size()
      .reset_index(name="dated_count")
)

print(df_count)

# 3️⃣ 颜色映射（新版 branca 用法）
min_val = df_count["dated_count"].min()
max_val = df_count["dated_count"].max()
if max_val == min_val:
    max_val = min_val + 1

name = "turbo"  # plasma, RdYlBu， 'coolwarm', 'Spectral', 'turbo' ，'viridis', 'Plasma', 'Cividis', 'Magma', 'Inferno'
mpl_map = mpl_cm.get_cmap(name)
colormap = bcm.LinearColormap(
    [mpl_map(i) for i in np.linspace(0, 1, 256)],
    vmin=min_val,
    vmax=max_val
)
colormap.caption = f"{name} colormap"


# 4️⃣ 经纬度偏移（20m）
lat_ref = df_count["query_lat"].mean()
lon_ref = df_count["query_lon"].mean()
d_lat = (20 / 111_000) / 2
d_lon = (20 / (111_000 * abs(np.cos(np.radians(lat_ref))))) / 2

# 5️⃣ 初始化地图
m = folium.Map(
    location=[lat_ref, lon_ref],
    zoom_start=17,
    tiles="OpenStreetMap"
)
colormap.add_to(m)
Fullscreen().add_to(m)

# 6️⃣ 绘制方格（降低透明度以增强底图可见度）
for _, row in df_count.iterrows():
    qlat, qlon = row["query_lat"], row["query_lon"]
    val = row["dated_count"]

    bounds = [
        [qlat - d_lat, qlon - d_lon],
        [qlat + d_lat, qlon + d_lon],
    ]

    folium.Rectangle(
        bounds=bounds,
        color=None,
        fill=True,
        fill_color=colormap(val),
        fill_opacity=1.0,  # ✅ 稍微透明一点，底图更清晰
        tooltip=f"({qlat:.6f}, {qlon:.6f}) — {int(val)} dated panoramas",
    ).add_to(m)

# 7️⃣ 保存结果
m.save("/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/streetview_grid_year_count_squares.html")
print("✅ 美化版地图完成：streetview_grid_year_count_squares_modern.html")

# %%
"""
visualize the most recent available date for each 20m x 20m grid cell
"""
import pandas as pd
import folium
import numpy as np
from folium.plugins import Fullscreen
from matplotlib import cm as mpl_cm
import branca.colormap as bcm

# 1️⃣ 读取数据
csv_path = (
    "/mnt/home/2715439w/sharedscratch/fairness/glasgow/metadata/"
    "glasgow_streetview_metadata_grid_20m_cleaned.csv"
)
df = pd.read_csv(csv_path).dropna(subset=["query_lat", "query_lon", "year", "month"])

# 2️⃣ 构造日期字段
df["date"] = pd.to_datetime(
    df["year"].astype(int).astype(str) + "-" + df["month"].astype(int).astype(str) + "-01"
)

# 3️⃣ 对每个 grid 取最新可用日期
df_latest = (
    df.groupby(["query_lat", "query_lon"])["date"]
    .max()
    .reset_index()
)

# 4️⃣ 数值映射（日期 → ordinal）
min_date = df_latest["date"].min()
max_date = df_latest["date"].max()
df_latest["date_ordinal"] = df_latest["date"].map(lambda d: d.toordinal())

# 5️⃣ 颜色映射：黑 → 亮黄
name = "cividis"
mpl_map = mpl_cm.get_cmap(name)
colormap = bcm.LinearColormap(
    colors=[mpl_map(i) for i in np.linspace(0, 1, 256)],
    vmin=min_date.toordinal(),
    vmax=max_date.toordinal(),
)

# ✅ 自定义 legend 的年份刻度
years = pd.date_range(min_date, max_date, freq="YS")
tick_positions = [d.toordinal() for d in years]
tick_labels = [d.strftime("%Y") for d in years]
colormap = colormap.to_step(index=tick_positions)  # 分段显示颜色
colormap.caption = "Most Recent Available Year (Old → New)"

# 6️⃣ 经纬度偏移（每个 grid 约 20m × 20m）
lat_ref = df_latest["query_lat"].mean()
lon_ref = df_latest["query_lon"].mean()
d_lat = (20 / 111_000) / 2
d_lon = (20 / (111_000 * abs(np.cos(np.radians(lat_ref))))) / 2

# 7️⃣ 初始化地图
m = folium.Map(location=[lat_ref, lon_ref], zoom_start=17, tiles="CartoDB Positron")
colormap.add_to(m)
Fullscreen().add_to(m)

# 8️⃣ 绘制方格
for _, row in df_latest.iterrows():
    qlat, qlon = row["query_lat"], row["query_lon"]
    val = row["date_ordinal"]
    date_label = row["date"].strftime("%Y-%m")

    bounds = [
        [qlat - d_lat, qlon - d_lon],
        [qlat + d_lat, qlon + d_lon],
    ]

    folium.Rectangle(
        bounds=bounds,
        color=None,
        fill=True,
        fill_color=colormap(val),
        fill_opacity=0.9,
        tooltip=f"({qlat:.6f}, {qlon:.6f}) — latest: {date_label}",
    ).add_to(m)

# 9️⃣ 保存结果
m.save("/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/streetview_grid_latest_date.html")
print("✅ 地图完成：streetview_grid_latest_date.html")

# %%
