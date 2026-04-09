# Python for an R User: Interview Prep

A 5-module Python refresher targeted at the Uber **policy economist**
interview. The goal is to walk into a 30-minute Python coding portion of
a tech-economics interview and be able to write any of the canonical
analytical queries without thinking about syntax.

**Time budget: ~3 hours**

| # | Module | Concepts | Sample interview questions |
|---|--------|----------|-----|
| 1 | Python for R Users | Lists / dicts / comprehensions / `def` / imports | mph function, average fare for SF, invert a dict |
| 2 | pandas basics | filter / mutate / arrange / summarise | weekday morning fares by city, top-N per group, peak share |
| 3 | Joins, merges, group-by recipes | merge, anti-join, transform, top-N per group | merge with drivers, most-frequent driver per rider, deviation from city mean |
| 4 | Regression and A/B tests with statsmodels | OLS, robust SEs, fixed effects, logit, A/B inference, DiD | OLS with city FE, A/B treatment effect with CI, DiD |
| 5 | End-to-end interview scenario | The full pipeline, three scenarios + drill questions | A/B test analysis, multi-CSV processing, disparate-impact audit |

## Two design choices

1. **pandas, not polars.** pandas is what Uber DS interviewers expect,
   and `statsmodels` integrates with it natively. polars is great for
   production but costs you on the interview.
2. **Interview-driven.** Every module is built around a small set of
   questions you should be able to answer cold. This isn't a complete
   pandas reference; it's the *minimum useful subset* for an
   econ-applied interview.

## How to use this repo

1. Build the synthetic CSVs **once**: `Rscript data/build_csvs.R`
2. Read each module's `concepts.md`
3. Walk through `slides.Rmd` (or the rendered `slides.html`)
4. Drill the questions in `exercise.py`:
   `python module-XX/exercise.py`
5. Re-write each query from memory until you can do it in under 5 minutes

The data:

```
data/drivers.csv     800 rows  (driver_id, signup_date, gender, city)
data/riders.csv     4000 rows  (rider_id, signup_date, city, is_minority)
data/rides.csv     30000 rows  (ride_id, rider_id, driver_id, city, pickup_at,
                                distance_mi, surge_mult, rider_rating,
                                duration_min, fare_usd)
data/ab_test.csv    5000 rows  (user_id, treatment, city, spend_usd)
```

## What to know cold

| Stack | Purpose | Module |
|---|---|---|
| `pandas` | Data manipulation | 2, 3, 5 |
| `numpy` | Vectorized math, NaN | 2 |
| `statsmodels.formula.api` | R-style regression | 4, 5 |
| `scipy.stats` | t-tests, distributions | 4, 5 |
| `matplotlib` | Plotting | 5 |
| `linearmodels` | Panel data with many FEs (optional) | 4 |

## How this is different from a general Python tutorial

A generic "learn Python" tutorial spends weeks on syntax, classes,
decorators, generators, etc. This refresher skips all of that and goes
straight to the data work. If you've used R for any length of time, you
already know what data analysis looks like; you just need the Python
*words* for the same operations.

That's what every module is designed to deliver.

Say **"start module 1"** to begin.
