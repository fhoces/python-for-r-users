# Python for an R User: Interview Prep

A 7-module Python refresher targeted at **applied economist / data science**
interviews in tech. The goal is to walk into a 30-minute Python coding
portion and be able to write any of the canonical analytical queries
without thinking about syntax.

**Time budget: ~5.5 hours** (module 7 adds about 2 hours, including the 36-minute audio lesson)

| # | Module | Concepts | Sample interview questions |
|---|--------|----------|-----|
| 1 | Python for R Users | Lists / dicts / comprehensions / `def` / imports | mph function, average fare for SF, invert a dict |
| 2 | pandas basics | filter / mutate / arrange / summarise | weekday morning fares by city, top-N per group, peak share |
| 3 | Joins, merges, group-by recipes | merge, anti-join, transform, top-N per group | merge with drivers, most-frequent driver per rider, deviation from city mean |
| 4 | Regression and A/B tests with statsmodels | OLS, robust SEs, fixed effects, logit, A/B inference, DiD | OLS with city FE, A/B treatment effect with CI, DiD |
| 5 | End-to-end interview scenario | The full pipeline, three scenarios + drill questions | A/B test analysis, multi-CSV processing, disparate-impact audit |
| 6 | Reading and Reviewing Someone Else's Python | Reading an unfamiliar codebase: imports → dependency graph → entry point, dataclasses, `frozen`/`replace`, relative imports, underscore convention | "Walk me through this code," find the bug, review a PR |
| 7 | Loading, Running SQL and Checking a Reproduction | Chunked `read_csv` with `dtype=str, keep_default_na=False` and explicit `""` to `None`; `executemany` with `?` placeholders; indexes after the load; `executescript` vs `execute`; `argparse`; deterministic CSV exports (sort keys, `repr` floats); `merge(indicator=True)`; tolerance vs exact equality; exit codes; the R twin (`DBI::dbExecute`, `read_csv_chunked`, `all.equal`); part 2: a Python twin of an R pipeline, function by function (openpyxl `data_only` reads, a positional frame indexed like the sheet, R's `as.numeric()` on a cell, `isin` / `duplicated(subset=...)` / `size()` / `sum()` as twins of `%in%` / `duplicated()` / `n()` / `sum(na.rm = TRUE)`, the parity test at `1e-9 * max(1, |r|)`) | Write the eight drill functions until `check.py` passes all eight |

Modules 1 to 5 each end with an "In the wild" slide and drill: real code
from the BSZ step of `opa-prop40` (`bsz-analysis/py/`), one idiom per
module with its R twin. One paper's reproduction supplies every real-code
excerpt in this course; module 7 drills the same code.

## Prerequisites

Modules 1 to 6 need no SQL. Module 7 pairs with module 6 of the SQL course
([sql-industry-prep](https://github.com/fhoces/sql-industry-prep)). Both are
built on the same real files from `opa-prop40`, `01_rtb_ca.sql` and
`02_data_sec_agg.sql`. The SQL module teaches what those queries compute.
Module 7 treats them as a black box and drills the Python around them, so do
SQL module 6 first. Module 7 also assumes modules 2 and 3 (pandas basics and
`merge`).

## Two design choices

1. **pandas, not polars.** pandas is what most tech-company DS interviewers expect,
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
