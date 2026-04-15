# Python for an R User: Interview Prep

A 5-module Python refresher targeted at **applied economist / data science**
interviews in tech. The goal: walk into a 30-minute Python coding portion
and write any of the canonical analytical queries without thinking about
syntax.

> **Live slides:** *(set up after enabling GitHub Pages on this repo)*

## Why this exists

Most Python tutorials spend weeks on syntax, classes, decorators,
generators, etc. This refresher skips all of that and goes straight to
the data work. If you've used R seriously, you already know what data
analysis looks like — you just need the Python *words* for the same
operations.

The stack is **pandas + statsmodels**, because that's what most tech-company
DS interviewers expect, and `statsmodels` integrates natively with pandas.
polars is great for production but costs you on the interview.

## How to use this repo

```bash
# 1. Build the synthetic CSV data (once, requires R)
Rscript data/build_csvs.R

# 2. Read the concepts file for each module
open module-01/concepts.md

# 3. Walk through the slide deck
open module-01/slides.html

# 4. Drill the questions
python module-01/exercise.py

# 5. Re-write each query from memory until you can do it in 5 minutes
```

## Modules

| # | Module | Topics | Sample interview questions |
|---|--------|--------|---|
| **1** | [Python for R Users](module-01/) | Lists, dicts, comprehensions, `def`, imports | mph function, average fare for SF, invert a dict |
| **2** | [pandas basics](module-02/) | filter / mutate / arrange / summarise | weekday morning fares by city, top-N per group, peak share |
| **3** | [Joins, merges, group-by recipes](module-03/) | merge, anti-join, transform, top-N per group | merge with drivers, most-frequent driver per rider |
| **4** | [Regression and A/B tests with statsmodels](module-04/) | OLS, robust SEs, FE, logit, A/B inference, DiD | A/B treatment effect, fixed-effects regression, DiD |
| **5** | [End-to-end interview scenario](module-05/) | The full pipeline + drill questions | A/B analysis, multi-CSV processing, disparate-impact audit |

## Dependencies

```bash
pip install pandas numpy statsmodels scipy matplotlib seaborn
pip install linearmodels   # only if interview involves panel data
```

To rebuild the slides locally you also need R, `rmarkdown`, and `xaringan`.

## The data

Synthetic ride-sharing CSVs in `data/`:

```
data/drivers.csv     800 rows  (driver_id, signup_date, gender, city)
data/riders.csv     4000 rows  (rider_id, signup_date, city, is_minority)
data/rides.csv     30000 rows  (ride_id, rider_id, driver_id, city, pickup_at,
                                distance_mi, surge_mult, rider_rating,
                                duration_min, fare_usd)
data/ab_test.csv    5000 rows  (user_id, treatment, city, spend_usd)
```

## Companion courses

This is part of a small set of refreshers for the same applied
policy-economist interview prep:

- [discrimination-econ-refresher](https://github.com/fhoces/discrimination-econ-refresher) — labor-econ literature on discrimination
- [ml-discrimination-refresher](https://github.com/fhoces/ml-discrimination-refresher) — ML fundamentals + algorithmic fairness
- [Intro to SQL](https://github.com/fhoces/sql-industry-prep) — SQL drilling on a synthetic rideshare schema
