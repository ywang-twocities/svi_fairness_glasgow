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
svi_meta["date"] = pd.to_datetime(svi_meta["year"].astype(int).astype(str) + "-" + svi_meta["month"].astype(int).astype(str))
'''merge svi_summary with osm_tags on grid_id'''
merged = osm_tags.merge(svi_meta, on="grid_id", how="left")

# move grid_id to the front
cols = ["grid_id"] + [c for c in merged.columns if c != "grid_id"]
merged = merged[cols]

print(merged.head())
# %%
merged.to_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/cross_svi_osm.csv", index=False)

# %%
