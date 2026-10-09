# Module 5: End-to-End Interview Scenario

## What this module covers

This is the put-it-all-together module. The previous four modules were
each one tool: syntax, pandas, joins, statsmodels. This one is the
*combination* — what you'd actually do in 15 minutes when an interviewer
hands you a CSV and a question.

We walk through three end-to-end scenarios at increasing difficulty,
and close with a 30-minute mock interview structure you can drill on
your own.

## The general structure of an interview question

1. **Read the question carefully.** What's the outcome variable?
   What's the population? What's the comparison?
2. **Look at the data.** `head()`, `shape`, `dtypes`, `describe()`.
3. **Pose the analysis as a function.** Inputs → outputs.
4. **Write the code.** Don't try to make it pretty on the first pass.
5. **Sanity check the result.** Does it match a hand calculation on a
   small subset?
6. **State the answer in plain English** with a confidence interval
   if applicable.

This last step is what separates a "good" candidate from a "great"
one. Always restate the answer in words.

## Scenario 1: A/B test analysis

> *"We ran an A/B test on a new dispatch algorithm in five cities.
> Treated users saw the new algorithm; control users saw the old one.
> Compute the average treatment effect on rider spend, with a 95% CI
> and a plot."*

```python
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

ab = pd.read_csv("data/ab_test.csv")

# Step 1: look at the data
print(ab.shape)
print(ab.describe())

# Step 2: balance check (are treatment and control similar on covariates?)
print(ab.groupby("treatment")["spend_usd"].agg(["count", "mean", "std"]))

# Step 3: run the regression (OLS = t-test, with HC SEs)
fit = smf.ols("spend_usd ~ treatment", data=ab).fit(cov_type="HC3")

ate    = fit.params["treatment"]
ate_ci = fit.conf_int().loc["treatment"]

print(f"\nATE: ${ate:.2f}")
print(f"95% CI: [${ate_ci[0]:.2f}, ${ate_ci[1]:.2f}]")

# Step 4: variance reduction with city fixed effects
fit_fe = smf.ols("spend_usd ~ treatment + C(city)", data=ab).fit(cov_type="HC3")
print(f"\nWith city FE: ATE = ${fit_fe.params['treatment']:.2f}")
print(f"  SE without FE: {fit.bse['treatment']:.4f}")
print(f"  SE with FE:    {fit_fe.bse['treatment']:.4f}")

# Step 5: visualize
fig, ax = plt.subplots(figsize=(7, 4))
ab.boxplot(column="spend_usd", by="treatment", ax=ax)
ax.set_title("Spend by treatment arm")
plt.suptitle("")
plt.tight_layout()
# plt.savefig("ab_test.png")  # save if needed
```

**Plain-English answer:** "The new dispatch algorithm increased rider
spend by approximately $1.80 per user, with a 95% confidence interval
of [$1.50, $2.10]. The estimate is robust to controlling for city
fixed effects."

## Scenario 2: Process a folder of CSVs

> *"We have one CSV per city in `data/by_city/`. Compute the daily
> ride count for each city and produce a single output table."*

```python
import pandas as pd
from pathlib import Path

# Step 1: list the files
files = list(Path("data/by_city").glob("*.csv"))

# Step 2: read each, add the city name, concat
dfs = []
for f in files:
    city = f.stem.replace("_", " ")
    df = pd.read_csv(f, parse_dates=["pickup_at"])
    df["city"] = city
    dfs.append(df)

all_rides = pd.concat(dfs, ignore_index=True)

# Step 3: compute daily counts per city
daily = (
    all_rides
    .assign(date = all_rides["pickup_at"].dt.date)
    .groupby(["city", "date"])
    .size()
    .reset_index(name="n_rides")
)

print(daily.head())
```

The patterns to memorize:
- `Path(...).glob("*.csv")` for file iteration
- A `for` loop to build a list of dataframes, then `pd.concat`
- `.dt.date` to collapse a datetime to a date

## Scenario 3: Disparate-impact audit

> *"We're auditing the surge pricing algorithm. Are higher-minority
> neighborhoods charged more per mile, conditional on trip
> characteristics?"*

This is the Pandey-Caliskan setup translated into pandas.

```python
import pandas as pd
import statsmodels.formula.api as smf

rides = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
# (assume rides has been merged with neighborhood demographics)

# Step 1: define the outcome
rides["fare_per_mile"] = rides["fare_usd"] / rides["distance_mi"]

# Step 2: simple comparison by demographic group
print(
    rides.assign(high_min = (rides["pct_minority"] >= 0.5).astype(int))
    .groupby("high_min")["fare_per_mile"]
    .agg(["mean", "median", "std", "count"])
)

# Step 3: regression with controls
fit = smf.ols(
    "fare_per_mile ~ pct_minority + distance_mi + duration_min + C(hour)",
    data=rides.assign(hour = rides["pickup_at"].dt.hour)
).fit(cov_type="HC3")

print(fit.summary().tables[1])

# Step 4: interpret
coef = fit.params["pct_minority"]
print(f"\nA 10pp increase in pct_minority is associated with ")
print(f"${coef * 0.1:.3f} higher fare per mile, conditional on controls.")
```

**Plain-English answer:** "After controlling for distance, duration,
and hour of day, neighborhoods with a 10 percentage point higher
minority share have $X higher fare per mile, on average. This is
documenting *disparate impact*; the causal mechanism is not identified
in this regression."

The "this is documenting disparate impact, not the causal mechanism"
caveat is worth memorizing — it's the kind of careful language a good
applied economist uses by default.

## A 30-minute mock interview structure

If you were interviewing yourself, here's how to spend the time:

| Minutes | Task |
|---|---|
| 0-2 | Read the prompt twice. Restate it in your own words. |
| 2-5 | Look at the data: shape, columns, types, head, missing values. |
| 5-15 | Write the code, top-down. Don't optimize. |
| 15-20 | Sanity check. Compute the same answer two ways if possible. |
| 20-25 | Plot the result if applicable. |
| 25-28 | Restate the answer in plain English. |
| 28-30 | Note caveats: identification, sample, what you would do with more time. |

**The single biggest mistake** people make in this kind of interview
is jumping into code before they understand the question. The first
2 minutes (re-read, restate) are the highest-leverage minutes you'll
spend.

**The second biggest mistake** is silence. Talk while you type. The
interviewer can't tell if you're stuck or thinking; if you say "OK,
first I need to look at the columns" they'll know you have a plan.

## In the wild: one function per stage, and a check that fails loudly

The 30-minute structure above is the shape of a 200-line script too.
`run_export.py` in the BSZ reproduction ([`fhoces/opa-prop40`](https://github.com/fhoces/opa-prop40),
`bsz-analysis/py/`; module 1 explains the series) reads a workbook and
writes every number the R pipeline exports:

```python
def run(out_dir=None, db=None):
    out_dir = Path(out_dir or project_root() / "export" / "py")
    # Inputs: one extract_* per sheet
    data_sec_all = ds.extract_data_sec_all()
    shortrunseries = ds.extract_shortrunseries()
    # The shared SQL step
    db = build_workbook_db(data_sec_all, ftb_raw, path=db)
    data_sec_agg_r = read_data_sec_agg(db)
    # Computations: data frames in, data frames out, no file I/O inside
    srs_r = compute_shortrunseries(data_sec_agg_r, data_sec_top4, bci_r, shortrunseries)
    exhibits = {"shortrunseries_r": srs_r, "fig1": fg.build_fig1(srs_r)}
    # Outputs: every exhibit becomes a CSV
    for name, obj in exhibits.items():
        files += write_exhibit(name, obj, ex_dir)
    print(f"wrote {len(files)} files under {out_dir}")
    return files

if __name__ == "__main__":
    run()
```

- Defaults of `None` resolved inside the function (`out_dir or ...`), so a
  test can redirect the output without touching the defaults.
- The compute functions take data frames and return data frames and never
  touch files. That is what makes each one testable on its own.
- The `__main__` guard: `python py/run_export.py` runs the pipeline,
  `from run_export import run` does not, so the parity test can import it.

`check_common.py` holds the report that every checker in the reproduction
ends with:

```python
def write_report(title, checks, report_name):
    failures = sum(not c["ok"] for c in checks)          # R: sum(!ok)
    ...
    print(title)
    for c in checks:
        print(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['name']:<58} n={c['n']:<7} "
              f"maxdiff={fmt(c['maxdiff'])}")
        if not c["ok"]:
            print(f"        {c['note']}")
    print(f"{failures} failing check(s). Report: {out}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())          # R: quit(status = 1)
```

- A check is a dict with `name`, `ok`, `n` (cells or rows compared),
  `maxdiff` and `note`. Every comparison in the pipeline returns one, so a
  single report function serves them all.
- `{c['name']:<58}` pads the name to a column; `fmt()` prints `maxdiff`
  with `:.3g`, and `inf` when one side is missing.
- The exit code is what a Makefile or CI reads. Step 4 of the interview
  structure, "same answer two ways", is this function with one check.
- The report prints counts and maximum differences only, never a row of
  the private files, so it can be committed next to the code.

The exercise file ends with two checks on the A/B test in this form (Q7).

## What to install before the interview

```bash
pip install pandas numpy statsmodels scipy matplotlib seaborn
pip install linearmodels   # only if they ask about panel data
```

## What to know cold

- `pd.read_csv` with `parse_dates`, `dtype`, `usecols`
- `df[df["x"] > 5]`, `df.query("x > 5")`
- `df.groupby("g")["y"].agg([...])` and `.transform("mean")`
- `df.merge(other, on=..., how=...)` with `validate="..."`
- `smf.ols("y ~ x + C(g)", data=df).fit(cov_type="HC3")`
- Reading a regression summary: which numbers to report
- t-test, confidence interval, p-value semantics
- Plotting basics with `df.plot(...)` or `matplotlib.pyplot`

## Closing exercise: drill the question types

The exercise file has six end-to-end mini-scenarios. The right way to
use it: **don't read the answers until you've tried each one yourself**.
Set a 5-minute timer per question. If you can't finish in 5 minutes,
peek at the answer and move on.

After you've done them all once, do them again the next day. Spaced
repetition is how this stuff sticks.
