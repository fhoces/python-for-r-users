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

## The four drills

| Drill | Function | Real file it simplifies | Graded on |
|---|---|---|---|
| Q1 | `load_csv(con, csv_path, table, columns, index_on, chunksize)` | `load_bundle.py` | row count, NULL counts, distinct values (trimming), sums, column types, indexes |
| Q2 | `run_and_export(con, sql_file, tables, out_dir, order_by)` | `run_sql.py` | byte-identical CSVs, and the sort really coming from `order_by` |
| Q3 | `compare(ours, key, key_cols, num_cols, tol)` | `check_rtb_ca.py` | rows on each side, cells off, max difference, ok, on a pretend authors' sheet with a vintage gap |
| Q4 | `parity(dir_a, dir_b, tables, tol)` | `cmp_parity()` in `check_rtb_ca.py` | an R-style export (same numbers, different text) passes, a changed value fails |

```sh
python data/build_rtb_sample.py              # once: data/*.csv and data/expected/
python module-07/check.py                    # grades exercise.py: all four fail as delivered
python module-07/check.py module-07/solution.py   # the reference passes all four
```

Then listen to `module-07/lesson/python-around-sql.m4b`, take the walking quiz (link in
`module-07/quiz/README.md`), and read the real files in
[`opa-prop40/bsz-analysis/py/`](https://github.com/fhoces/opa-prop40/tree/main/bsz-analysis/py).
