# Module 7: Loading, Running SQL and Checking a Reproduction

## Why this module breaks the pattern

Modules 1 to 5 use the ride-sharing data, and module 6 reads a codebase you did not
write. This one is about the Python that sits **around** a SQL file in a real
reproduction: load raw CSVs into SQLite, run a shared `.sql` file, export the result
deterministically, and check it against someone else's numbers. The source is
[`fhoces/opa-prop40`](https://github.com/fhoces/opa-prop40), folder `bsz-analysis/py/`
(four Python files) plus its R twin `R/run_sql.R`. The data there are confidential, so
the drills run on a synthetic panel in the same shape (`python data/build_rtb_sample.py`:
invented people, random-walk fortunes). The SQL itself is covered in the SQL course
(sql-industry-prep, module 6); here it is a black box that builds four tables.
[Part 2](#part-2-translating-an-r-pipeline-into-a-python-twin) moves to the paper's
second step, where a whole R pipeline has a Python twin, and drills the translation:
openpyxl cell reading, pandas versions of the R idioms, and the parity test.

The pipeline, as the real files split it:

```
bundle_paths.py   where things live (and a useful error when they are missing)
load_bundle.py    raw CSV / xlsx  ->  SQLite tables            (drill 1)
run_sql.py        .sql file       ->  tables  ->  sorted CSVs  (drill 2)
check_rtb_ca.py   our CSVs vs the answer keys, and R vs Python (drills 3 and 4)
R/run_sql.R       the same .sql file from R, for the parity check
```

## `bundle_paths.py`: one place that knows where things are

**What it does.** Every path the other scripts need comes from one small module:
the bundle root, the SQLite file, the export folder, two private config files.

**The Python idioms.**

- **`pathlib.Path` and `/`.** `Path(__file__).resolve().parent.parent` is "the folder
  that holds `py/`". Paths are then built with the `/` operator:
  `BSZ_DIR / "data-raw" / "bundle.sqlite"`. R analogue: `here::here("data-raw",
  "bundle.sqlite")` or `file.path()`, except a `Path` is an object with methods
  (`.exists()`, `.is_dir()`, `.rglob()`, `.read_text()`).
- **An environment variable with a default.** `os.environ.get("BSZ_BUNDLE_DIR", "")`
  returns the variable or `""`, and the code falls back to a default path. R:
  `Sys.getenv("BSZ_BUNDLE_DIR", unset = "")`. This lets a git worktree, or a co-author,
  point at a bundle elsewhere without editing code.
- **Raise with a message that says what to do.** When the bundle is missing,
  `bundle_dir()` raises `FileNotFoundError(f"Author bundle not found at {path}. ...
  set the {ENV_VAR} environment variable ...")`. The message names the path it tried
  and the fix. R: `stop()` with the same kind of message. A bare `KeyError` three
  functions later is the alternative you want to avoid.
- **Find a file by name, and insist on exactly one.** `find_in_bundle()` uses
  `root.rglob(basename)` and raises unless there is exactly one hit, so a duplicated
  file in the bundle fails loudly instead of silently picking the first.
- **Comment lines in a small CSV.** `read_commented_csv()` drops lines starting with `#`
  before handing the rest to `csv.DictReader`, so a config file can document its own
  schema. (The committed `*.example.csv` files do exactly that.)

## `load_bundle.py`: raw files into SQLite

**What it does.** Builds `data-raw/bundle.sqlite` with one loader function per table,
registered in a `LOADERS` dict. Each loader drops and recreates the one table it owns,
so the script is safe to re-run (idempotent).

**Reading a big CSV in pieces.** The Forbes file has about 5.9 million rows. The real
loader reads it with the standard library's `csv.reader`, appends converted rows to a
list, and every `BATCH = 100_000` rows hands the list to `con.executemany(insert, batch)`
and starts a new one. Memory stays flat whatever the file size. The pandas form of the
same idea, which drill 1 uses, is `pd.read_csv(path, chunksize=5000)`: it returns an
iterator of DataFrames instead of one DataFrame. R analogue:
`readr::read_csv_chunked(path, callback = ...)`.

**Empty string, NaN and None: what reaches SQLite.** The bundle's CSVs write a missing
value as an empty field. Three things can happen to it:

| You read with | An empty field becomes | Stored in SQLite as |
|---|---|---|
| `csv.reader`, no conversion | `""` (an empty string) | the text `''`, which is **not** NULL |
| `pd.read_csv` defaults | `NaN`, also inside text columns | NULL, but the strings `"NA"`, `"null"` and `"NaN"` also become NaN, and text columns hold a mix of strings and floats |
| `dtype=str, keep_default_na=False`, then `v if v != "" else None` | `None` | NULL, and nothing else is touched |

The real loader converts explicitly (`_text()` and `_real()` return `None` for `""`),
and so does the drill. Explicit is the point: SQL's aggregates skip NULL the way R's
`na.rm = TRUE` does, but an empty string is a value, so it would be counted by
`COUNT(col)` and break `SUM`.

**Trimming like readr.** `readr::read_csv` trims leading and trailing spaces by default
(`trim_ws = TRUE`). Python's readers do not. The real loader calls `v.strip(" \t")` on
every field, because many `source` values in the Forbes file end in a space; without it,
"software" and "software " are two different industries. (The synthetic CSV has the same
trailing spaces, so drill 1 catches a loader that forgets.)

**Parameter binding, not string formatting.** The insert statement is built once with
`?` placeholders, `INSERT INTO t (a, b, c) VALUES (?, ?, ?)`, and the values travel
separately in `executemany`. SQLite then handles quoting and types. Building
`f"VALUES ('{name}', {worth})"` by hand breaks on the first name with an apostrophe,
turns `None` into the string `'None'`, and opens the door to SQL injection. R:
`DBI::dbExecute(con, sql, params = list(...))` or `dbAppendTable()`. (`DataFrame.to_sql`
is the one-line alternative; the real loader avoids it so it controls types and NULLs
exactly.)

**Indexes after the load.** The two `CREATE INDEX` statements run after all rows are in.
Building an index once over finished data is much faster than updating it on every
insert. Same reason the loader sets `PRAGMA journal_mode = OFF` and
`synchronous = OFF`: the database is a rebuildable artifact, so it trades crash safety
for speed.

**Timing and a sanity count.** `main()` times each loader with `time.time()`, then runs
`SELECT COUNT(*)` and raises if it differs from the number of rows inserted. Cheap, and
it catches a silent partial load.

## `run_sql.py`: run a shared `.sql` file and export tables

**What it does.** `python py/run_sql.py sql/01_rtb_ca.sql --export t1 t2 t3` runs the
file and writes each named table to `data-raw/sql-out/py/<table>.csv`.

**`executescript` versus `execute`.** `con.execute(sql)` runs exactly one statement and
raises if you give it two. `con.executescript(text)` runs a whole file of statements,
separated by semicolons, in order, and stops at the first error (statements before it
have already run). It first commits any open transaction. Because the shared file has
several `DROP TABLE` / `CREATE TABLE ... AS` blocks, `executescript` is the right call.
It cannot take parameters, so it is for trusted files, never for user input.

**Reading results back.** `cur = con.execute("SELECT * FROM t ORDER BY ...")`, then
`cur.description` gives the column names and `cur.fetchall()` the rows as tuples.
`pd.read_sql("SELECT ...", con)` gives a DataFrame in one line; the real file stays with
tuples so it controls the text format.

**Deterministic export.** Two runs, or two languages, must write byte-identical files,
so nothing is left to chance:

- **Sort by a key, always.** `EXPORT_ORDER` maps each table to an `ORDER BY` clause
  (with a tie-breaker), and the export query uses it. A table with no entry is sorted
  by all its columns. Never rely on the order a table happens to store its rows in.
- **Floats with `repr()`.** `repr(x)` is the shortest text that reads back as the same
  double (`0.1`, not `0.1000000000000000055511151231257827`). `str()` is the same in
  Python 3, but `f"{x:.6f}"` or pandas' `float_format` would round.
- **NULL as an empty field**, `lineterminator="\n"`, and `newline=""` when opening the
  file (otherwise Windows doubles the line ends).

**`argparse`.** `p.add_argument("sql_file")` is a required positional argument;
`p.add_argument("--export", nargs="*", default=[])` takes any number of table names;
`--db` and `--out` override the defaults. `p.parse_args(argv)` with `argv=None` reads
the real command line, and a test can pass a list instead. R has no built-in
equivalent; `commandArgs(trailingOnly = TRUE)` plus hand parsing (as `run_sql.R` does)
or the `optparse` package.

## `check_rtb_ca.py`: is our table the same as theirs?

**What it does.** Compares the three exports with the answer keys (the authors'
private sheets and the public workbook) and with the R exports, writes a Markdown report
with counts and maximum differences only, prints one PASS or FAIL line per check, and
exits with code 1 if anything fails.

**Align on keys, never on row position.** Each comparison builds a dict keyed on the
natural key (`forbes_id` within a date, `industries`, or `date`), then compares the key
sets: ids only in ours, only in theirs, and the common ones cell by cell. The pandas
version of the same idea, which drill 3 uses, is a full outer join with an indicator:

```python
m = ours.merge(key, on=["date"], how="outer", suffixes=("_ours", "_key"), indicator=True)
m["_merge"].value_counts()   # both / left_only / right_only
```

`indicator=True` adds a `_merge` column saying where each row came from. R analogue:
`dplyr::full_join()` plus `anti_join()` both ways, or a flag column you add before the
join.

**Tolerance versus exact equality.** Counts and text must match exactly. Numbers pass
if `abs(a - b) <= TOL` with `TOL = 1e-6` against the answer keys, `1e-9` for R versus
Python, and `0.005` for cells that were typed with two decimals. Exact equality fails on
harmless noise: summing the same numbers in a different order changes the last digits.
R analogue: `all.equal(a, b, tolerance = 1e-6)`, but that compares a mean relative
difference. The checker uses the largest absolute difference, which in R is
`max(abs(a - b)) <= 1e-6`. A tolerance is not a fudge factor: a missing person changes a count and fails
no matter how wide the tolerance is.

**Rows on one side only.** For the daily table, dates only in ours are reported but do
not fail the check (a newer data file has more days); dates only in the key do fail.
Drill 3's `compare()` follows the same rule.

**Privacy in the report.** Rows of the private sheets are never printed, only counts,
row totals and maximum absolute differences. A useful habit for any check against data
you may not publish.

**Exit codes as test results.** `main()` returns `1 if failures else 0` and the script
ends with `sys.exit(main())`. A shell, a Makefile or CI can then branch on the result
(`python py/check_rtb_ca.py && echo ok`). R: `quit(status = 1)`.

## `R/run_sql.R`: the same file from R, as the contrast

The R twin runs the identical `.sql` file and writes identical CSVs, so the parity check
can compare two independent implementations of everything except the SQL.

- **No `executescript` in DBI.** `DBI::dbExecute()` runs one statement. So `run_sql.R`
  splits the file itself with `sql_split_statements()`, a small state machine that walks
  the text character by character and splits at each `;` that is real code, ignoring
  semicolons inside `-- comments`, `/* comments */`, strings and quoted identifiers.
- **Formatting doubles like Python's `repr()`.** `.format_double()` tries
  `sprintf("%.15g")`, then 16, then 17 significant digits, keeping the first that reads
  back as the same number, and adds `.0` to integer-looking values. R's text-to-number
  parser is not always correctly rounded in the 16th digit, so R sometimes writes 17
  digits where Python writes 16. The files can differ as text while holding the same
  doubles. That is why the parity check parses numbers instead of comparing text, which
  is drill 4.
- **Defines functions, runs only under `Rscript`.** The entry point is guarded by
  `if (sys.nframe() == 0L && !interactive())`, the R version of Python's
  `if __name__ == "__main__":`, so `_targets.R` and the tests can `source()` the file
  without running it.

## Part 2: translating an R pipeline into a Python twin

Part 1 was the Python **around** one SQL file. Part 2 is a whole R pipeline rewritten in
Python: the paper's second step (the public workbook to every number the R side exports),
in `bsz-analysis/py/` of the same repo. The R pipeline stays the reference. The Python
version exists to check it, so it is written to be compared, not to be idiomatic.

### Function by function, file by file

Each Python file is the twin of one R file, with the same function names:
`R/excel_cells.R` and `py/excel_cells.py` both define `xls_cell()`, `R/compute_pareto.R`
and `py/compute_pareto.py` both define `compute_pareto_missing()`, and so on across the files of step 2.
`py/run_export.py` plays the role of `_targets.R`: it calls everything in order and writes
`export/py/`. The rule is mirroring, not redesign:

- **Same names, same order, same shapes.** A data frame keeps R's column names and column
  order; R's named list becomes a dict with the same keys. Where the R code reproduces a
  spreadsheet quirk (an average row computed the sheet's way), the twin reproduces the
  same quirk, and a change to one side is a change to both.
- **Comments carry the R index.** Year-aligned R vectors are 1-based and numpy arrays are
  0-based, so the 2021 slot of a 2018-based panel is `x[4]` in R and `x[3]` in Python.
  The twin keeps the R index in a comment wherever it matters (`# R: anchor_i is a + 1`).
- **What is not twinned is listed.** Rendering (gt tables, ggplot figures), the report's
  code listings and an R-only test helper stay in R; the twin produces the **data**
  behind each table and figure, which is what the numbers are.
- **Literals that vary live in one file.** `vintage.py` (twin of `R/vintage.R`) holds every
  column letter and row offset that differs between the May and August workbooks, keyed
  by an environment variable, `BSZ_VINTAGE`. Both languages switch the same way.

### Reading cells with openpyxl, the way readxl does

The R side reads many sheets **by position**: `read_sheet()` returns the whole sheet with
columns named A, B, C and rows numbered as in Excel, and `xls_cell(df, "G16")` reads one
cell. The Python twin, `ingest_excel.read_sheet()`, does the same with openpyxl:

- **`openpyxl.load_workbook(path, data_only=True, read_only=True)`.** `data_only=True`
  returns each formula cell's cached value, the number Excel last computed, which is what
  readxl reads. Without it you get the formula text (`"=SUM(B4:B9)"`). A file saved by a
  program that never calculated has no cached values, and `data_only=True` then gives
  `None`. `read_only=True` streams the sheet, which is faster for big ones.
- **`ws.iter_rows(values_only=True)`** yields one tuple of raw values per row: `str`,
  `int`, `float`, `bool`, `None`, or a `datetime` for a date cell.
- **A positional DataFrame.** Columns named by `excel_col_letters()` (A to Z, then AA, AB)
  and `df.index = range(1, n + 1)`, so `df.at[16, "G"]` is cell G16, the way `df$G[16]` is
  in R. Python's `df.iloc[15, 6]` would be the same cell, but the twin's job is to look
  like the R line it mirrors.
- **readxl's habits, reproduced.** It drops trailing empty rows and columns (a formatted
  but empty cell at the bottom makes openpyxl report extra rows), and in a text column it
  reports a date as its Excel serial number (2018-12-31 is 43465, days since 1899-12-30).
  The twin converts each `datetime` back to that number.
- **Number parsing can differ in the last digit.** readxl keeps the 17-digit text of a
  number and R parses it with its own routine; openpyxl uses Python's `float()`, which is
  correctly rounded. The two can differ by a unit in the last place, about 1e-16 of the
  value. This is one reason the parity test needs a tolerance.

### A cell as R's `as.numeric()` sees it

R reads a mixed column as character and calls `suppressWarnings(as.numeric(v))`, so
anything that is not a number becomes `NA`. The twin's `to_num()` returns `NaN` for the
same cases, and the cases are not the ones `float()` would pick:

| Cell | R `as.numeric()` | Python `float()` | `to_num()` |
|---|---|---|---|
| `" 97.293 "` | 97.293 | 97.293 | 97.293 |
| `"1_000"` | NA | 1000.0 | NaN |
| `"n/a"`, `"1,234"` | NA | ValueError | NaN |
| a `TRUE` cell (text `"TRUE"` in R) | NA | 1.0 (`float(True)`) | NaN |
| empty | NA | TypeError on `None` | NaN |

`xls_cell()` parses the address with a regular expression (`^([A-Z]+)([0-9]+)$`) and
returns NaN for an address outside the sheet, as R's `df$G[999]` returns `NA`.

### pandas and numpy equivalents of the R idioms used

| R | Python twin | The trap |
|---|---|---|
| `x %in% ids`, `!x %in% ids` | `s.isin(ids)`, `~s.isin(ids)` | `not` and `!` do not work on a Series; use `~` |
| `!duplicated(pick(a, b, c))` | `~df.duplicated(subset=[a, b, c], keep="first")` | `drop_duplicates()` with no subset compares every column |
| `n()` | `groupby(...).size()` | `.count()` counts non-missing values, like SQL's `COUNT(col)` |
| `sum(x, na.rm = TRUE)` | `np.nansum(x)`, or pandas `.sum()` | `.sum(min_count=1)` gives NaN for an all-NaN group; `np.sum` gives NaN if any value is NaN |
| `sum(x)` of a short vector | a left-to-right loop | numpy sums pairwise, so the last digit can differ |
| `x[4]` (1-based) | `x[3]` | off by one, silently |
| `c(x[-1], 0)` (drop the first, pad with 0) | `np.append(x[1:], 0)` | in Python `x[-1]` is the **last** element |
| `seq(0, 0.2, by = 0.001)` | `0 + np.arange(n + 1) * 0.001` | `np.arange(0, 0.2, 0.001)` stops before 0.2 (200 values, not 201); with a nonzero start its rounded step can move the last digit |
| `bind_rows()` of frames with different columns | `pd.concat()` | both fill the gaps with missing values |
| `grepl("^2019.*average", x)` | `re.search(r"^2019.*average", s)` | R's `grepl` is vectorised; map it over the Series |

Drill 7 uses the first four rows: it twins the R version of `compute_data_sec_agg()`
(the dplyr code that `02_data_sec_agg.sql` later replaced) and is graded against that SQL
file, run on the same sheet.

### The parity test: two export folders, one relative tolerance

`python py/run_export.py` writes every number the Python twin computes to `export/py/`
(CSV, floats with `repr()`, `NA` for a missing value). `tests/testthat/test-py-parity.R`
compares each file with its R counterpart: the export contract with `export/r/`, the site
data with `site/data/`, and every computed table with the R snapshots. The comparison,
`compare_parity_frames()`, is strict about everything except the last digits:

- **Same column names, same number of rows.** Otherwise the output fails outright.
- **Missing values in the same cells.** `NA` in R and a number in Python (or the reverse)
  fails, whatever the tolerance.
- **Text exactly.** Labels, years written as text, file names.
- **Numbers within a relative tolerance:** `|python - r| <= 1e-9 * max(1, |r|)`.

Why relative: one unit in the last place grows with the number. At 2e12 (a dollar total,
like the drill's tax table) it is about 2e-4, so an **absolute** 1e-9 would fail on pure
rounding. Why the `max(1, ...)` floor: some outputs are near zero by construction (a
decomposition check that should be 0 and holds 1e-13), and a pure relative test would turn
a 3e-16 gap into a 0.3% "difference". Why 1e-9: the real gaps are about 1e-16 of the value (the parsing
difference above, R's `mean()` taking a second correction pass, numpy's pairwise sums),
while the smallest digit the paper prints is 1e-3. A real bug moves a number by far more
than 1e-9.

Three habits of the real test worth copying. It **skips, never fails**, when `export/py/`
is missing or was built from the other workbook vintage, so an R-only run is not blocked.
It **flags files on one side only** (an extra Python file with no R snapshot fails). And
`export/py/` is committed, so the test runs where Python is not installed. On the day it
was written, 50 outputs and 53,855 numbers agreed to 5e-15 relative, and the site's data
file was byte-identical.

## The eight drills

| Drill | Function | Real file it simplifies | Graded on |
|---|---|---|---|
| Q1 | `load_csv(con, csv_path, table, columns, index_on, chunksize)` | `load_bundle.py` | row count, NULL counts, distinct values (trimming), sums, column types, indexes |
| Q2 | `run_and_export(con, sql_file, tables, out_dir, order_by)` | `run_sql.py` | byte-identical CSVs, and the sort really coming from `order_by` |
| Q3 | `compare(ours, key, key_cols, num_cols, tol)` | `check_rtb_ca.py` | rows on each side, cells off, max difference, ok, on a pretend authors' sheet with a vintage gap |
| Q4 | `parity(dir_a, dir_b, tables, tol)` | `cmp_parity()` in `check_rtb_ca.py` | an R-style export (same numbers, different text) passes, a changed value fails |
| Q5 | `read_sheet(path, sheet)` (and `excel_col_letters(n)`) | `ingest_excel.py` | shape after dropping trailing empty rows, columns A to AB, index from 1, raw cells, a date as 43465.0 |
| Q6 | `xls_cell(df, addr)` (and `to_num(v)`) | `excel_cells.py` | 18 addresses: numbers, text numbers with spaces, `"1_000"`, `"n/a"`, `TRUE`, a date, outside the sheet |
| Q7 | `compute_data_sec_agg(data_sec_all, exclude_ids, cols)` | the dplyr code before `02_data_sec_agg.sql` | the SQL file's result at 1e-9 relative: exclusion, re-pasted rows (one with no worth), `n`, an all-missing column |
| Q8 | `parity_rel(dir_r, dir_py, tol)` | `helper-py-parity.R` | an R folder against a good Python one (rounding noise at 2e12 and near 0: must pass) and a bad one (a 1e-7 gap, a missing file, an extra file, NA versus 0: must fail) |

```sh
python data/build_rtb_sample.py              # once: data/*.csv, data/workbook_sample.xlsx, data/expected/
python module-07/check.py                    # grades exercise.py: all eight fail as delivered
python module-07/check.py module-07/solution.py   # the reference passes all eight
```

Then listen to `module-07/lesson/python-around-sql.m4b`, take the walking quiz (link in
`module-07/quiz/README.md`), and read the real files in
[`opa-prop40/bsz-analysis/py/`](https://github.com/fhoces/opa-prop40/tree/main/bsz-analysis/py).
