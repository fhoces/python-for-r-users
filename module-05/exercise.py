"""
Module 5: End-to-End Interview Scenario -- Exercise

Six mini-scenarios. Set a 5-minute timer per question. Try each one
yourself BEFORE reading the answer.

Run with: python module-05/exercise.py
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats

rides = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
ab    = pd.read_csv("data/ab_test.csv")


# =============================================================================
# Q1. Compute the average treatment effect, its 95% CI, and a one-sentence
#     summary, on data/ab_test.csv
# =============================================================================

print("Q1. A/B test")
fit = smf.ols("spend_usd ~ treatment", data=ab).fit(cov_type="HC3")
ate = fit.params["treatment"]
ci = fit.conf_int().loc["treatment"]
print(f"  ATE: ${ate:.2f}, 95% CI: [${ci[0]:.2f}, ${ci[1]:.2f}]")
print(f"  → Treatment increased spend by ${ate:.2f} per user, "
      f"95% CI [{ci[0]:.2f}, {ci[1]:.2f}].")


# =============================================================================
# Q2. Write a function that, given a rides DataFrame and a driver_id,
#     returns that driver's percentile in their city by avg fare
# =============================================================================

def driver_city_percentile(df, driver_id):
    driver_city = df.loc[df["driver_id"] == driver_id, "city"].iloc[0]
    city_drivers = (
        df[df["city"] == driver_city]
        .groupby("driver_id")["fare_usd"].mean()
        .sort_values()
    )
    rank = (city_drivers.index.get_loc(driver_id) + 1) / len(city_drivers)
    return rank

print("\nQ2. Driver percentile in city")
for did in [1, 50, 100]:
    p = driver_city_percentile(rides, did)
    print(f"  driver {did}: {p:.1%} percentile in their city")


# =============================================================================
# Q3. For each city, compute the share of rides that have a 5-star rating,
#     then plot it as a horizontal bar chart (saved to file)
# =============================================================================

print("\nQ3. 5-star share by city")
star5 = (
    rides
    .assign(is_5star = (rides["rider_rating"] == 5).astype(int))
    .groupby("city")
    .agg(n_rides = ("ride_id", "count"),
         pct_5star = ("is_5star", "mean"))
    .sort_values("pct_5star", ascending=False)
)
print(star5.round(3))

# Plot — uncomment to actually save
# import matplotlib.pyplot as plt
# fig, ax = plt.subplots()
# star5["pct_5star"].plot.barh(ax=ax)
# ax.set_xlabel("5-star share")
# plt.tight_layout()
# plt.savefig("module-05/q3_5star.png")


# =============================================================================
# Q4. Difference-in-differences with synthetic data
# =============================================================================

print("\nQ4. Difference-in-differences")
np.random.seed(42)
n = 4000
panel = pd.DataFrame({
    "city":  np.random.choice(["A", "B"], n),
    "month": np.random.choice(range(1, 13), n),
})
panel["treated"] = (panel["city"] == "A").astype(int)
panel["post"]    = (panel["month"] >= 7).astype(int)
panel["did"]     = panel["treated"] * panel["post"]
panel["outcome"] = (
    20 + 2 * panel["treated"] + 1 * panel["post"]
    + 5 * panel["did"]
    + np.random.normal(0, 3, n)
)

did_fit = smf.ols(
    "outcome ~ treated + post + did + C(city) + C(month)",
    data=panel
).fit(cov_type="cluster", cov_kwds={"groups": panel["city"]})
print(f"  DiD coef: {did_fit.params['did']:.3f} "
      f"(true effect: 5.000)")


# =============================================================================
# Q5. Read multiple CSVs from a folder and concat
# =============================================================================

# Skipping the actual file-system part since we don't have the folder set up.
# In a real interview:
#
#   from pathlib import Path
#   files = list(Path("data/by_city").glob("*.csv"))
#   dfs = [pd.read_csv(f).assign(city=f.stem) for f in files]
#   all_data = pd.concat(dfs, ignore_index=True)

print("\nQ5. (Skipped — see concepts.md for the file-system pattern)")


# =============================================================================
# Q6. Disparate-impact-style audit: regress fare-per-mile on group,
#     conditional on trip features. (Synthetic since we don't have demographics
#     in the rides CSV.)
# =============================================================================

print("\nQ6. Disparate-impact audit (synthetic)")
np.random.seed(7)
audit = pd.DataFrame({
    "fare_per_mile": np.random.normal(1.50, 0.30, 1000),
    "distance_mi":   np.random.lognormal(1.5, 0.5, 1000),
    "high_minority": np.random.binomial(1, 0.4, 1000)
})
# Inject a small disparate impact
audit.loc[audit["high_minority"] == 1, "fare_per_mile"] += 0.05

fit_audit = smf.ols(
    "fare_per_mile ~ high_minority + distance_mi",
    data=audit
).fit(cov_type="HC3")

print(f"  Coef on high_minority: {fit_audit.params['high_minority']:.3f}")
print(f"  SE: {fit_audit.bse['high_minority']:.3f}")
print(f"  → After controlling for distance, high-minority neighborhoods")
print(f"    are charged ${fit_audit.params['high_minority']:.3f}/mi more.")
print(f"    This documents disparate impact; mechanism is not identified.")
