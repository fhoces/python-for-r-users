"""
Module 7: grade the eight drill functions (part 1: Q1 to Q4; part 2: Q5 to Q8).

Usage, from the repo root (after `python data/build_rtb_sample.py`):

    python module-07/check.py                        # grades module-07/exercise.py
    python module-07/check.py my_answers.py          # any file with the four functions
    python module-07/check.py module-07/solution.py  # must pass every drill

Imports the file, runs each drill function on the synthetic data in a
temporary folder, and compares the result with data/expected/. Prints one line
per drill: PASS, or the first difference. Exit code 1 if any drill fails.

The drills are graded independently: drill 2 runs on a database this script
builds itself, so a broken loader in drill 1 does not fail drill 2, and drills
6 and 7 read the workbook with the grader's own reader, not your drill 5.
Part 2 needs openpyxl (pandas' Excel reader uses it too).
"""
import csv
import importlib.util
import json
import math
import sqlite3
import sys
import tempfile
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXPECTED = DATA / "expected"
SQL_FILE = ROOT / "module-07" / "01_rtb_ca.sql"

RTB_COLUMNS = [("date", "TEXT"), ("forbes_id", "TEXT"), ("forbes_name", "TEXT"),
               ("state", "TEXT"), ("country_citizenship", "TEXT"), ("source", "TEXT"),
               ("industries", "TEXT"), ("forbes_worth", "REAL"),
               ("forbes_public_worth", "REAL"), ("forbes_private_worth", "REAL")]
EXPORT_ORDER = {
    "rtb_ca_eoy": "date, forbes_worth DESC, forbes_id",
    "rtb_ca_2026_01_01_industry": "(industries = 'Total'), fraction_forbes_worth DESC, industries",
    "rtb_ca_aggregate": "date",
}
TABLES = list(EXPORT_ORDER)


def _import(path):
    spec = importlib.util.spec_from_file_location("answers", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _reference_db(path):
    """The three input tables, loaded with the csv module (independent of drill 1)."""
    con = sqlite3.connect(path)

    def load(csv_path, table, columns):
        con.execute(f"CREATE TABLE {table} (" + ", ".join(f"{n} {t}" for n, t in columns) + ")")
        with open(csv_path, newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r)
            rows = []
            for row in r:
                out = []
                for (_, t), v in zip(columns, row):
                    v = v.strip(" \t")
                    out.append(None if v == "" else float(v) if t == "REAL"
                               else int(v) if t == "INTEGER" else v)
                rows.append(out)
        con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(columns))})", rows)

    load(DATA / "rtb_sample.csv", "rtb_all_combined", RTB_COLUMNS)
    load(DATA / "rtb_ca_cik.csv", "rtb_ca_cik", [("forbes_id", "TEXT"), ("cik", "INTEGER")])
    load(DATA / "rtb_residency_overrides.csv", "rtb_residency_overrides",
         [("forbes_id", "TEXT"), ("rule", "TEXT"), ("note", "TEXT")])
    con.commit()
    return con


# ---------------------------------------------------------------------------
# one function per drill; each returns None (pass) or a message
# ---------------------------------------------------------------------------
def drill1(mod, tmp):
    con = sqlite3.connect(Path(tmp) / "d1.sqlite")
    n = mod.load_csv(con, DATA / "rtb_sample.csv", "rtb_all_combined", RTB_COLUMNS,
                     index_on=("date", "forbes_id"))
    prof = pd.read_csv(EXPECTED / "load_profile.csv", keep_default_na=False)
    n_exp = int(prof["n_rows"].iloc[0])
    if n != n_exp:
        return f"returned {n!r}, expected {n_exp} rows"
    (n_tab,) = con.execute("SELECT COUNT(*) FROM rtb_all_combined").fetchone()
    if n_tab != n_exp:
        return f"table has {n_tab} rows, expected {n_exp}"
    types = {r[1]: r[2].upper() for r in con.execute("PRAGMA table_info(rtb_all_combined)")}
    for _, r in prof.iterrows():
        c = r["column"]
        if types.get(c) != r["type"]:
            return f"column {c} has type {types.get(c)!r}, expected {r['type']}"
        n_null, n_distinct = con.execute(
            f"SELECT SUM({c} IS NULL), COUNT(DISTINCT {c}) FROM rtb_all_combined").fetchone()
        if n_null != int(r["n_null"]):
            return f"column {c}: {n_null} NULLs, expected {r['n_null']} (empty fields must become NULL)"
        if n_distinct != int(r["n_distinct"]):
            return (f"column {c}: {n_distinct} distinct values, expected {r['n_distinct']} "
                    "(are leading and trailing spaces trimmed?)")
        if r["type"] == "REAL":
            (n_text,) = con.execute(
                f"SELECT COUNT(*) FROM rtb_all_combined WHERE typeof({c}) = 'text'").fetchone()
            if n_text:
                return f"column {c}: {n_text} values stored as text, expected numbers"
            (s,) = con.execute(f"SELECT SUM({c}) FROM rtb_all_combined").fetchone()
            if abs(s - float(r["sum"])) > 1e-3:
                return f"column {c}: sum {s!r}, expected {r['sum']}"
    idx_cols = set()
    for row in con.execute("PRAGMA index_list(rtb_all_combined)"):
        idx_cols |= {r[2] for r in con.execute(f"PRAGMA index_info({row[1]})")}
    if not {"date", "forbes_id"} <= idx_cols:
        return f"indexes cover {sorted(idx_cols)}, expected date and forbes_id"
    return None


def drill2(mod, tmp):
    con = _reference_db(Path(tmp) / "d2.sqlite")
    out = Path(tmp) / "exports"
    counts = mod.run_and_export(con, SQL_FILE, TABLES, out, EXPORT_ORDER)
    for t in TABLES:
        exp = (EXPECTED / "exports" / f"{t}.csv").read_bytes()
        path = out / f"{t}.csv"
        if not path.exists():
            return f"{t}.csv was not written"
        got = path.read_bytes()
        if got != exp:
            gl, el = got.decode().split("\n"), exp.decode().split("\n")
            for i, (a, b) in enumerate(zip(gl, el), 1):
                if a != b:
                    j = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                    lo = max(0, j - 25)
                    return (f"{t}.csv line {i}, from character {j + 1}: yours {a[lo:j + 30]!r}, "
                            f"expected {b[lo:j + 30]!r}")
            return f"{t}.csv has {len(gl)} lines, expected {len(el)}"
        n_exp = exp.decode().count("\n") - 1
        if not isinstance(counts, dict) or counts.get(t) != n_exp:
            return f"returned {counts!r}, expected {t}: {n_exp}"
    # The sort must come from order_by, not from the order rows happen to be
    # stored in: export the daily table again, newest date first.
    out2 = Path(tmp) / "exports_desc"
    mod.run_and_export(con, SQL_FILE, ["rtb_ca_aggregate"], out2,
                       {"rtb_ca_aggregate": "date DESC"})
    lines = (EXPECTED / "exports" / "rtb_ca_aggregate.csv").read_text().splitlines()
    want = "\n".join([lines[0]] + lines[:0:-1]) + "\n"
    if (out2 / "rtb_ca_aggregate.csv").read_text() != want:
        return "with order_by 'date DESC' the daily table is not newest-first: use order_by[table]"
    return None


def drill3(mod, tmp):
    agg = pd.read_csv(EXPECTED / "exports" / "rtb_ca_aggregate.csv")
    key = pd.read_csv(EXPECTED / "answer_key_aggregate.csv")
    num = ["n_billionaires", "forbes_worth_total", "forbes_worth_top4"]
    exp = json.loads((EXPECTED / "compare_result.json").read_text())
    same = mod.compare(agg, agg.copy(), ["date"], num)
    if not (same.get("ok") is True and same.get("cells_off") == 0 and same.get("only_ours") == 0
            and same.get("only_key") == 0 and same.get("max_abs_diff") == 0):
        return f"a table compared with itself should be ok with zero differences, got {same!r}"
    got = mod.compare(agg, key, ["date"], num)
    for k, v in exp.items():
        g = got.get(k)
        if k == "max_abs_diff":
            if g is None or abs(g - v) > 1e-9:
                return f"max_abs_diff {g!r}, expected {v}"
        elif g != v:
            return f"{k} {g!r}, expected {v!r} (full result {got!r})"
    return None


def drill4(mod, tmp):
    exp = json.loads((EXPECTED / "parity_results.json").read_text())
    for other, results in exp.items():
        got = mod.parity(EXPECTED / "exports", EXPECTED / other, TABLES)
        for t, e in results.items():
            g = got.get(t, {})
            for k, v in e.items():
                gv = g.get(k)
                if k == "max_abs_diff":
                    if gv is None or math.isnan(gv) or abs(gv - v) > 1e-12:
                        return f"{other}/{t}: max_abs_diff {gv!r}, expected {v!r}"
                elif gv != v:
                    return f"{other}/{t}: {k} {gv!r}, expected {v!r}"
    return None


# ---------------------------------------------------------------------------
# Part 2: drills 5 to 8 (an R pipeline and its Python twin)
# ---------------------------------------------------------------------------
WORKBOOK = DATA / "workbook_sample.xlsx"


def _same(a, b):
    """Equal values, numbers within 1e-12 (an int and a float can match)."""
    if a is None or b is None or isinstance(a, bool) or isinstance(b, bool):
        if isinstance(a, float) and math.isnan(a):
            a = None
        return a is b or a == b and type(a) is type(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-12
    return a == b


def _grader_sheet(sheet):
    """The grader's own positional read of a sheet (independent of drill 5)."""
    import openpyxl
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True, read_only=True)
    rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    wb.close()
    epoch = __import__("datetime").datetime(1899, 12, 30)
    rows = [[(v - epoch).total_seconds() / 86400 if hasattr(v, "year") else v for v in r]
            for r in rows]
    while rows and all(v is None for v in rows[-1]):
        rows.pop()
    width = max(max((j + 1 for j, v in enumerate(r) if v is not None), default=0) for r in rows)

    def letters(n):
        x, out = n, ""
        while x > 0:
            x, r = divmod(x - 1, 26)
            out = chr(65 + r) + out
        return out
    df = pd.DataFrame([r[:width] + [None] * (width - len(r[:width])) for r in rows],
                      columns=[letters(j) for j in range(1, width + 1)], dtype=object)
    df.index = range(1, len(df) + 1)
    return df


def drill5(mod, tmp):
    exp = json.loads((EXPECTED / "read_sheet.json").read_text())
    for sheet, e in exp.items():
        df = mod.read_sheet(WORKBOOK, sheet)
        if not isinstance(df, pd.DataFrame):
            return f"{sheet}: returned {type(df).__name__}, expected a DataFrame"
        if list(df.shape) != e["shape"]:
            return (f"{sheet}: shape {df.shape}, expected {tuple(e['shape'])} "
                    "(are trailing empty rows dropped? is every column kept?)")
        if list(df.columns[:3]) != ["A", "B", "C"] or df.columns[-1] != e["columns_last"]:
            return f"{sheet}: columns {list(df.columns[:3])} ... {df.columns[-1]!r}, expected A, B, C ... {e['columns_last']!r}"
        if df.index[0] != 1:
            return f"{sheet}: the index starts at {df.index[0]!r}; it should be the sheet row, from 1"
        for addr, want in e["cells"].items():
            col, row = addr.rstrip("0123456789"), int(addr.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            got = df.at[row, col]
            if isinstance(got, float) and math.isnan(got) and want is None:
                continue
            if not _same(got, want):
                return f"{sheet}!{addr}: {got!r}, expected {want!r}"
    return None


def drill6(mod, tmp):
    df = _grader_sheet("summary")
    for addr, want in json.loads((EXPECTED / "xls_cells.json").read_text()):
        got = mod.xls_cell(df, addr)
        if want is None:
            if not (isinstance(got, float) and math.isnan(got)):
                return f"xls_cell(df, {addr!r}) is {got!r}, expected NaN (not a number, as R's as.numeric() sees it)"
        elif not isinstance(got, float) or abs(got - want) > 1e-12:
            return f"xls_cell(df, {addr!r}) is {got!r}, expected {want!r} (a float)"
    return None


def drill7(mod, tmp):
    spec = json.loads((EXPECTED / "data_sec_agg_inputs.json").read_text())
    dsa = pd.read_excel(WORKBOOK, sheet_name="data_sec_all", skiprows=3)
    exp = pd.read_csv(EXPECTED / "data_sec_agg.csv")
    got = mod.compute_data_sec_agg(dsa.copy(), spec["exclude_ids"], spec["cols"])
    want_cols = ["year", "n"] + spec["cols"]
    if list(got.columns) != want_cols:
        return f"columns {list(got.columns)[:4]}..., expected {want_cols[:4]}... ({len(want_cols)} in all)"
    if len(got) != len(exp):
        return f"{len(got)} rows, expected {len(exp)} (one per year)"
    got = got.reset_index(drop=True)
    if list(got["year"]) != list(exp["year"]):
        return f"years {list(got['year'])}, expected {list(exp['year'])}"
    for i in range(len(exp)):
        if int(got.at[i, "n"]) != int(exp.at[i, "n"]):
            return (f"year {exp.at[i, 'year']}: n {got.at[i, 'n']!r}, expected {exp.at[i, 'n']} "
                    "(count rows, not non-missing values; drop each re-paste once)")
    for c in spec["cols"]:
        a = got[c].to_numpy(dtype=float)
        b = exp[c].to_numpy(dtype=float)
        bad = ~(abs(a - b) <= 1e-9 * pd.Series(abs(b)).clip(lower=1).to_numpy())
        if bad.any():
            i = int(bad.argmax())
            return f"year {exp.at[i, 'year']}, {c}: {a[i]!r}, expected {b[i]!r}"
    return None


def drill8(mod, tmp):
    exp = json.loads((EXPECTED / "parity_rel_results.json").read_text())
    base = EXPECTED / "parity_rel"
    for other, results in exp.items():
        got = mod.parity_rel(base / "r", base / other)
        if sorted(got) != sorted(results):
            return f"r vs {other}: files {sorted(got)}, expected {sorted(results)}"
        for name, e in results.items():
            g = got[name]
            if g.get("ok") is not e["ok"]:
                return f"r vs {other}, {name}: ok {g.get('ok')!r}, expected {e['ok']} (full result {g!r})"
            if g.get("n_values") != e["n_values"]:
                return f"r vs {other}, {name}: n_values {g.get('n_values')!r}, expected {e['n_values']}"
            gm, em = g.get("max_rel_diff"), e["max_rel_diff"]
            if (gm is None) != (em is None) or (em is not None and abs(gm - em) > 1e-6 * em + 1e-20):
                return f"r vs {other}, {name}: max_rel_diff {gm!r}, expected {em!r}"
    return None


DRILLS = [("Q1", "load_csv", drill1), ("Q2", "run_and_export", drill2),
          ("Q3", "compare", drill3), ("Q4", "parity", drill4),
          ("Q5", "read_sheet", drill5), ("Q6", "xls_cell", drill6),
          ("Q7", "compute_data_sec_agg", drill7), ("Q8", "parity_rel", drill8)]


def main(argv):
    path = Path(argv[0]) if argv else ROOT / "module-07" / "exercise.py"
    if not (EXPECTED / "load_profile.csv").exists():
        sys.exit("data/expected/ is missing: run python data/build_rtb_sample.py first")
    mod = _import(path)
    failures = 0
    for label, name, fn in DRILLS:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                if not hasattr(mod, name):
                    msg = f"no function named {name}"
                else:
                    msg = fn(mod, tmp)
            except NotImplementedError:
                msg = "not implemented yet"
            except Exception as e:  # report the learner's error, keep grading
                tb = traceback.extract_tb(e.__traceback__)[-1]
                msg = f"{type(e).__name__}: {e} (line {tb.lineno} of {Path(tb.filename).name})"
        if msg is None:
            print(f"{label}  PASS  {name}")
        else:
            failures += 1
            print(f"{label}  FAIL  {name}: {msg}")
    print(f"{len(DRILLS) - failures} of {len(DRILLS)} drills pass.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
