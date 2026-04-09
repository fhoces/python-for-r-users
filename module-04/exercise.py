"""
Module 4: Regressions and A/B Tests with statsmodels -- Exercise

Run with: python module-04/exercise.py

Requires: pandas, numpy, statsmodels, scipy
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats

rides = pd.read_csv("data/rides.csv", parse_dates=["pickup_at"])
ab    = pd.read_csv("data/ab_test.csv")


# =============================================================================
# Q1. OLS of fare on distance + duration + city, robust SEs
# =============================================================================

fit = smf.ols(
    "fare_usd ~ distance_mi + duration_min + C(city)",
    data=rides
).fit(cov_type="HC3")

print("Q1. OLS results")
print(pd.DataFrame({
    "coef": fit.params,
    "se":   fit.bse,
    "t":    fit.tvalues,
    "p":    fit.pvalues
}).round(4))
print(f"R² = {fit.rsquared:.4f}, n = {int(fit.nobs)}")


# =============================================================================
# Q2. A/B test: average treatment effect, SE, 95% CI
# =============================================================================

# OLS approach
fit_ab = smf.ols("spend_usd ~ treatment", data=ab).fit(cov_type="HC3")
ate    = fit_ab.params["treatment"]
ate_se = fit_ab.bse["treatment"]
ate_ci = fit_ab.conf_int().loc["treatment"]

print("\nQ2. A/B test results")
print(f"  ATE     : {ate:.4f}")
print(f"  SE      : {ate_se:.4f}")
print(f"  95% CI  : [{ate_ci[0]:.4f}, {ate_ci[1]:.4f}]")
print(f"  p-value : {fit_ab.pvalues['treatment']:.4f}")

# Sanity check with t-test
t_stat, p_val = stats.ttest_ind(
    ab.loc[ab["treatment"] == 1, "spend_usd"],
    ab.loc[ab["treatment"] == 0, "spend_usd"],
    equal_var=False
)
print(f"  Welch t : {t_stat:.4f}, p = {p_val:.4f}")


# =============================================================================
# Q3. Logit (just for syntax)
# =============================================================================

# We'll create a binary outcome to demonstrate the syntax
rides["is_long_trip"] = (rides["distance_mi"] > 5).astype(int)

logit = smf.logit(
    "is_long_trip ~ duration_min + surge_mult + C(city)",
    data=rides
).fit(disp=False)

print("\nQ3. Logit on is_long_trip")
print(pd.DataFrame({
    "coef":       logit.params,
    "odds_ratio": np.exp(logit.params),
    "p":          logit.pvalues
}).round(4))


# =============================================================================
# Q4. Add controls to the A/B test (variance reduction)
# =============================================================================

fit_ab_ctrl = smf.ols("spend_usd ~ treatment + C(city)", data=ab).fit(cov_type="HC3")

print("\nQ4. A/B test with city fixed effects (variance reduction)")
print(f"  ATE     : {fit_ab_ctrl.params['treatment']:.4f}")
print(f"  SE      : {fit_ab_ctrl.bse['treatment']:.4f}")
print(f"  Reduction in SE vs naive: "
      f"{(1 - fit_ab_ctrl.bse['treatment'] / ate_se):.1%}")


# =============================================================================
# Q5. Difference-in-differences on synthetic data
# =============================================================================

np.random.seed(2026)
n = 4000
panel = pd.DataFrame({
    "city":      np.random.choice(["A", "B"], n),
    "month":     np.random.choice(range(1, 13), n),
})
panel["treated"] = (panel["city"] == "A").astype(int)
panel["post"]    = (panel["month"] >= 7).astype(int)
panel["did"]     = panel["treated"] * panel["post"]

# True effect: 5 dollar bump for treated × post
panel["outcome"] = (
    20 + 2 * panel["treated"] + 1 * panel["post"]
    + 5 * panel["did"]
    + np.random.normal(0, 3, n)
)

did_fit = smf.ols(
    "outcome ~ treated + post + did + C(city) + C(month)",
    data=panel
).fit(cov_type="cluster", cov_kwds={"groups": panel["city"]})

print("\nQ5. DiD estimate")
print(f"  Coefficient on `did`: {did_fit.params['did']:.3f}")
print(f"  SE                  : {did_fit.bse['did']:.3f}")
print(f"  p-value             : {did_fit.pvalues['did']:.4f}")
print(f"  True effect         : 5.000")
