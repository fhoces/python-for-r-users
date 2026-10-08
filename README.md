# Python for an R User: Interview Prep

A 7-module Python refresher targeted at **applied economist / data science**
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
| **6** | [Reading and Reviewing Someone Else's Python](module-06/) | Reading an unfamiliar codebase: imports → entry point → leaves first | "Walk me through this code," find the bug, review a PR |
| **7** | [Loading, Running SQL and Checking a Reproduction](module-07/) | Chunked loading with explicit NULLs, parameter binding, `executescript`, deterministic exports, `merge(indicator=True)`, tolerances, exit codes, the R twin | Write the loader, the SQL runner, the answer-key comparison and the R vs Python parity check; graded by `check.py` |

## Module 7: different data, and two new artifact types

Module 7 works on the Python around one SQL step of a real replication
([fhoces/opa-prop40](https://github.com/fhoces/opa-prop40), `bsz-analysis/py/`).
Its data are a synthetic billionaire panel in the shape of the real one:
`python data/build_rtb_sample.py` writes `data/rtb_sample.csv`,
`data/rtb_ca_cik.csv`, `data/rtb_residency_overrides.csv` and the reference
results in `data/expected/`. Grade the drills with `python module-07/check.py`.

It also introduces two artifact types that no earlier module has:

- **`module-07/lesson/`**: an audio lesson, `python-around-sql.m4b`
  (chaptered, about 27 minutes, for Apple Books), narrated from the text
  sections in `lesson/text/`.
- **`module-07/quiz/`**: a walking quiz, read aloud and adaptive, published
  as a claude.ai Artifact: https://claude.ai/artifact/8ffFhvpHZLKPEzwyNtiUqe (private; the rebuild steps are in
  [`module-07/quiz/README.md`](module-07/quiz/README.md)).

The scripts that build both live in `tools/quiz/` (copied from the
book-summaries project, adapted for code questions and PNG covers).

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
