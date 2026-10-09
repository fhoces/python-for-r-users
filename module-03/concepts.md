# Module 3: Joins, Merges, and Group-By Recipes

## What this module covers

The pandas equivalents of dplyr's `*_join` family, plus the most common
group-by recipes you'll need: ranking within groups, finding the top
member of each group, joining a per-group summary back to the original.
This module is the bridge from "I can write a pandas one-liner" to "I
can write a 30-line analysis script that does something useful."

## merge: pandas' join

The pandas function for joining two DataFrames is `merge` (or the
equivalent `df1.merge(df2)` method). The `how=` argument controls the
join type:

| dplyr | pandas |
|---|---|
| `inner_join(a, b, by = "id")` | `a.merge(b, on="id", how="inner")` |
| `left_join(a, b, by = "id")` | `a.merge(b, on="id", how="left")` |
| `right_join(a, b, by = "id")` | `a.merge(b, on="id", how="right")` |
| `full_join(a, b, by = "id")` | `a.merge(b, on="id", how="outer")` |
| `semi_join(a, b, by = "id")` | `a[a["id"].isin(b["id"])]` |
| `anti_join(a, b, by = "id")` | `a[~a["id"].isin(b["id"])]` |

`merge` defaults to `how="inner"`. **Always specify `how=` explicitly**
to make your intent obvious to readers.

## A first merge

```python
import pandas as pd

rides   = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
drivers = pd.read_csv("data/drivers.csv", parse_dates=["signup_date"])

merged = rides.merge(drivers, on="driver_id", how="left", suffixes=("_ride", "_driver"))
merged.head()
```

The `suffixes=` argument is what pandas uses to disambiguate columns
that exist in both tables (here, `city` exists in both, so they become
`city_ride` and `city_driver`). dplyr uses `.x` and `.y` by default;
pandas uses `_x` and `_y`. Override with `suffixes=`.

## Different column names on each side

```python
# If the join columns have different names
rides.merge(
    drivers,
    left_on  = "driver_id",
    right_on = "id",
    how      = "left"
)
```

dplyr equivalent: `left_join(rides, drivers, by = c("driver_id" = "id"))`.

## Joining on index vs column

pandas DataFrames always have an index. You can join on the index
using `left_index=True` / `right_index=True`:

```python
# drivers indexed on driver_id
drivers_idx = drivers.set_index("driver_id")

rides.merge(
    drivers_idx,
    left_on     = "driver_id",
    right_index = True,
    how         = "left"
)
```

This is faster for very large tables because the index is hashed.

## Anti-join: drivers who never appeared

```python
# Drivers in drivers.csv who never had a ride
no_ride_drivers = drivers[~drivers["driver_id"].isin(rides["driver_id"])]
```

## Per-rider: their most-frequent driver

This is one of the most common interview-style group-by questions.

```python
top_driver_per_rider = (
    rides
    .groupby(["rider_id", "driver_id"])
    .size()
    .reset_index(name="n_rides")
    .sort_values(["rider_id", "n_rides"], ascending=[True, False])
    .drop_duplicates("rider_id")
)
```

The pattern: count per (group, sub-group), sort, then `drop_duplicates`
on the group keeps only the first (largest count) row per group.

You can also use `groupby().head(1)`:

```python
top_driver_per_rider = (
    rides
    .groupby(["rider_id", "driver_id"])
    .size()
    .reset_index(name="n_rides")
    .sort_values(["rider_id", "n_rides"], ascending=[True, False])
    .groupby("rider_id")
    .head(1)
)
```

## Per-city averages joined back to per-ride

The classic "deviation from group mean" pattern. Three ways:

### 1. Join the aggregate back

```python
city_means = rides.groupby("city", as_index=False)["fare_usd"].mean()
city_means = city_means.rename(columns={"fare_usd": "city_avg_fare"})

rides2 = rides.merge(city_means, on="city", how="left")
rides2["fare_above_city_avg"] = rides2["fare_usd"] - rides2["city_avg_fare"]
```

### 2. Use `transform`

```python
rides["city_avg_fare"] = rides.groupby("city")["fare_usd"].transform("mean")
rides["fare_above_city_avg"] = rides["fare_usd"] - rides["city_avg_fare"]
```

`transform` is the pandas idiom for "apply a group-level function and
broadcast the result back to the original shape." It's the cleanest
way to do this and worth memorizing.

### 3. Use `assign` + lambda

```python
rides = rides.assign(
    city_avg_fare      = lambda d: d.groupby("city")["fare_usd"].transform("mean"),
    fare_above_city_avg = lambda d: d["fare_usd"] - d["city_avg_fare"]
)
```

## Group-by-and-rank: top-N per group

dplyr: `slice_max(n = 5, by = city)`. pandas:

```python
# Method 1: rank inside groupby, then filter
rides["fare_rank"] = (
    rides
    .groupby("city")["fare_usd"]
    .rank(method="dense", ascending=False)
)
top5 = rides[rides["fare_rank"] <= 5]
```

```python
# Method 2: sort + groupby + head (cleaner)
top5 = (
    rides
    .sort_values(["city", "fare_usd"], ascending=[True, False])
    .groupby("city")
    .head(5)
)
```

Method 2 is what you'll see in idiomatic pandas code.

## concat: pandas' bind_rows / bind_cols

```python
# Stacking by row (like rbind / dplyr::bind_rows)
combined = pd.concat([df1, df2, df3], ignore_index=True)

# By column (like cbind / dplyr::bind_cols)
combined = pd.concat([df1, df2], axis=1)
```

## crosstab: pandas' xtabs

```python
pd.crosstab(rides["city"], rides["rider_rating"])
pd.crosstab(rides["city"], rides["rider_rating"], values=rides["fare_usd"], aggfunc="mean")
```

R: `table(rides$city, rides$rider_rating)`. The pandas version handles
both raw counts and aggregates.

## Common traps

### 1. Many-to-many merges

If both sides have duplicates on the join key, the result is the
Cartesian product within each key. This can blow up sizes
unexpectedly. pandas will warn you with `validate="one_to_many"` if
you specify it:

```python
rides.merge(drivers, on="driver_id", how="left", validate="many_to_one")
```

The valid options: `"one_to_one"`, `"one_to_many"`, `"many_to_one"`,
`"many_to_many"`. Use this any time you're not 100% sure of the
cardinality.

### 2. Default `how="inner"`

If you don't specify `how=`, you silently drop unmatched rows. This is
the source of "where did 5% of my data go?" bugs. Always be explicit.

### 3. Index alignment in `pd.concat`

`pd.concat` aligns on the index by default. If your DataFrames have a
non-trivial index (e.g., from a previous groupby), the result can have
NaNs. Use `ignore_index=True` to start with a fresh integer index.

### 4. `transform` only works with functions that return same-length output

```python
rides.groupby("city")["fare_usd"].transform("mean")    # ✓ broadcasts the mean
rides.groupby("city")["fare_usd"].transform("sum")     # ✓ broadcasts the sum
rides.groupby("city")["fare_usd"].transform("nlargest")# ✗ wrong shape
```

For variable-length output use `apply()` instead.

## In the wild: a join without pandas, and `match()` two ways

`check_common.py` in the BSZ reproduction ([`fhoces/opa-prop40`](https://github.com/fhoces/opa-prop40),
`bsz-analysis/py/`; module 1 explains the series) compares an export with
an answer key row by row. It aligns the two on a key with dicts and sets,
which is a join written by hand:

```python
def compare_keyed(name, ours, key, key_cols, num_cols, text_cols, tol):
    def k_of(r):
        return tuple(text(r[c]) for c in key_cols)   # the composite key, as text
    o = {k_of(r): r for r in ours}                   # rows reachable by their key
    k = {k_of(r): r for r in key}
    common = [x for x in o if x in k]                # inner join: keys on both sides
    chk = compare_rows(name, [o[x] for x in common], [k[x] for x in common], num_cols, text_cols, tol)
    only_o, only_k = len(set(o) - set(k)), len(set(k) - set(o))   # the two anti-joins
    dup = (len(ours) - len(o)) + (len(key) - len(k))              # rows lost to a repeated key
    chk["ok"] = chk["ok"] and only_o == 0 and only_k == 0 and dup == 0
```

- The key is a tuple of text, so a composite key works and `"2019"`
  matches `2019` whichever side typed it as a number.
- A dict keeps one row per key; a repeated key silently overwrites the
  earlier one. `len(ours) - len(o)` counts what was lost, which is the
  many-to-many trap (trap 1 below) made visible instead of multiplying rows.
- The pandas twin: `merge(how="outer", indicator=True)` and
  `value_counts()` of `_merge` give the three counts (`both`, `left_only`,
  `right_only`); `duplicated(subset=key_cols).sum()` gives `dup`. Module 7
  uses that form. The hand-written version keeps every row reachable by
  its key (`o[x]`), which the cell-by-cell comparison needs next.

The same lookup, R's `m1$x[match(yrs, m1$year)]`, appears twice in the
reproduction:

```python
# compute_shortrunseries.py: positions first, then the values
m1_year = m1["year"].to_numpy()
idx = [int(np.flatnonzero(m1_year == y)[0]) for y in yrs]
X = m1["ca_inctax_ca_billionaires_b"].to_numpy(float)[idx]

# tables.py: through the index
m1 = billionaires_ca_inctax_r["method1"].set_index("year")
x = m1.loc[yrs, "ca_inctax_ca_billionaires_b"].to_numpy(float)
```

Both are positional lookups by key. They differ in how they fail: a
missing year raises `IndexError` in the first and `KeyError` in the
second, at the lookup. R's `match()` returns `NA` and the error surfaces
later, somewhere else. Where a lookup must return exactly one row, the file
guards it:

```python
def pick(fid, yr, col):
    row = d[(d["forbes_id"] == fid) & (d["year"] == yr)]
    return float(row[col].iloc[0]) if len(row) == 1 else NA   # R: if (nrow(row) == 1) ... else NA
```

The exercise file drills the key-set comparison against `merge` (Q6).

## Interview questions

1. **Merge `rides` with `drivers` on `driver_id`, keeping all rides.**
2. **For each rider, find the driver they've ridden with most often.**
3. **Compute per-city averages and merge them back as a `city_avg_fare`
   column on each ride.**
4. **Anti-join: drivers in `drivers.csv` who never appear in
   `rides.csv`.**
5. **Rank rides within each driver by fare descending; keep the top 3
   per driver.**
