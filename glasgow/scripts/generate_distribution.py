# %%
"""
Temporal Coverage Bias Analysis – Glasgow
-----------------------------------------
This script analyses the temporal characteristics of Google Street View imagery
in 20m × 20m grids. It visualises and quantifies three temporal dimensions:
  (1) density of available dates (dated_count)
  (2) temporal span (spreading_months)
  (3) recency / freshness (recency_months)
and integrates them into a composite index (TCBI).
"""

# %% 0. Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LogNorm
from matplotlib.ticker import MaxNLocator

# Configure Seaborn style (clean, publication-ready)
sns.set_theme(style="whitegrid", palette="deep", context="paper")

# %% 1. Load and prepare data
csv_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/metadata/glasgow_streetview_metadata_grid_20m_cleaned.csv"
df = pd.read_csv(csv_path).dropna(subset=["query_lat", "query_lon", "year", "month"])

# Create a datetime column (month-level precision)
df["date"] = pd.to_datetime(df["year"].astype(int).astype(str) + "-" +
                            df["month"].astype(int).astype(str))

# %% 2. Temporal metrics per grid cell
# (a) Number of available dates per grid (temporal density)
df_count = (
    df.groupby(["query_lat", "query_lon"])
      .size()
      .reset_index(name="dated_count")
)

# (b) Temporal span per grid (months between earliest and latest capture)
df_grid = (
    df.groupby(["query_lat", "query_lon"])["date"]
      .agg(["min", "max"])
      .reset_index()
)
df_grid["spreading_months"] = ((df_grid["max"].dt.year - df_grid["min"].dt.year) * 12 +
                               (df_grid["max"].dt.month - df_grid["min"].dt.month))

# (c) Most recent available date per grid & recency (in months)
df_latest = (
    df.groupby(["query_lat", "query_lon"])["date"]
      .max()
      .reset_index(name="latest_date")
)
from dateutil.relativedelta import relativedelta

# 全局最新日期（全局最大年月）
global_latest = df_latest["latest_date"].max()

# 计算每个格子的时间差（以月为单位）
df_latest["recency_months"] = df_latest["latest_date"].apply(
    lambda d: (global_latest.year - d.year) * 12 + (global_latest.month - d.month)
)

# Merge all metrics into one dataframe
g = (df_count
     .merge(df_grid[["query_lat", "query_lon", "spreading_months"]], on=["query_lat", "query_lon"])
     .merge(df_latest[["query_lat", "query_lon", "latest_date", "recency_months"]], on=["query_lat", "query_lon"])
)

# %% 3. Visualise basic distributions
# --- 3.1 Number of available dates per grid
plt.figure(figsize=(7, 4.5))
sns.histplot(df_count["dated_count"],
             bins=range(1, df_count["dated_count"].max() + 2),
             edgecolor="white")
plt.xlabel("Number of available dates per grid")
plt.ylabel("Number of grids")
plt.title("Distribution of Available Street View Dates per 20m Grid")
plt.grid(alpha=0.25)
plt.tight_layout()
plt.show()

# --- 3.2 Temporal span (spreading months)
plt.figure(figsize=(7, 4.5))
sns.histplot(df_grid["spreading_months"],
             bins=range(1, df_grid["spreading_months"].max() + 2),
             edgecolor="white",
             color=sns.color_palette("deep")[1])
plt.xlabel("Spreading months (max - min per grid)")
plt.ylabel("Number of grids")
plt.title("Distribution of Spreading Months per Grid (Glasgow)")
plt.grid(alpha=0.25)
plt.tight_layout()
plt.show()

# --- 3.3 Latest available date
plt.figure(figsize=(7, 4.5))
sns.histplot(df_latest["latest_date"],
             edgecolor="white",
             color=sns.color_palette("deep")[2])
plt.xlabel("Latest available date per grid")
plt.ylabel("Number of grids")
plt.title("Distribution of Latest Street View Date per Grid (Glasgow)")
plt.grid(alpha=0.25)
plt.tight_layout()
plt.show()

# %%
# 高频但旧
high_old = g[(g["dated_count"] > g["dated_count"].quantile(0.75)) &
              (g["recency_months"] > g["recency_months"].quantile(0.75))]

# 低频但新 
'''from the map I see those are mainly newly built areas with new residential buildings'''
low_new = g[(g["dated_count"] < g["dated_count"].quantile(0.25)) &
             (g["recency_months"] < g["recency_months"].quantile(0.25))]
print(len(high_old), len(low_new))
import folium
m = folium.Map(location=[55.86, -4.25], zoom_start=12)
for _, r in high_old.iterrows():
    folium.CircleMarker([r.query_lat, r.query_lon], radius=2, color="red").add_to(m)
for _, r in low_new.iterrows():
    folium.CircleMarker([r.query_lat, r.query_lon], radius=2, color="blue").add_to(m)
m.save("recency_frequency_outliers.html")

print("高频但旧：没啥特点；低频但新：主要是新建住宅区")
# %%
