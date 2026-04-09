# Module 2: pandas Basics

## What this module covers

The five-verb dplyr toolkit (`filter`, `mutate`, `select`, `arrange`,
`summarise`) translated into pandas. By the end you should be able to
do any of the standard rideshare data-wrangling tasks in pandas
without looking up syntax — and be able to read any pandas script
written by a more idiomatic Python user.

## Setting up

```python
import pandas as pd
import numpy as np

rides   = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
drivers = pd.read_csv("data/drivers.csv", parse_dates=["signup_date"])
riders  = pd.read_csv("data/riders.csv",  parse_dates=["signup_date"])

rides.head()
rides.shape          # (30000, 9) — like dim() in R
rides.columns        # Index(['ride_id', 'rider_id', ...]) — like names()
rides.dtypes         # column types — like sapply(rides, class) sort of
```

The `parse_dates=` argument is essential. Without it, date columns are
parsed as strings.

## The dplyr → pandas translation table

| Verb | dplyr | pandas |
|---|---|---|
| Filter rows | `filter(fare > 10)` | `rides[rides["fare_usd"] > 10]` |
| Select columns | `select(city, fare)` | `rides[["city", "fare_usd"]]` |
| Add column | `mutate(rate = fare / dist)` | `rides["rate"] = rides["fare_usd"] / rides["distance_mi"]` |
| Sort | `arrange(desc(fare))` | `rides.sort_values("fare_usd", ascending=False)` |
| Summarise | `summarise(avg = mean(fare))` | `rides["fare_usd"].mean()` |
| Group + summarise | `group_by(city) |> summarise(...)` | `rides.groupby("city")["fare_usd"].mean()` |
| Distinct | `distinct(driver_id)` | `rides.drop_duplicates("driver_id")` |
| Count rows | `n()` / `count()` | `len(rides)` / `rides.value_counts()` |
| Rename | `rename(new = old)` | `rides.rename(columns={"old":"new"})` |

The thing to internalize: in pandas, **everything is a method call on
a DataFrame**, where dplyr is a pipeline of free functions. You'll
find yourself writing `rides.method1().method2().method3()` chains
that look a lot like a dplyr pipe.

## Filter

```python
# Single condition
rides[rides["fare_usd"] > 20]

# Multiple conditions — use & and |, NOT and/or
rides[(rides["fare_usd"] > 20) & (rides["distance_mi"] < 5)]

# isin (matches dplyr's %in%)
rides[rides["city"].isin(["SF", "Chicago"])]

# Negation
rides[~rides["city"].isin(["SF"])]

# Query method (string-based, often cleaner)
rides.query("fare_usd > 20 and distance_mi < 5")
```

The parentheses around each condition in the `&` form are **required**
because of operator precedence. Forgetting them is the most common
pandas mistake.

## Select / drop columns

```python
# Pick a few columns
rides[["ride_id", "fare_usd", "city"]]

# Pick by pattern
rides.filter(like="id")

# Drop a column
rides.drop(columns=["surge_mult"])

# Drop multiple
rides.drop(columns=["surge_mult", "rider_rating"])
```

Note: `rides.filter(...)` in pandas means *select columns*, NOT filter
rows. This naming clash with dplyr is confusing.

## Mutate (add / transform columns)

```python
# Single new column
rides["fare_per_mile"] = rides["fare_usd"] / rides["distance_mi"]

# Multiple new columns at once with assign() — closer to dplyr style
rides = rides.assign(
    fare_per_mile = rides["fare_usd"] / rides["distance_mi"],
    is_long_trip  = rides["distance_mi"] > 10,
    log_fare      = np.log(rides["fare_usd"])
)

# Conditional column with np.where
rides["price_tier"] = np.where(rides["fare_usd"] > 30, "premium", "standard")

# Multiple conditions: np.select
conditions = [
    rides["fare_usd"] < 10,
    rides["fare_usd"] < 25,
    rides["fare_usd"] >= 25
]
choices = ["cheap", "medium", "premium"]
rides["tier"] = np.select(conditions, choices, default="other")
```

The `assign()` method is the dplyr-est way to add columns. The
direct-assignment style (`rides["new"] = ...`) mutates the existing
DataFrame in place.

## Arrange (sort)

```python
rides.sort_values("fare_usd", ascending=False)
rides.sort_values(["city", "fare_usd"], ascending=[True, False])
```

## Summarise (aggregate)

```python
rides["fare_usd"].mean()                      # → scalar
rides[["fare_usd", "distance_mi"]].mean()     # → Series

# Multiple statistics with .agg()
rides[["fare_usd", "distance_mi"]].agg(["mean", "median", "std", "count"])

# Single column, multiple stats
rides["fare_usd"].agg(["mean", "median", "sum", "min", "max"])
```

## Group by + summarise

This is the workhorse of analytical work.

```python
# One group, one stat — returns a Series
rides.groupby("city")["fare_usd"].mean()

# One group, multiple stats — returns a DataFrame
rides.groupby("city")["fare_usd"].agg(["mean", "median", "count"])

# Multiple stats on multiple columns
rides.groupby("city").agg(
    avg_fare    = ("fare_usd", "mean"),
    n_rides     = ("ride_id", "count"),
    avg_distance = ("distance_mi", "mean"),
    p90_fare    = ("fare_usd", lambda x: x.quantile(0.9))
)

# Multiple grouping columns
rides.groupby(["city", "rider_rating"])["fare_usd"].mean()

# To get a regular DataFrame back (instead of grouped index)
rides.groupby("city", as_index=False)["fare_usd"].mean()
```

The `.agg(name=(column, function))` syntax is the cleanest way to do
multiple named aggregates — it's the closest thing pandas has to dplyr's
`summarise(avg_fare = mean(fare_usd), ...)`.

## Date/time operations

Once you parse a column with `parse_dates=`, pandas gives you a `.dt`
accessor:

```python
rides["pickup_at"].dt.year
rides["pickup_at"].dt.month
rides["pickup_at"].dt.day_name()
rides["pickup_at"].dt.hour
rides["pickup_at"].dt.dayofweek          # 0=Monday
```

Filter on dates:

```python
rides[rides["pickup_at"] >= "2025-12-01"]
rides[(rides["pickup_at"] >= "2025-12-01") & (rides["pickup_at"] < "2025-12-08")]
```

Resample to daily / weekly / monthly:

```python
rides.set_index("pickup_at").resample("D")["fare_usd"].sum()
rides.set_index("pickup_at").resample("W")["fare_usd"].mean()
rides.set_index("pickup_at").resample("ME")["ride_id"].count()  # M = month-end
```

## Pivot

Long → wide:

```python
# Each row: city, hour, n_rides → wide table with hours as columns
hourly = (
    rides
    .assign(hour = rides["pickup_at"].dt.hour)
    .groupby(["city", "hour"])
    .size()
    .reset_index(name="n_rides")
)

wide = hourly.pivot(index="city", columns="hour", values="n_rides")
```

Wide → long:

```python
long = wide.reset_index().melt(id_vars="city", var_name="hour", value_name="n_rides")
```

This is `tidyr::pivot_wider` and `pivot_longer`.

## Common traps

### 1. Operator precedence in boolean filters

```python
# WRONG — operator precedence sneaks up on you
rides[rides["fare_usd"] > 20 & rides["distance_mi"] < 5]

# RIGHT — parenthesize each condition
rides[(rides["fare_usd"] > 20) & (rides["distance_mi"] < 5)]
```

### 2. Chained assignment / "SettingWithCopyWarning"

```python
rides[rides["city"] == "SF"]["fare_usd"] = 0     # ⚠ silently does nothing
rides.loc[rides["city"] == "SF", "fare_usd"] = 0 # ✓ correct
```

Use `.loc[row_selector, col_selector]` for any "modify a subset" pattern.

### 3. NaN handling

`mean`, `sum`, `count` skip NaN by default (like R). But `==` doesn't
work for NaN: `df["col"] == np.nan` is always False. Use
`df["col"].isna()` instead.

### 4. Default index

pandas always has a row index, which is by default 0, 1, 2, ... If you
filter or group, the index can become non-contiguous. `df.reset_index(drop=True)`
gives you a fresh integer index.

## Interview questions

1. **Load `rides.csv`, keep weekday rides between 7-9am, compute mean
   fare by city.**
2. **Add a `fare_per_mile` column and find the top 5 most expensive
   rides per city.**
3. **Compute the share of rides per city that are during peak hours
   (7-9am or 5-7pm).**
4. **Find the top 3 cities by ride volume in the last 30 days of 2025.**
5. **Pivot a long table of (city, hour, n_rides) into a wide table.**
