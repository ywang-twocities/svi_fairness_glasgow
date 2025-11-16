
'''
This script extracts OSM tags for a 20m grid over Glasgow using pyrosm.
It performs the following steps:
1) Reads Glasgow boundary from GeoJSON.
2) Loads OSM data from a PBF file within the boundary.
3) Generates a 20m grid from provided center points CSV.(aligned with previous grid given by glasgow_grid_20m.csv)
4) Spatially joins OSM features to the grid.
5) Melts OSM tags into a long format (grid_id, tag_key, tag_value).
6) Summarizes tags per grid cell and saves results. 
'''
# %% ----------------------------- Imports -------------------------------------
import geopandas as gpd
from pyrosm import OSM
import pandas as pd
from shapely.geometry import Point
from tqdm import tqdm
import warnings
from shapely.geometry import box
warnings.filterwarnings("ignore") 
tqdm.pandas()

# %% ----------------------------- Paths ---------------------------------------
# 1) load glasgow_boundary.geojson (generated from glasgow_polygon.py)
BOUNDARY_PATH = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/boundary/glasgow_boundary.geojson"
# 2) load scotland OSM PBF file
PBF_PATH = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/boundary/scotland-251101.osm.pbf"
# 3) load glasgow_grid_20m.csv where (query_lat, query_lon）of grid center points are stored (generate_grids.py)
GRID_CSV = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_grid_20m.csv"

# %% ----------------------------- Helper --------------------------------------
def to_27700(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """projected to EPSG:27700 (better for geometry calc than 4326)"""
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    return gdf.to_crs(27700)

def back_to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gdf.to_crs(4326)

def melt_tags(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """
    change tag (from pyrosm) into long format (grid_id, tag_key, tag_value)。
    df is after sjoin (include grid_id but not geometry)
    """
    # exclude some useless columns (keep id_col and tag）
    drop_cols = {
        id_col, "id", "osm_id", "timestamp", "version", "changeset",
        "uid", "layer", "index_right", "source", "z_order"
    }
    # only pick non-empty columns as tag column
    tag_cols = [c for c in df.columns
                if c not in drop_cols and c != "geometry" and not df[c].isna().all()]
    if not tag_cols:
        return pd.DataFrame(columns=[id_col, "tag_key", "tag_value"])
    long_df = df[[id_col] + tag_cols].melt(
        id_vars=id_col, var_name="tag_key", value_name="tag_value"
    ).dropna(subset=["tag_value"])
    # change all tag values into str type to avoid complex data types
    long_df["tag_value"] = long_df["tag_value"].astype(str)
    return long_df

# %% ----------------------------- 1) load glasgow boundary ------------------------
glasgow = gpd.read_file(BOUNDARY_PATH)
glasgow = glasgow.to_crs(4326)
bounding_polygon = glasgow.geometry.iloc[0]
print("✅ Glasgow boundary loaded.")

# %% ----------------------------- 2) load osm data -----------------------------
osm = OSM(PBF_PATH, bounding_box=bounding_polygon)

# road layers
roads_all = osm.get_network(network_type="all")
roads_drivable = osm.get_network(network_type="driving")

# # building tag
# buildings = osm.get_data_by_custom_criteria(custom_filter={"building": True})                                        
# # landuse, amenity, natural, shop, tourism tags
# landuse = osm.get_data_by_custom_criteria(custom_filter={"landuse": True})
# amenities = osm.get_data_by_custom_criteria(custom_filter={"amenity": True})
# natural = osm.get_data_by_custom_criteria(custom_filter={"natural": True})
# shops = osm.get_data_by_custom_criteria(custom_filter={"shop": True})
# tourism = osm.get_data_by_custom_criteria(custom_filter={"tourism": True})

# Buildings
buildings = osm.get_buildings()

# Landuse / Natural
landuse = osm.get_landuse()
natural = osm.get_natural()

# POIs (amenity, shop, tourism)
pois = osm.get_pois()

amenities = pois[pois["amenity"].notnull()]
shops = pois[pois["shop"].notnull()]
tourism = pois[pois["tourism"].notnull()]

layers = {
    "roads": roads_all,
    "buildings": buildings,
    "landuse": landuse,
    "amenities": amenities,
    "natural": natural,
    "shops": shops,
    "tourism": tourism,
}

for k, v in layers.items():
    print(f"{k:9s} ->", "None" if v is None else f"{len(v)} features")

# %% ----------------------------- 3) generate identical 20m grids using center coords in glasgow_grid_20m.csv -----------------------
# load center coord from glasgow_grid_20m.csv
df_grid = pd.read_csv(GRID_CSV)
gdf_points = gpd.GeoDataFrame(
    df_grid,
    geometry=gpd.points_from_xy(df_grid["query_lon"], df_grid["query_lat"]),
    crs=4326
)

# projected to EPSG:27700, then generate 20m×20m grids
gdf_points_27700 = to_27700(gdf_points)
half = 10  # meter
# cap_style=3 -> square buffers
gdf_points_27700["geometry"] = gdf_points_27700.geometry.buffer(half, cap_style=3)

# project back to WGS84，and give grid_id
grid = back_to_wgs84(gdf_points_27700)
# grid["grid_id"] = range(len(grid))
# use grid_id from glasgow_grid_20m.csv if exists
if "grid_id" in df_grid.columns:
    grid["grid_id"] = df_grid["grid_id"].values
else:
    grid["grid_id"] = range(len(grid))
print(f"✅ generate {len(grid)} 20m×20m grids from center points in {GRID_CSV}.")

# %% ----------------------------- 4) Spatial join ----------------------------
grid_27700 = to_27700(grid)
joined_list = []

for name, gdf in layers.items():
    if gdf is None or len(gdf) == 0:
        continue
    gdf = gdf.to_crs(27700)
    keep_cols = [c for c in gdf.columns if c != "geometry"]
    j = gpd.sjoin(gdf[keep_cols + ["geometry"]], grid_27700[["grid_id", "geometry"]],
                  how="inner", predicate="intersects")
    j = j.drop(columns=["index_right"])
    j["layer"] = name
    joined_list.append(j)

if not joined_list:
    raise RuntimeError(f"No intersection between OSM layers and grids from {GRID_CSV}!")

joined_all_27700 = pd.concat(joined_list, ignore_index=True)
joined_all = back_to_wgs84(joined_all_27700)
print("✅ Spatial intersection completed:", len(joined_all), "records total")


# %% ----------------------------- 5) Determine road_type ----------------------
# all roads
roads_all_27700 = to_27700(roads_all)

# spatially join all roads to grid
join_all = gpd.sjoin(
    grid_27700[["grid_id", "geometry"]],
    roads_all_27700[["geometry"]],
    how="left",
    predicate="intersects"
)

# drivable road spatial join
roads_drivable_27700 = to_27700(roads_drivable)
join_drive = gpd.sjoin(
    grid_27700[["grid_id", "geometry"]],
    roads_drivable_27700[["geometry"]],
    how="left",
    predicate="intersects"
)

# three categories: no-road, non-drivable, drivable
grid["road_type"] = "no-road"
# grid.loc[join_all["index_right"].notnull(), "road_type"] = "non-drivable"
# grid.loc[join_drive["index_right"].notnull(), "road_type"] = "drivable"
# find grid_id that joins any types of roads
grids_with_any_road = join_all.loc[join_all["index_right"].notnull(), "grid_id"].unique()
grids_with_drive_road = join_drive.loc[join_drive["index_right"].notnull(), "grid_id"].unique()

grid["road_type"] = "no-road"

# first tag non-drivable 
grid.loc[grid["grid_id"].isin(grids_with_any_road), "road_type"] = "non-drivable"

# overlap with drivable
grid.loc[grid["grid_id"].isin(grids_with_drive_road), "road_type"] = "drivable"

print(f"✅ Road type classification completed. "
      f"no-road={sum(grid['road_type']=='no-road')}, "
      f"non-drivable={sum(grid['road_type']=='non-drivable')}, "
      f"drivable={sum(grid['road_type']=='drivable')}")


# %% ----------------------------- 6) Generate summary (same as before) -------
joined_no_geom = joined_all.drop(columns=["geometry"], errors="ignore")
tags_long = melt_tags(joined_no_geom, id_col="grid_id")

SPECIAL_KEYS = {"shop", "tourism", "highway"}
SEMANTIC_KEYS = ["building", "landuse", "amenity", "natural", "shop", "tourism", "highway"]
tags_long = tags_long[tags_long["tag_key"].isin(SEMANTIC_KEYS)]
print("✅ tags long format completed:", len(tags_long), " (grid_id, tag_key, tag_value) rows")

summary = (
    tags_long.groupby("grid_id")
    .agg(
        tag_key_list=("tag_key", list),
        tag_value_list=("tag_value", list),
        n_tags=("tag_key", "size"),
        unique_keys=("tag_key", "nunique"),
    )
    .reset_index()
)

# ---- main highway classification (same as before) ----
highway_df = tags_long[tags_long["tag_key"] == "highway"]

def pick_main_highway(values):
    priority = [
        "motorway", "trunk", "primary", "secondary", "tertiary",
        "residential", "service", "unclassified", "pedestrian", "track", "path", "footway"
    ]
    for p in priority:
        if p in values:
            return p
    return values[0] if values else None

highway_summary = (
    highway_df.groupby("grid_id")["tag_value"]
    .apply(lambda x: pick_main_highway(list(x)))
    .reset_index()
    .rename(columns={"tag_value": "grid_highway"})
)

summary = summary.merge(highway_summary, on="grid_id", how="left")

# Merge summary with grid and clean up
grid = grid.merge(summary, on="grid_id", how="left")
for c in ["n_tags", "unique_keys"]:
    grid[c] = grid[c].fillna(0).astype(int)

print("✅ Summary completed: number of grids with tags =", grid["n_tags"].gt(0).sum())

# %% ----------------------------- 6) Save simplified CSV ----------------------
cols_to_keep = [
    "grid_id", "query_lat", "query_lon",
    "grid_highway", "road_type", 
    "n_tags", "unique_keys",
    "tag_key_list", "tag_value_list"
]
grid_simplified = grid[cols_to_keep].copy()

output_path = "/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/grid_with_osm_tags_roads.csv"

grid_simplified.to_csv(output_path, index=False)
print(f"✅ Saved simplified grid with road_type classification to: {output_path}")