# %%
import pandas as pd 

# %%
osm_tags = pd.read_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/grid_with_osm_tags_roads.csv")
svi_meta = pd.read_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_streetview_metadata_grid_20m_cleaned.csv")

# %%
print(f"OSM tags shape: {osm_tags.shape}")
print(f"SVI metadata shape: {svi_meta.shape}\n")

print(osm_tags.columns)
print("\n")
print(svi_meta.columns)
print("\n")
print(osm_tags.head(5))
print("\n")
print(svi_meta.head(5))
print("\n")
# %%
'''process svi_meta to get, for each grid cell, the number of dated panoramas and the latest date available'''

# 1️⃣ filter out entries with NaN year or month
df = svi_meta.dropna(subset=["year", "month"]).copy()

# 2️⃣ construct datetime 
df["date"] = pd.to_datetime(df["year"].astype(int).astype(str) + "-" + df["month"].astype(int).astype(str))

# 3️⃣ drop duplicate entries for the same grid_id and (year, month)
df = df.drop_duplicates(subset=["grid_id", "year", "month"])

# 4️⃣ summary dated_count + latest_date for each grid cell.
svi_summary = (
    df.groupby("grid_id")
      .agg(
          dated_count=("date", "size"),
          latest_date=("date", "max")
      )
      .reset_index()
)

# 5️⃣ check
print(svi_summary.head())
print(svi_summary.describe())

# %%
'''merge svi_summary with osm_tags on grid_id'''
reference = pd.read_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv")

osm_tags = osm_tags.drop(columns=["query_lat", "query_lon"], errors="ignore") # these columns are also in reference
svi_summary = svi_summary.drop(columns=["query_lat", "query_lon"], errors="ignore") # these columns are also in reference

merged = reference.merge(osm_tags, on="grid_id", how="left").merge(svi_summary, on="grid_id", how="left")

# move grid_id to the front
cols = ["grid_id"] + [c for c in merged.columns if c != "grid_id"]
merged = merged[cols]

print(merged.head())
# %%
merged.to_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/cross_svi_osm.csv", index=False)

# %%
summary = (
    merged.groupby(["road_type", "grid_highway"], dropna=False)
    .agg(
        grid_count=("grid_id", "count"),              # 每类格网数量
        total_dated_count=("dated_count", "sum"),     # 每类 dated_count 总和
        mean_dated_count=("dated_count", "mean"),     # 平均每格网 dated_count
        latest_date=("latest_date", "max")            # 每类的最新街景日期
    )
    .sort_values('mean_dated_count',ascending=False).reset_index()
)

# 可选：四舍五入 dated_count，便于展示
summary["mean_dated_count"] = summary["mean_dated_count"].round(2)

summary

# %%
