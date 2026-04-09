# Module 4: Regressions and A/B Tests with statsmodels

## What this module covers

The single most important Python module for an applied policy
economist: `statsmodels`. It gives you OLS, logit, robust standard
errors, fixed effects, A/B test inference, and the **R-style formula
interface** you already know — `y ~ x1 + x2 + C(group)` works exactly
the way you'd hope.

This is the module where Python finally feels comfortable for an
econometrician.

## Two interfaces

statsmodels has two ways to fit a model:

```python
# 1. Formula interface (R-style) — usually what you want
import statsmodels.formula.api as smf
fit = smf.ols("fare_usd ~ distance_mi + C(city)", data=rides).fit()

# 2. Matrix interface
import statsmodels.api as sm
X = sm.add_constant(rides[["distance_mi"]])
y = rides["fare_usd"]
fit = sm.OLS(y, X).fit()
```

**Use the formula interface unless you have a specific reason not to.**
It's shorter, more readable, and handles categorical variables, factor
expansion, and interactions automatically.

The convention I'll use throughout the rest of this module:

```python
import statsmodels.formula.api as smf
```

## OLS with formulas

```python
# Simple regression
fit = smf.ols("fare_usd ~ distance_mi", data=rides).fit()
print(fit.summary())

# Multiple regression
fit = smf.ols("fare_usd ~ distance_mi + duration_min + surge_mult", data=rides).fit()

# With a categorical variable (R uses factor; Python wraps with C(...))
fit = smf.ols("fare_usd ~ distance_mi + C(city)", data=rides).fit()

# Interaction
fit = smf.ols("fare_usd ~ distance_mi * C(city)", data=rides).fit()
```

The formula syntax is **identical to R** — `+`, `:`, `*`, `-`, `I(...)`,
and `C(...)` for the categorical wrapper. The one difference: Python
needs `C(...)` explicitly because pandas doesn't have a native factor
type.

## Reading the summary

```python
print(fit.summary())
```

Gives you the standard regression table — coefficient, SE, t-stat,
p-value, 95% CI, R², F-stat. Plus diagnostics (Durbin-Watson,
Jarque-Bera, etc.) at the bottom.

The most useful attributes if you want to extract things:

```python
fit.params              # Series of coefficients
fit.bse                 # standard errors
fit.tvalues             # t-statistics
fit.pvalues             # p-values
fit.conf_int()          # confidence intervals
fit.rsquared            # R²
fit.rsquared_adj
fit.nobs                # n
fit.resid               # residuals
fit.fittedvalues        # ŷ
```

For a dataframe-shaped summary:

```python
import pandas as pd
pd.DataFrame({
    "coef": fit.params,
    "se":   fit.bse,
    "t":    fit.tvalues,
    "p":    fit.pvalues
}).round(3)
```

## Robust standard errors

The `cov_type` argument when fitting:

```python
# Heteroskedasticity-robust (HC3 is the modern default)
fit_hc3 = smf.ols("y ~ x", data=df).fit(cov_type="HC3")

# Cluster-robust
fit_cluster = smf.ols("y ~ x", data=df).fit(
    cov_type="cluster",
    cov_kwds={"groups": df["driver_id"]}
)
```

dplyr / R equivalent: `lm_robust(..., clusters = driver_id)` from the
`estimatr` package, or `coeftest(fit, vcov = vcovHC(fit, type = "HC3"))`.

## Fixed effects

The "two-way fixed effects" or absorbed-effects pattern. Two ways:

### 1. With `C()` (small N of fixed effects)

```python
fit = smf.ols(
    "fare_usd ~ distance_mi + C(driver_id) + C(city)",
    data=rides
).fit()
```

This works but is slow if you have thousands of fixed effects, because
statsmodels will literally create a column for each.

### 2. With `linearmodels` (for many fixed effects)

```python
from linearmodels.panel import PanelOLS

# Convert to a panel data structure
panel = rides.set_index(["driver_id", "pickup_at"])
fit = PanelOLS.from_formula(
    "fare_usd ~ distance_mi + EntityEffects + TimeEffects",
    data=panel
).fit(cov_type="clustered", cluster_entity=True)
```

`linearmodels` is the third-party package econometricians use for
panel data. It's not installed by default but it's standard at any
academic-research-adjacent shop.

## Logit / Probit / GLM

```python
# Logistic regression
logit = smf.logit("accepted ~ distance_mi + C(city)", data=requests).fit()

# Probit
probit = smf.probit("accepted ~ distance_mi", data=requests).fit()

# GLM with custom family / link
glm = smf.glm(
    "accepted ~ distance_mi",
    data=requests,
    family=sm.families.Binomial()
).fit()
```

The output is the same shape as `ols`. Coefficients are on the
log-odds scale; `np.exp(fit.params)` gives odds ratios.

## A/B test inference

The most common interview question. Three ways to answer "is the
treatment effect statistically significant":

### Way 1: t-test on the means

```python
from scipy import stats

t_stat, p_value = stats.ttest_ind(
    ab.loc[ab["treatment"] == 1, "spend_usd"],
    ab.loc[ab["treatment"] == 0, "spend_usd"],
    equal_var=False  # Welch's t-test, the modern default
)
```

### Way 2: OLS regression (the econometrician's t-test)

```python
fit = smf.ols("spend_usd ~ treatment", data=ab).fit()
print(fit.summary())
```

The coefficient on `treatment` is the average treatment effect; its SE
and p-value answer the same question as the t-test. **Equivalent in
expectation, identical with HC2 or HC3 SEs.**

### Way 3: OLS with controls

```python
fit = smf.ols("spend_usd ~ treatment + C(city)", data=ab).fit()
```

Adds covariates to soak up variance. The treatment estimate is unbiased
(because of randomization) but more precise.

For the interview answer, do version 2 first. It generalizes to fixed
effects, clustering, interactions, and is the closest thing to "the
right answer" in modern econometrics.

## Confidence intervals on the treatment effect

```python
ate     = fit.params["treatment"]
ate_se  = fit.bse["treatment"]
ate_ci  = fit.conf_int().loc["treatment"]

print(f"Treatment effect: {ate:.3f} (SE = {ate_se:.3f})")
print(f"95% CI: [{ate_ci[0]:.3f}, {ate_ci[1]:.3f}]")
```

## Difference-in-differences

```python
# Suppose city A had a policy change at time t=10, city B did not
df["post"]      = (df["t"] >= 10).astype(int)
df["treated"]   = (df["city"] == "A").astype(int)
df["did"]       = df["post"] * df["treated"]

fit = smf.ols(
    "outcome ~ post + treated + did + C(city) + C(t)",
    data=df
).fit(cov_type="cluster", cov_kwds={"groups": df["city"]})

# The coefficient on `did` is the DiD estimate
```

The DiD coefficient is the interaction term `did = post * treated`.
The two-way fixed effects (city + time) absorb the level effects, so
`did` cleanly identifies the treatment effect under the parallel-trends
assumption.

## Predict on new data

```python
new_data = pd.DataFrame({"distance_mi": [3, 5, 10]})
preds = fit.predict(new_data)
```

For prediction with confidence intervals:

```python
predictions = fit.get_prediction(new_data).summary_frame()
# Returns: mean, mean_se, mean_ci_lower, mean_ci_upper, obs_ci_*
```

## Common traps

### 1. The formula API copies the data

`smf.ols(...)` makes a copy of the relevant columns. This is fine for
most data sizes but can be slow for huge datasets. The matrix API is
faster for big data.

### 2. NaNs are dropped silently

If any row has NaN in any of the formula's columns, statsmodels drops
it. Compare `fit.nobs` to `len(data)` to see how many rows you lost.
This is the source of "my coefficients changed when I added a control"
mysteries.

### 3. Categorical reference level

`C(city)` uses the first city alphabetically as the reference. To
change it: `C(city, Treatment(reference="SF"))`.

### 4. Cluster argument is a Series, not a column name

```python
# WRONG
.fit(cov_type="cluster", cov_kwds={"groups": "driver_id"})

# RIGHT
.fit(cov_type="cluster", cov_kwds={"groups": df["driver_id"]})
```

## Interview questions

1. **OLS of `fare_usd` on `distance_mi + duration_min + C(city)`**, with
   robust SEs.
2. **Compute the average treatment effect, its SE, and 95% CI** from
   `data/ab_test.csv`.
3. **Logit of `is_minority` on rider features** (just to practice the
   syntax — note that this is *not* a fairness audit, that's Module 7
   of the ML course).
4. **Two-way fixed effects regression**: `fare_usd ~ distance_mi +
   C(driver_id) + C(city)`. Get cluster-robust SEs.
5. **Difference-in-differences on a synthetic panel**: identify the DiD
   coefficient and interpret it.
