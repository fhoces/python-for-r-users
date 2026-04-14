"""
Module 1: Python for R Users -- Exercise

Run with: python module-01/exercise.py
"""

import pandas as pd
import os

# =============================================================================
# Q1. Function: miles per hour
# =============================================================================

def mph(distance, minutes):
    """Compute miles per hour given distance (mi) and time (min)."""
    return distance / (minutes / 60)

print("Q1. mph(5, 15) =", mph(5, 15))           # 20.0
print("Q1. mph(10, 20) =", mph(10, 20))         # 30.0


# =============================================================================
# Q2. Average fare for SF rides (no pandas yet)
# =============================================================================

rides = [
    {"city": "SF", "fare": 12},
    {"city": "NY", "fare": 18},
    {"city": "SF", "fare": 9},
    {"city": "NY", "fare": 22},
    {"city": "SF", "fare": 15},
]

sf_fares = [r["fare"] for r in rides if r["city"] == "SF"]
sf_avg = sum(sf_fares) / len(sf_fares)
print("Q2. SF fares:", sf_fares, "-> avg =", sf_avg)


# =============================================================================
# Q3. Read a CSV with pandas
# =============================================================================

csv_path = "data/rides.csv"
if os.path.exists(csv_path):
    rides_df = pd.read_csv(csv_path)
    print("\nQ3. rides.csv shape:", rides_df.shape)
    print(rides_df.head())
else:
    print(f"\nQ3. SKIPPED -- run `Rscript data/build_csvs.R` to create {csv_path}")


# =============================================================================
# Q4. Invert a dict
# =============================================================================

original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print("\nQ4. original:", original)
print("Q4. inverted:", inverted)


# =============================================================================
# Q5. Unique sorted even numbers
# =============================================================================

nums = [4, 7, 2, 8, 4, 1, 6, 3, 8, 2]
unique_evens = sorted({n for n in nums if n % 2 == 0})
print("\nQ5. nums:", nums)
print("Q5. unique evens (sorted):", unique_evens)


# =============================================================================
# Bonus: f-strings, list slicing, dict.get()
# =============================================================================

name = "Maya"
n_rides = 137
print(f"\nBonus: {name} took {n_rides:,} rides last year ({n_rides/12:.1f}/month)")

# slicing
print("First three nums:", nums[:3])
print("Last two nums:   ", nums[-2:])

# dict.get with default
print("Missing city -> default:", {"SF": 5}.get("LA", 0))
