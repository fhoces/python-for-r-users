-- =============================================================================
-- 02_data_sec_agg.sql: data_sec_all to the yearly aggregates (course copy)
-- =============================================================================
--
-- From github.com/fhoces/opa-prop40 (bsz-analysis/sql/), the shared query
-- that both R and Python run in the paper's step 2. The two blocks below
-- are the real file; only this banner is shorter. Drill 7 asks for a pandas
-- twin of the R code this query replaced, and data/build_rtb_sample.py runs
-- this file to write the drill's expected result (the SQL is the reference
-- both languages must match).
--
-- Inputs (SQLite tables):
--   data_sec_all          the sheet's rows in sheet order (row_num), money in
--                         $ million, blank cells stored as NULL
--   data_sec_agg_exclude  forbes_id values left out of every aggregate (in
--                         the course, one invented id)
--
-- Output:
--   data_sec_agg          one row per year: the count n and 27 sums in $ billion
--
-- NULLs: SUM skips NULL, as R's sum(..., na.rm = TRUE) does. A year where
-- every value of a column is NULL would give NULL in SQL and 0 in R, so each
-- sum is wrapped in COALESCE(..., 0).
--
-- Rounding: SQLite (3.43 and later) adds up doubles with a compensated sum,
-- R adds them one by one. The two can differ in the last digit or two, about
-- 1e-13 of the value; the R tests allow 1.5e-8.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1. The rows that count (intermediate table)
--     Course: module 4 (CTE chain, NOT IN (SELECT ...)), module 5 (window
--     function ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...))
--     Beyond the course: DROP TABLE IF EXISTS, CREATE TABLE AS.
--
--     Two filters, in the order the R code applied them:
--       * kept: drop the ids on the exclusion table. NOT IN (SELECT ...)
--         would drop every row if the subquery returned a NULL id; the
--         loaders never write one.
--       * numbered / WHERE copy_num = 1: drop exact re-pastes. August's sheet
--         repeats a four-row block of 2025 rows at its tail. A row counts as a
--         copy when an earlier row (lower row_num) has the same year,
--         forbes_id and forbes_worth. This is R's
--         !duplicated(df[c("year", "forbes_id", "forbes_worth")]), which
--         also keeps the first occurrence. Two rows with the same id and year
--         but a different worth (two separately tracked Forbes amounts) are
--         both kept. PARTITION BY puts NULL worths in one group, as
--         duplicated() treats two NAs as equal.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS data_sec_all_kept;
CREATE TABLE data_sec_all_kept AS
WITH kept AS (
  SELECT *
  FROM data_sec_all
  WHERE forbes_id NOT IN (SELECT forbes_id FROM data_sec_agg_exclude)
),
numbered AS (
  SELECT
    kept.*,
    ROW_NUMBER() OVER (
      PARTITION BY year, forbes_id, forbes_worth
      ORDER BY row_num
    ) AS copy_num
  FROM kept
)
SELECT *
FROM numbered
WHERE copy_num = 1;


-- -----------------------------------------------------------------------------
-- Q2. Yearly count and sums, in $ billion
--     Course: module 3 (GROUP BY with COUNT and SUM), module 1 (COALESCE)
--
--     The R code was group_by(year) |> summarise(n = n(), across(cols,
--     \(x) sum(x, na.rm = TRUE) / 1000)). Here it is one GROUP BY with one
--     SUM per column, in the column order of the data_sec_agg sheet. Dividing
--     by 1000.0 (not 1000) keeps the division in floating point.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS data_sec_agg;
CREATE TABLE data_sec_agg AS
SELECT
  year,
  COUNT(*)                                          AS n,
  COALESCE(SUM(forbes_worth), 0) / 1000.0           AS forbes_worth,
  COALESCE(SUM(forbes_public_worth), 0) / 1000.0    AS forbes_public_worth,
  COALESCE(SUM(purchase), 0) / 1000.0               AS purchase,
  COALESCE(SUM(sale), 0) / 1000.0                   AS sale,
  COALESCE(SUM(kg), 0) / 1000.0                     AS kg,
  COALESCE(SUM(kg_long), 0) / 1000.0                AS kg_long,
  COALESCE(SUM(kg_short), 0) / 1000.0               AS kg_short,
  COALESCE(SUM(option_profit), 0) / 1000.0          AS option_profit,
  COALESCE(SUM(noneq_comp), 0) / 1000.0             AS noneq_comp,
  COALESCE(SUM(ordinary_income), 0) / 1000.0        AS ordinary_income,
  COALESCE(SUM(kg_taxable), 0) / 1000.0             AS kg_taxable,
  COALESCE(SUM(dividend), 0) / 1000.0               AS dividend,
  COALESCE(SUM(fiscal_income), 0) / 1000.0          AS fiscal_income,
  COALESCE(SUM(donation), 0) / 1000.0               AS donation,
  COALESCE(SUM(donation_deductible), 0) / 1000.0    AS donation_deductible,
  COALESCE(SUM(income_taxable), 0) / 1000.0         AS income_taxable,
  COALESCE(SUM(ca_income_tax), 0) / 1000.0          AS ca_income_tax,
  COALESCE(SUM(fed_ordinary_income_tax), 0) / 1000.0 AS fed_ordinary_income_tax,
  COALESCE(SUM(fed_preferential_tax), 0) / 1000.0   AS fed_preferential_tax,
  COALESCE(SUM(fed_income_tax), 0) / 1000.0         AS fed_income_tax,
  COALESCE(SUM(fiscal_income_tax), 0) / 1000.0      AS fiscal_income_tax,
  COALESCE(SUM(sales_tax), 0) / 1000.0              AS sales_tax,
  COALESCE(SUM(w_txt), 0) / 1000.0                  AS w_txt,
  COALESCE(SUM(w_tax_ppent), 0) / 1000.0            AS w_tax_ppent,
  COALESCE(SUM(w_pi), 0) / 1000.0                   AS w_pi,
  COALESCE(SUM(total_tax), 0) / 1000.0              AS total_tax,
  COALESCE(SUM(economic_income), 0) / 1000.0        AS economic_income
FROM data_sec_all_kept
GROUP BY year
ORDER BY year;
