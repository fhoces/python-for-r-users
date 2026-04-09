"""
Module 2: pandas Basics -- Exercise

Run with: python module-02/exercise.py
"""

import pandas as pd
import numpy as np

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
