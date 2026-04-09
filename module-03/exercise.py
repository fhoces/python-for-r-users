"""
Module 3: Joins, Merges, Group-By Recipes -- Exercise

Run with: python module-03/exercise.py
"""

import pandas as pd
import numpy as np

rides   = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
drivers = pd.read_csv("data/drivers.csv", parse_dates=["signup_date"])
riders  = pd.read_csv("data/riders.csv",  parse_dates=["signup_date"])


# =============================================================================
# Q1. LEFT merge rides + drivers on driver_id
# =============================================================================

merged = rides.merge(drivers, on="driver_id", how="left", suffixes=("_ride", "_driver"))
print("Q1. Merged shape:", merged.shape)
print(merged[["ride_id", "driver_id", "city_ride", "city_driver", "gender"]].head())


# =============================================================================
# Q2. For each rider, find the driver they've ridden with most often
# =============================================================================

top_driver_per_rider = (
    rides
    .groupby(["rider_id", "driver_id"])
    .size()
    .reset_index(name="n_rides")
    .sort_values(["rider_id", "n_rides"], ascending=[True, False])
    .drop_duplicates("rider_id")
    .head(10)
)
print("\nQ2. Top driver per rider (first 10):")
print(top_driver_per_rider)


# =============================================================================
# Q3. Per-city averages joined back as a column on each ride
# =============================================================================

# Method A: transform (the cleanest)
rides["city_avg_fare"] = rides.groupby("city")["fare_usd"].transform("mean")
rides["fare_above_city_avg"] = rides["fare_usd"] - rides["city_avg_fare"]
print("\nQ3. With per-city averages:")
print(rides[["ride_id", "city", "fare_usd", "city_avg_fare", "fare_above_city_avg"]].head().round(2))


# =============================================================================
# Q4. Anti-join: drivers who never appear in rides
# =============================================================================

no_ride_drivers = drivers[~drivers["driver_id"].isin(rides["driver_id"])]
print("\nQ4. Drivers with no rides in the dataset:", len(no_ride_drivers))
print(no_ride_drivers.head())


# =============================================================================
# Q5. Rank rides within each driver by fare desc; top 3 per driver
# =============================================================================

top3 = (
    rides
    .sort_values(["driver_id", "fare_usd"], ascending=[True, False])
    .groupby("driver_id")
    .head(3)
)
print("\nQ5. Top 3 fares per driver (first 9 rows):")
print(top3[["driver_id", "ride_id", "fare_usd"]].head(9))


# =============================================================================
# Bonus: A 3-way merge (rides + drivers + riders)
# =============================================================================

full = (
    rides
    .merge(drivers.add_prefix("driver_"), left_on="driver_id", right_on="driver_driver_id", how="left")
    .merge(riders.add_prefix("rider_"),   left_on="rider_id",  right_on="rider_rider_id",   how="left")
)
print("\nBonus: full join shape:", full.shape)
print(full.columns.tolist()[:12], "...")
