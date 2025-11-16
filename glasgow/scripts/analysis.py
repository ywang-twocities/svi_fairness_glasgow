# %%
import pandas as pd
import numpy as np

# %%
merged = pd.read_csv("/mnt/home/2715439w/sharedscratch/fairness/glasgow/results/merged_svi_osm.csv")

# %%
# parse 'date' column
parsed_date = pd.to_datetime(merged["date"], format="%d/%m/%Y", errors="coerce")
parsed_year  = parsed_date.dt.year
parsed_month = parsed_date.dt.month
month_index = parsed_year * 12 + parsed_month # year * 12 + month for calculations
group = merged.groupby("grid_id")

# %%
# time calc using month_index
def agg_time(df):
    idx = (pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.year * 12 +
           pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.month)

    idx = idx.dropna().astype(int).values
    if len(idx) == 0:
        return pd.Series({
            "first_date":  np.nan,
            "latest_date": np.nan,
            "n_dates":     0,
            "n_panos":     df["panoid"].nunique(),
            "max_gap_months": np.nan,
            "span_months": np.nan,
            "recency_months": np.nan
        })

    idx_sorted = np.sort(idx)
    first_idx = idx_sorted[0]
    last_idx  = idx_sorted[-1]

    # 最大 gap（月）
    if len(idx_sorted) > 1:
        max_gap = np.max(np.diff(idx_sorted))
    else:
        max_gap = np.nan

    # 提取原始文本的 first/latest date（不创建新列）
    first_text = df.loc[(pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.year * 12 +
                         pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.month) == first_idx, "date"].iloc[0]

    latest_text = df.loc[(pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.year * 12 +
                          pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce").dt.month) == last_idx,  "date"].iloc[0]

    return pd.Series({
        "first_date": first_text,
        "latest_date": latest_text,
        "n_dates": len(np.unique(idx_sorted)),
        "n_panos": df["panoid"].nunique(),
        "max_gap_months": max_gap,
        "span_months": last_idx - first_idx,
        "recency_months": month_index.max() - last_idx  # month_index 来自外层，不写入 merged
    })

# 4) 计算 grid_summary（不更改 merged）
grid_summary = group.apply(agg_time)

print(grid_summary.head())
# %%
