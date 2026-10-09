"""
Module 2: pandas Basics -- Exercise

Run with: python module-02/exercise.py
"""

import itertools

import numpy as np
import pandas as pd

# Load the data
rides   = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
drivers = pd.read_csv("data/drivers.csv", parse_dates=["signup_date"])
riders  = pd.read_csv("data/riders.csv",  parse_dates=["signup_date"])

print("Loaded:", rides.shape, drivers.shape, riders.shape)


# =============================================================================
# Q1. Weekday rides 7-9am, mean fare by city
# =============================================================================

morning_weekday = rides[
    (rides["pickup_at"].dt.dayofweek < 5) &
    (rides["pickup_at"].dt.hour >= 7) &
    (rides["pickup_at"].dt.hour < 9)
]
q1 = morning_weekday.groupby("city")["fare_usd"].mean().round(2)
print("\nQ1. Mean fare for weekday 7-9am rides by city:")
print(q1)


# =============================================================================
# Q2. Top 5 most expensive rides per city (preview of group-by-rank)
# =============================================================================

q2 = (
    rides
    .assign(fare_per_mile = rides["fare_usd"] / rides["distance_mi"])
    .sort_values(["city", "fare_per_mile"], ascending=[True, False])
    .groupby("city")
    .head(5)
    [["city", "ride_id", "fare_usd", "distance_mi", "fare_per_mile"]]
)
print("\nQ2. Top 5 most expensive ($/mi) per city (first 10 rows):")
print(q2.head(10).round(2))


# =============================================================================
# Q3. Share of rides per city during peak hours (7-9am or 5-7pm)
# =============================================================================

rides["hour"] = rides["pickup_at"].dt.hour
rides["is_peak"] = ((rides["hour"].between(7, 8)) | (rides["hour"].between(17, 18))).astype(int)

q3 = (
    rides
    .groupby("city")
    .agg(
        n_rides     = ("ride_id", "count"),
        n_peak      = ("is_peak", "sum"),
    )
    .assign(peak_share = lambda d: (d["n_peak"] / d["n_rides"]).round(3))
)
print("\nQ3. Peak-hour share by city:")
print(q3)


# =============================================================================
# Q4. Top 3 cities by ride volume in the last 30 days of 2025
# =============================================================================

recent = rides[rides["pickup_at"] >= "2025-12-02"]
q4 = recent.groupby("city").size().sort_values(ascending=False).head(3)
print("\nQ4. Top 3 cities by ride volume (last 30 days):")
print(q4)


# =============================================================================
# Q5. Pivot: long (city x hour) -> wide
# =============================================================================

long = (
    rides
    .groupby(["city", "hour"])
    .size()
    .reset_index(name="n_rides")
)
wide = long.pivot(index="city", columns="hour", values="n_rides")
print("\nQ5. Pivoted hourly counts (first 4 hour columns):")
print(wide.iloc[:, :4])


# =============================================================================
# Bonus: assign() chain (closest to dplyr style)
# =============================================================================

summary = (
    rides
    .assign(
        log_fare    = np.log(rides["fare_usd"]),
        is_long     = rides["distance_mi"] > 5,
        weekday     = rides["pickup_at"].dt.day_name()
    )
    .groupby(["city", "weekday"], as_index=False)
    .agg(
        n_rides    = ("ride_id", "count"),
        avg_fare   = ("fare_usd", "mean"),
        avg_log    = ("log_fare", "mean")
    )
    .sort_values(["city", "weekday"])
)
print("\nBonus: per-city per-weekday summary (first 10 rows):")
print(summary.head(10).round(2))


# =============================================================================
# Q6. In the wild: a per-city table with an "All cities" row (tables.py pattern)
# =============================================================================

by_city = (
    rides
    .groupby("city", as_index=False)
    .agg(n_rides=("ride_id", "count"), mean_fare=("fare_usd", "mean"))
    .sort_values("mean_fare", ascending=False, kind="stable")   # R's order() is stable
)
all_row = {"city": "All cities", "n_rides": len(rides), "mean_fare": rides["fare_usd"].mean()}
q6 = pd.concat([by_city, pd.DataFrame([all_row])], ignore_index=True)   # bind_rows
print("\nQ6. Mean fare by city, with a total row:")
print(q6.round(2).to_string(index=False))

# numpy twins of R's c(NA, head(x, -1)) and sum(x, na.rm = TRUE), on daily ride counts
daily = rides.groupby(rides["pickup_at"].dt.floor("D")).size().to_numpy(float)
change = daily - np.append(np.nan, daily[:-1])
print(f"Q6. {len(daily)} days; day-over-day changes sum to {np.nansum(change):.0f}, "
      f"which is last - first = {daily[-1] - daily[0]:.0f}")


# =============================================================================
# Q7. Real code: rebuild the Prop 40 explorer's grid as a DataFrame
# =============================================================================

# The explorer at https://fhoces.github.io/opa-prop40/bsz-analysis/site/explorer/
# has six dials. Every combination of their levels is one row of a precomputed
# grid: 6 x 5 x 4 x 4 x 2 x 2 = 1,920 settings. Here you rebuild that grid with
# the repo's own function and then query it with Module 2 pandas.
# score_tab5_cell() and the grid loop come from the opa-prop40 repo at commit
# 21d653f: bsz-analysis/py/compute_tab5.py and build_site_grid() in
# bsz-analysis/py/site_exports.py. Module 1's Q7 walks through the function.

# The eight numbers it reads. That repo computes them from the authors' public
# workbook (August 2026): $B unless noted.
INP = {
    "n0": 250,                                    # billionaires Forbes lists in CA (count)
    "W0": 2307,                                   # their total wealth
    "C": 3.0613637745707907,                      # CA income tax they pay per year
    "pct_wealth_increase": 0.2819041155905384,    # extra wealth of the ones Forbes misses (share)
    "pct_count_increase": 1.4782375212688241,     # how many more billionaires that is (share)
    "fraction_in_phasein": 0.12141926321056487,   # share of the extra wealth near the $1B line
    "W_pre": 333.61,                              # wealth of those who left before 2026
    "leaver_loss": 0.3623624024787383,            # income tax lost to all leavers per year
}


def score_tab5_cell(inp, avoidance=0.10, mobility_share=0.50, avoidance_small=0.20,
                    sell_share=1 / 3, pareto=False, leavers=False, tax_rate=0.05,
                    phasein_rate=0.025, gains_share=0.80, ca_cg_rate=0.133):
    pw = inp["pct_wealth_increase"] if pareto else 0
    W = inp["W0"] * (1 + pw)
    n = inp["n0"] * ((1 + inp["pct_count_increase"]) if pareto else 1)
    taxable = ((1 - avoidance) * (inp["W0"] - (inp["W_pre"] if leavers else 0))
               + (1 - avoidance_small) * inp["W0"] * pw)
    # Row 2 subtracts the phase-in deduction; row 4 (pareto AND leavers) does
    # not (Tab5!F9). Literal workbook behaviour.
    phasein = inp["W0"] * pw * inp["fraction_in_phasein"] * phasein_rate if (pareto and not leavers) else 0
    revenue = tax_rate * taxable - phasein
    extra = revenue * sell_share * gains_share * ca_cg_rate
    loss = (-(avoidance * mobility_share) * inp["C"] * (1 + pw)
            - (inp["leaver_loss"] if leavers else 0))
    return {
        "n_billionaires": float(n),
        "wealth": float(W),
        "taxable_wealth": float(taxable),
        "avoidance_rate": float(1 - taxable / W),
        "wealth_tax_revenue": float(revenue),
        "extra_ca_inctax_sales": float(extra),
        "annual_ca_inctax_loss": float(loss),
    }


def score_tab5_cell(inp, avoidance=0.10, mobility_share=0.50, avoidance_small=0.20,
                    sell_share=1 / 3, pareto=False, leavers=False, tax_rate=0.05,
                    phasein_rate=0.025, gains_share=0.80, ca_cg_rate=0.133):
    pw = inp["pct_wealth_increase"] if pareto else 0
    W = inp["W0"] * (1 + pw)
    n = inp["n0"] * ((1 + inp["pct_count_increase"]) if pareto else 1)
    taxable = ((1 - avoidance) * (inp["W0"] - (inp["W_pre"] if leavers else 0))
               + (1 - avoidance_small) * inp["W0"] * pw)
    # Row 2 subtracts the phase-in deduction; row 4 (pareto AND leavers) does
    # not (Tab5!F9). Literal workbook behaviour.
    phasein = inp["W0"] * pw * inp["fraction_in_phasein"] * phasein_rate if (pareto and not leavers) else 0
    revenue = tax_rate * taxable - phasein
    extra = revenue * sell_share * gains_share * ca_cg_rate
    loss = (-(avoidance * mobility_share) * inp["C"] * (1 + pw)
            - (inp["leaver_loss"] if leavers else 0))
    return {
        "n_billionaires": float(n),
        "wealth": float(W),
        "taxable_wealth": float(taxable),
        "avoidance_rate": float(1 - taxable / W),
        "wealth_tax_revenue": float(revenue),
        "extra_ca_inctax_sales": float(extra),
        "annual_ca_inctax_loss": float(loss),
    }


DIALS = {                                         # the explorer's six dials and their levels
    "avoidance":       [0, 0.05, 0.10, 0.15, 0.20, 0.30],
    "mobility_share":  [0, 0.25, 0.50, 0.75, 1],
    "avoidance_small": [0.10, 0.20, 0.30, 0.50],
    "sell_share":      [0, 1 / 3, 2 / 3, 1],
    "pareto":          [False, True],
    "leavers":         [False, True],
}
PV_5Y_3PCT = (1 - 1.03 ** -5) / 0.03              # sums a yearly amount over 5 years at 3%

# (a) One dict per setting, then one DataFrame (R: expand.grid() + pmap() + bind_rows()).
#     itertools.product varies the LAST dial fastest, as build_site_grid() does.
rows = []
for values in itertools.product(*DIALS.values()):
    setting = dict(zip(DIALS, values))
    rows.append({**setting, **score_tab5_cell(INP, **setting)})
grid = pd.DataFrame(rows)
grid.insert(0, "cell", range(1, len(grid) + 1))
print("\nQ7a. grid:", grid.shape)                                    # (1920, 14)

# (b) mutate: the main estimate as column arithmetic, not inside the loop.
grid = grid.assign(
    income_tax_loss_pv = grid["annual_ca_inctax_loss"] * PV_5Y_3PCT,
    main_estimate      = lambda d: d["wealth_tax_revenue"] + d["extra_ca_inctax_sales"]
                                   + d["income_tax_loss_pv"],
)

# (c) filter: the authors' base scenario is the row where every dial is at its default.
is_base = ((grid["avoidance"] == 0.10) & (grid["mobility_share"] == 0.50)
           & (grid["avoidance_small"] == 0.20) & (grid["sell_share"] == 1 / 3)
           & ~grid["pareto"] & ~grid["leavers"])
print(grid.loc[is_base, ["cell", "main_estimate"]].round(1).to_string(index=False))  # cell 789, 106.8

# (d) group by + summarise: how far one dial moves the estimate across all other settings.
q7d = grid.groupby("avoidance")["main_estimate"].agg(["min", "median", "max"]).round(1)
print("\nQ7d. main estimate by avoidance rate, over the other 320 settings each:")
print(q7d)

# (e) arrange: the five lowest settings (the explorer flags the lowest one). The first
#     four tie: avoidance_small only matters when pareto is True, so with pareto False
#     its four levels give the same number.
print("\nQ7e. five lowest settings:")
print(grid.nsmallest(5, "main_estimate")[list(DIALS) + ["main_estimate"]].round(2).to_string(index=False))

# (f) pivot: avoidance x mobility share, with the other four dials at the base values.
others_at_base = ((grid["avoidance_small"] == 0.20) & (grid["sell_share"] == 1 / 3)
                  & ~grid["pareto"] & ~grid["leavers"])
q7f = grid[others_at_base].pivot(index="avoidance", columns="mobility_share", values="main_estimate")
print("\nQ7f. main estimate, avoidance (rows) x share of avoidance that is leaving (columns):")
print(q7f.round(1))

# (g) summarise a condition: the mean of a True/False column is a share.
print(f"\nQ7g. settings with a main estimate under $90B: {(grid['main_estimate'] < 90).mean():.1%}")
