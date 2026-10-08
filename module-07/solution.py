"""
Module 7: Loading, Running SQL and Checking a Reproduction -- reference answers

The eight drill functions of module-07/exercise.py, filled in. Drills 1 to 4
follow the real files in github.com/fhoces/opa-prop40 (bsz-analysis/py/):
load_bundle.py, run_sql.py and check_rtb_ca.py, simplified to one table each
and, for the comparison, rewritten with pandas merge so the R mental model
(dplyr joins) carries over. Drills 5 to 8 follow the Python twin of the R
pipeline in the same folder: ingest_excel.py, excel_cells.py,
compute_data_sec_agg.py and the R vs Python parity test.

Grade them (they must pass every drill):
    python module-07/check.py module-07/solution.py

data/build_rtb_sample.py also imports this file to write data/expected/.
"""
import csv
import datetime
import math
import re
import sqlite3
from pathlib import Path

import openpyxl
import pandas as pd


# =============================================================================
# Q1. A chunked loader with empty-to-NULL
# =============================================================================
def load_csv(con, csv_path, table, columns, index_on=(), chunksize=5000):
    """Load csv_path into a new SQLite table and return the number of rows.

    columns: list of (name, sqlite_type) pairs, in file order; types are TEXT,
    REAL or INTEGER. Every field is trimmed of leading and trailing spaces and
    tabs (as readr::read_csv does), an empty field becomes NULL (None), REAL
    fields become floats and INTEGER fields ints. The table is dropped and
    recreated, rows are inserted chunk by chunk with parameter binding, and
    an index is created on each column in index_on AFTER the load.
    """
    names = [n for n, _ in columns]
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"CREATE TABLE {table} (" + ", ".join(f"{n} {t}" for n, t in columns) + ")")
    insert = f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join('?' * len(names))})"
    casts = {"REAL": float, "INTEGER": lambda v: int(float(v)), "TEXT": str}
    cast = [casts[t] for _, t in columns]
    n = 0
    # dtype=str + keep_default_na=False: every cell arrives as the text in the
    # file, and an empty cell stays "" instead of turning into NaN.
    for chunk in pd.read_csv(csv_path, dtype=str, keep_default_na=False, chunksize=chunksize):
        if list(chunk.columns) != names:
            raise ValueError(f"Unexpected header in {csv_path}: {list(chunk.columns)}")
        rows = []
        for rec in chunk.itertuples(index=False):
            row = []
            for f, v in zip(cast, rec):
                v = v.strip(" \t")
                row.append(f(v) if v != "" else None)
            rows.append(row)
        con.executemany(insert, rows)
        n += len(rows)
    for col in index_on:
        con.execute(f"CREATE INDEX idx_{table}_{col} ON {table} ({col})")
    con.commit()
    return n


# =============================================================================
# Q2. Run a .sql file and export tables deterministically
# =============================================================================
def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(v)
    return str(v)


def run_and_export(con, sql_file, tables, out_dir, order_by):
    """Run sql_file with executescript, then write each table to out_dir/<table>.csv.

    Format: a header row with the column names, then the rows sorted by
    order_by[table] (an ORDER BY clause), NULL written as an empty field,
    floats written with repr(), "\\n" line endings. Returns {table: n_rows}.
    """
    con.executescript(Path(sql_file).read_text(encoding="utf-8"))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for t in tables:
        cur = con.execute(f"SELECT * FROM {t} ORDER BY {order_by[t]}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(out_dir / f"{t}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cols)
            for r in rows:
                w.writerow([_fmt(v) for v in r])
        counts[t] = len(rows)
    return counts


# =============================================================================
# Q3. Compare a result with an answer key, aligned on a key
# =============================================================================
def compare(ours, key, key_cols, num_cols, tol=1e-6):
    """Align two DataFrames on key_cols and compare num_cols within tol.

    Returns a dict:
      n_common      rows present on both sides
      only_ours     rows only in ours (reported, not a failure: a newer
                    data vintage can have extra rows)
      only_key      rows only in the key (a failure)
      cells_off     numeric cells on common rows that differ by more than tol,
                    or are missing on exactly one side
      max_abs_diff  largest absolute difference over common rows (0.0 if none)
      ok            only_key == 0 and cells_off == 0
    """
    m = ours.merge(key, on=key_cols, how="outer", suffixes=("_ours", "_key"),
                   indicator=True)
    both = m[m["_merge"] == "both"]
    cells_off, max_abs = 0, 0.0
    for c in num_cols:
        a, b = both[f"{c}_ours"].astype(float), both[f"{c}_key"].astype(float)
        one_missing = a.isna() ^ b.isna()
        diff = (a - b).abs()
        cells_off += int(one_missing.sum()) + int((diff > tol).sum())
        if diff.notna().any():
            max_abs = max(max_abs, float(diff.max()))
    out = {
        "n_common": int(len(both)),
        "only_ours": int((m["_merge"] == "left_only").sum()),
        "only_key": int((m["_merge"] == "right_only").sum()),
        "cells_off": int(cells_off),
        "max_abs_diff": max_abs,
    }
    out["ok"] = out["only_key"] == 0 and out["cells_off"] == 0
    return out


# =============================================================================
# Q4. Parity between two export directories (R vs Python)
# =============================================================================
def parity(dir_a, dir_b, tables, tol=1e-9):
    """Compare <dir_a>/<t>.csv with <dir_b>/<t>.csv for each table, row by row.

    Both files must have the same columns and the same number of rows (the
    exports are already sorted the same way). A cell counts as numeric when
    both sides parse as floats; numeric cells may differ by at most tol, other
    cells must be equal as text (empty equals empty).
    Returns {table: {"ok", "n", "max_abs_diff", "text_off"}}.
    """
    out = {}
    for t in tables:
        a = pd.read_csv(Path(dir_a) / f"{t}.csv", dtype=str, keep_default_na=False)
        b = pd.read_csv(Path(dir_b) / f"{t}.csv", dtype=str, keep_default_na=False)
        same_shape = list(a.columns) == list(b.columns) and len(a) == len(b)
        max_abs, text_off = 0.0, 0
        if same_shape:
            for c in a.columns:
                for u, v in zip(a[c], b[c]):
                    try:
                        max_abs = max(max_abs, abs(float(u) - float(v)))
                    except ValueError:
                        text_off += u != v
        ok = same_shape and max_abs <= tol and text_off == 0 and not math.isnan(max_abs)
        out[t] = {"ok": bool(ok), "n": int(len(a)), "max_abs_diff": max_abs,
                  "text_off": int(text_off)}
    return out


# =============================================================================
# Part 2: an R pipeline and its Python twin
#     Drills 5 to 8 follow the step-2 files of the same repo: ingest_excel.py,
#     excel_cells.py, compute_data_sec_agg.py (before its SQL version) and the
#     parity test (tests/testthat/helper-py-parity.R).
# =============================================================================

# =============================================================================
# Q5. Read a sheet by position, like R's read_sheet()
# =============================================================================
EXCEL_EPOCH = datetime.datetime(1899, 12, 30)


def excel_col_letters(n):
    """The first n Excel column names: A, B, ..., Z, AA, AB, ..."""
    out = []
    for i in range(1, n + 1):
        x, s = i, ""
        while x > 0:
            r = (x - 1) % 26
            s = chr(65 + r) + s
            x = (x - 1) // 26
        out.append(s)
    return out


def read_sheet(path, sheet):
    """The whole sheet as a positional DataFrame.

    Columns are named by Excel letter and the index is the sheet row number,
    so df.at[16, "G"] is cell G16 (R: df$G[16]). Values stay raw: str, int,
    float, bool or None, except that a date becomes its Excel serial number
    (2018-12-31 is 43465.0), as readxl reports a date in a text column.
    Trailing rows and columns that are entirely empty are dropped, as readxl
    drops them. Read cached values (data_only=True), never formulas.
    """
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        rows = []
        for row in wb[sheet].iter_rows(values_only=True):
            rows.append([(v - EXCEL_EPOCH).total_seconds() / 86400
                         if isinstance(v, datetime.datetime) else v for v in row])
    finally:
        wb.close()
    while rows and all(v is None for v in rows[-1]):
        rows.pop()
    width = 0
    for r in rows:
        filled = [j for j, v in enumerate(r) if v is not None]
        if filled:
            width = max(width, filled[-1] + 1)
    data = [list(r[:width]) + [None] * (width - len(r[:width])) for r in rows]
    df = pd.DataFrame(data, columns=excel_col_letters(width), dtype=object)
    df.index = range(1, len(df) + 1)
    return df


# =============================================================================
# Q6. One cell as a number, like R's suppressWarnings(as.numeric(df$G[16]))
# =============================================================================
_ADDR = re.compile(r"^([A-Z]+)([0-9]+)$")


def to_num(v):
    """R's suppressWarnings(as.numeric(v)) for one workbook value: a number,
    or NaN for anything that is not one (None, a bool, a label, "n/a")."""
    if v is None or isinstance(v, bool):
        return math.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if "_" in s:          # float() reads "1_000"; as.numeric() does not
        return math.nan
    try:
        return float(s)
    except ValueError:
        return math.nan


def xls_cell(df, addr):
    """The cell at an address such as "G16" as a float (NaN if missing or not
    a number, or if the address is outside the sheet)."""
    m = _ADDR.match(addr)
    if not m:
        raise ValueError(f"Not a cell address: {addr}")
    col, row = m.group(1), int(m.group(2))
    if col not in df.columns or row not in df.index:
        return math.nan
    return to_num(df.at[row, col])


# =============================================================================
# Q7. A dplyr pipeline, twinned in pandas
# =============================================================================
def compute_data_sec_agg(data_sec_all, exclude_ids, cols):
    """The Python twin of this R function (the version before the SQL file):

        data_sec_all |>
          filter(!forbes_id %in% exclude_ids) |>
          filter(!duplicated(pick(year, forbes_id, forbes_worth))) |>
          group_by(year) |>
          summarise(n = n(), across(all_of(cols), \\(x) sum(x, na.rm = TRUE) / 1000))

    Returns a DataFrame with columns year, n, then cols, one row per year in
    increasing order; year and n are ints.
    """
    d = data_sec_all[~data_sec_all["forbes_id"].isin(list(exclude_ids))]
    # duplicated() in pandas, like R's, keeps the first and treats NaN == NaN.
    d = d[~d.duplicated(subset=["year", "forbes_id", "forbes_worth"], keep="first")]
    g = d.groupby("year", sort=True)
    out = g[list(cols)].sum() / 1000          # skips NaN; an all-NaN group sums to 0
    out.insert(0, "n", g.size())              # n(): rows, not non-missing values
    out = out.reset_index()
    out["year"] = out["year"].astype(int)
    out["n"] = out["n"].astype(int)
    return out


# =============================================================================
# Q8. Parity between an R export folder and a Python one, relative tolerance
# =============================================================================
def _num(s):
    """A CSV field as a float, None when missing ("" or "NA"); ValueError if text."""
    if s in ("", "NA"):
        return None
    return float(s)


def parity_rel(dir_r, dir_py, tol=1e-9):
    """Compare every CSV in dir_r with the file of the same name in dir_py.

    Returns {file name: {"ok", "n_values", "max_rel_diff"}} for every file in
    either folder. A file on one side only, or a pair whose column names or
    row counts differ: ok False, n_values 0, max_rel_diff None. Otherwise, per
    column: if every cell on both sides is a number or missing ("" or "NA"),
    the missing cells must sit in the same rows, and each pair of numbers is
    compared as |py - r| / max(1, |r|); n_values counts those pairs and
    max_rel_diff is the largest. Any other column must match exactly as text.
    ok means: no text or missing-value difference and max_rel_diff <= tol.
    """
    dir_r, dir_py = Path(dir_r), Path(dir_py)
    names = sorted({p.name for p in dir_r.glob("*.csv")} | {p.name for p in dir_py.glob("*.csv")})
    out = {}
    for name in names:
        res = {"ok": False, "n_values": 0, "max_rel_diff": None}
        out[name] = res
        if not ((dir_r / name).exists() and (dir_py / name).exists()):
            continue
        a = pd.read_csv(dir_r / name, dtype=str, keep_default_na=False)
        b = pd.read_csv(dir_py / name, dtype=str, keep_default_na=False)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            continue
        ok, n, max_rel = True, 0, 0.0
        for c in a.columns:
            try:
                x = [_num(v) for v in a[c]]
                y = [_num(v) for v in b[c]]
            except ValueError:
                ok = ok and list(a[c]) == list(b[c])
                continue
            for u, v in zip(x, y):
                if (u is None) != (v is None):
                    ok = False
                elif u is not None:
                    max_rel = max(max_rel, abs(v - u) / max(1.0, abs(u)))
                    n += 1
        res.update(ok=bool(ok and max_rel <= tol), n_values=n, max_rel_diff=max_rel)
    return out
