'''
filter glasgow_streetview_metadata_grid_20m.csv to ensure each panoid only appears once,
keeping the entry with the smallest distance_m (i.e., snapped to its nearest grid point)
and removing entries with NaN year or month
save to glasgow_streetview_metadata_grid_20m_cleaned.csv
'''

# %%
import pandas as pd

meta_data = pd.read_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_streetview_metadata_grid_20m.csv") 

# %%
meta_data[:10]

# %%
# example of a panoid with multiple entries
meta_data[meta_data['panoid']=='gEwac6dZ153bgC4Z_6YgtA']

# %%
print('total number of entries:\n')
print(meta_data.shape[0])
print('number of non-na entries:\n')
print(meta_data[meta_data['year'].notna()].shape[0])
print('\nnumber of unique panoids:\n')
print(meta_data['panoid'].nunique())
print('\n')
print(f"meaning there are {meta_data[meta_data['year'].notna()].shape[0] - meta_data['panoid'].nunique()} panoids are given to several grids.")
# %%
import pandas as pd

# 1️⃣ 去掉 year 或 month 为 NaN 的行
filtered = meta_data.dropna(subset=['year', 'month'])

# 2️⃣ 对每个 panoid 保留 distance_m 最小的那一行 (snapped to its nearest grid point)
filtered_unique = filtered.loc[filtered.groupby('panoid')['distance_m'].idxmin()]

# 3️⃣ 结果重置索引（方便后续操作）
# filtered_unique = filtered_unique.reset_index(drop=True)

# ✅ example of the same panoid after filtering
filtered_unique[filtered_unique['panoid']=='gEwac6dZ153bgC4Z_6YgtA']

print('total number of entries after filtering:\n')
print(filtered_unique.shape[0])
print('number of non-na entries after filtering:\n')
print(filtered_unique[filtered_unique['year'].notna()].shape[0])
print('\nnumber of unique panoids after filtering:\n')
print(filtered_unique['panoid'].nunique())
print('\n')
print(f"meaning there are {filtered_unique[filtered_unique['year'].notna()].shape[0] - filtered_unique['panoid'].nunique()} panoids are given to several grids.")
# %%
filtered_unique.to_csv(r"/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/glasgow_streetview_metadata_grid_20m_cleaned.csv", index=False)
# %%
