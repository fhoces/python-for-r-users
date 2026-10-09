"""
Module 1: Python for R Users -- Exercise

Run with: python module-01/exercise.py
"""

import os

import pandas as pd


def mi_per_h(d, m): 
    return d /(m/60)







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
# Dict comprehension, read right to left: .items() yields (key, value) pairs,
# "for k, v in" unpacks each pair, and "v: k" writes it back swapped, so the
# old value becomes the new key. R analog: setNames(names(x), x).
# If two keys share a value, the later one wins (dict keys are unique).
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


# =============================================================================
# Q6. In the wild: a dict of functions (the LOADERS pattern of load_bundle.py)
# =============================================================================

# A registry: names -> functions. Each takes the list of ride dicts from Q2.
def mean_fare(rows):
    return sum(r["fare"] for r in rows) / len(rows)

def max_fare(rows):
    return max(r["fare"] for r in rows)

def n_rides(rows):
    return len(rows)

STATS = {"mean": mean_fare, "max": max_fare, "n": n_rides}

def summarise_sf(rows, wanted=None):
    wanted = wanted or list(STATS)                 # an empty list is falsy: default to all
    unknown = [w for w in wanted if w not in STATS]
    if unknown:
        raise ValueError(f"Unknown stat(s): {', '.join(unknown)}. Known: {', '.join(STATS)}")
    sf = [r for r in rows if r["city"] == "SF"]
    return {w: STATS[w](sf) for w in wanted}       # call the function the dict holds

print("\nQ6. all stats:", summarise_sf(rides))
print("Q6. two stats:", summarise_sf(rides, ["n", "max"]))
try:
    summarise_sf(rides, ["median"])
except ValueError as e:
    print("Q6. rejected:", e)
# R twin: stats <- list(mean = ..., max = ..., n = ...); stats[[w]](sf)


# =============================================================================
# Q7. Real code: the function behind the Prop 40 explorer's main estimate
# =============================================================================

# score_tab5_cell() is copied verbatim from the opa-prop40 repo, file
# bsz-analysis/py/compute_tab5.py at commit 21d653f
# (https://github.com/fhoces/opa-prop40/blob/21d653f/bsz-analysis/py/compute_tab5.py).
# It estimates revenue from California's proposed one-time 5% billionaire wealth
# tax (Proposition 40) at one setting of six assumptions, the six dials of the
# explorer at https://fhoces.github.io/opa-prop40/bsz-analysis/site/explorer/.
# Everything here is Module 1 Python: keyword arguments with defaults, dict
# lookups, a one-line if/else, and a dict as the return value.

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


# The explorer's main estimate adds three parts. The income tax loss is per year,
# so it is summed over 5 years at 3% first (site_pv_factor() in site_exports.py).
def pv_factor(r=0.03, years=5):
    return (1 - (1 + r) ** (-years)) / r

def main_estimate(out):
    return (out["wealth_tax_revenue"] + out["extra_ca_inctax_sales"]
            + out["annual_ca_inctax_loss"] * pv_factor())

# (a) Call it with the defaults. The defaults are the authors' base scenario.
base = score_tab5_cell(INP)
print("\nQ7a. base scenario:")
for k, v in base.items():
    print(f"  {k:24s}{v:10.3f}")
print(f"Q7a. main estimate: ${main_estimate(base):.1f}B")             # $106.8B, as the explorer shows

# (b) Change one assumption by name. Arguments you do not name keep their defaults.
print(f"Q7b. avoidance 20% instead of 10%: ${main_estimate(score_tab5_cell(INP, avoidance=0.20)):.1f}B")

# (c) Settings kept in a dict, unpacked with ** (R: do.call(f, c(list(inp), settings))).
leavers_row = {"pareto": False, "leavers": True}
print(f"Q7c. the authors' leavers row: ${main_estimate(score_tab5_cell(INP, **leavers_row)):.1f}B")

# (d) A dict comprehension sweeps one dial, as the explorer's first slider does.
sweep = {a: round(main_estimate(score_tab5_cell(INP, avoidance=a)), 1)
         for a in [0, 0.05, 0.10, 0.15, 0.20, 0.30]}
print("Q7d. main estimate by avoidance rate:", sweep)
# `x if cond else 0` in score_tab5_cell is Python's one-line if/else, R's
# `if (cond) x else 0`. Each one switches a term off: with pareto=False, pw is 0
# and the missing billionaires add nothing to W, n or taxable.
