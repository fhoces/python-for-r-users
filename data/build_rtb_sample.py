"""
Build the synthetic billionaire panel and the reference results for module 7.

Module 7 is about the Python around one real SQL step: 01_rtb_ca.sql in
github.com/fhoces/opa-prop40 (bsz-analysis/), which turns daily Forbes
real-time billionaire snapshots into the California lists of a published
paper. The real snapshots are confidential, so this script invents a panel in
the same shape. Every person, id and number here is made up.

This is a Python port of sql-industry-prep/data/build_rtb_sample.R (same seed,
same schema, same hand-placed cases and the same invented ids for them). The
courses do not share files, and numpy's random numbers differ from R's, so
the remaining people and every worth differ from the SQL course's panel.

Writes, from the repo root:
  data/rtb_sample.csv                 rtb_all_combined: one row per (date,
                                      forbes_id), worth in $ million; missing
                                      values are EMPTY fields, and some source
                                      values carry a trailing space, as in the
                                      real bundle's CSVs
  data/rtb_ca_cik.csv                 forbes_id, cik
  data/rtb_residency_overrides.csv    forbes_id, rule, note
  data/expected/                      what module-07/check.py compares with:
    load_profile.csv                    per column: type, NULL count, distinct
                                        values, sum (drill 1)
    exports/<table>.csv                 the three deterministic exports (drill 2)
    answer_key_aggregate.csv            a pretend "authors' sheet" for drill 3
    compare_result.json                 what compare() should return on it
    parity_r/, parity_bad/              two more export folders for drill 4
    parity_results.json                 what parity() should return on them

The reference results come from module-07/solution.py.

Run from the repo root with: python data/build_rtb_sample.py
"""
import csv
import json
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXPECTED = DATA / "expected"
sys.path.insert(0, str(ROOT / "module-07"))
import solution  # noqa: E402

rng = np.random.default_rng(2026)

# --- dates: every 8th day, plus the snapshot dates, no 2025-12-31 ---------------
EOY = ["2019-12-31", "2020-12-31", "2021-12-31", "2022-12-31", "2023-12-31",
       "2024-12-31", "2026-01-01"]
SKIP = ["2022-07-18", "2026-03-29", "2026-03-30"]
d0, d1 = date(2019, 12, 31), date(2026, 3, 30)
dates = {(d0 + timedelta(days=k)).isoformat() for k in range(0, (d1 - d0).days + 1, 8)}
dates |= set(EOY) | set(SKIP) | {"2025-12-30"}
dates.discard("2025-12-31")
dates = sorted(dates)
n_dates = len(dates)

# --- people: 60 invented billionaires -------------------------------------------
first = ["Avery", "Bram", "Calla", "Dorian", "Ember", "Faro", "Gideon", "Halle",
         "Ines", "Jory", "Kestrel", "Lumen", "Marlo", "Nell", "Orrin", "Pia",
         "Quill", "Rhea", "Soren", "Tamsin", "Ulla", "Vance", "Wren", "Xavi",
         "Yara", "Zeno", "Adair", "Bexley", "Cyrus", "Delphine"]
last = ["Ashgrove", "Brightwater", "Coldharbor", "Dunmore", "Elderfield",
        "Fairweather", "Glenrock", "Hollowell", "Ironwood", "Juniper",
        "Kettleby", "Larkspur", "Merriweather", "Northcott", "Oakhurst",
        "Pennyroyal", "Quarrington", "Ravensworth", "Silverbrook", "Thistlewood",
        "Underhill", "Vantongeren", "Whitlock", "Yarrowby", "Zanderfell",
        "Amberly", "Blackthorn", "Copperfield", "Driftwood", "Emberton"]
# The hand-placed people keep the SQL course's invented names, so the query's
# top-4 ids and the override table are the same in both courses.
fixed = ["Marlo Zanderfell", "Calla Vantongeren", "Xavi Juniper", "Quill Silverbrook",
         "Wren Underhill", "Soren Driftwood", "Rhea Dunmore"]
pool = [f"{a} {b}" for a in first for b in last if f"{a} {b}" not in fixed]
names = fixed + list(rng.choice(pool, size=60 - len(fixed), replace=False))
n_people = len(names)

industry_sources = [
    ("Technology", "software"), ("Technology", "semiconductors"),
    ("Technology", "online marketplace"), ("Finance & Investments", "hedge funds"),
    ("Finance & Investments", "private equity"), ("Media & Entertainment", "streaming"),
    ("Real Estate", "real estate"), ("Healthcare", "medical devices"),
    ("Food & Beverage", "coffee chains"), ("Fashion & Retail", "athletic apparel"),
    ("Diversified", "investments"),
]
w = np.array([4, 3, 2, 3, 2, 2, 2, 2, 1, 1, 1], dtype=float)
ind = rng.choice(len(industry_sources), size=n_people, p=w / w.sum())
states = rng.choice(["California", "New York", "Texas", "Washington", "Florida",
                     "Nevada", "Massachusetts"], size=n_people,
                    p=[0.50, 0.12, 0.10, 0.08, 0.08, 0.06, 0.06])
people = pd.DataFrame({
    "forbes_name": names,
    "forbes_id": [n.lower().replace(" ", "-") for n in names],
    "state": states.astype(object),
    "country_citizenship": "United States",
    "industries": [industry_sources[i][0] for i in ind],
    "source": [industry_sources[i][1] for i in ind],
})
# Hand-placed cases (rows are 0-based here):
# 0-3 the top 4; 4 California by override (state Nevada); 5 California by
# override (no state); 6 state California but excluded; 7-8 no state, no
# override; 9-10 not US citizens; 11 the Sports owner, never a public split.
people.loc[0:3, "state"] = "California"
people.loc[0:3, "industries"] = "Technology"
people.loc[0:3, "source"] = ["software", "semiconductors", "online marketplace", "software"]
people.loc[4, "state"] = "Nevada"
people.loc[5, "state"] = None
people.loc[6, "state"] = "California"
people.loc[7:8, "state"] = None
people.loc[9:10, "state"] = None
people.loc[9:10, "country_citizenship"] = ["Canada", "Brazil"]
people.loc[11, ["state", "industries", "source"]] = ["California", "Sports", "sports team"]

w0 = np.exp(rng.uniform(np.log(600), np.log(40000), n_people))
w0[0:4] = [160000, 120000, 95000, 90000]
w0[[4, 5, 6, 11]] = [4000, 2500, 6000, 1800]
public_share = np.round(rng.uniform(0, 0.95, n_people), 3)
first_day = np.zeros(n_people, dtype=int)
last_day = np.full(n_people, n_dates - 1)
late = rng.choice(np.arange(12, n_people), size=10, replace=False)
first_day[late] = rng.integers(29, 250, size=10)
gone = rng.choice(np.setdiff1d(np.arange(12, n_people), late), size=2, replace=False)
last_day[gone] = rng.integers(149, 280, size=2)

# --- the panel: a random walk in log worth per person ---------------------------
rows = []
for i, p in people.iterrows():
    days = np.arange(first_day[i], last_day[i] + 1)
    steps = rng.normal(0.003, 0.04, size=len(days))
    worth = np.round(w0[i] * np.exp(np.cumsum(steps) - steps[0]), 1)
    for d, wv in zip(days, worth):
        pub = round(wv * public_share[i], 1)
        rows.append([dates[d], p.forbes_id, p.forbes_name, p.state, p.country_citizenship,
                     p.source, p.industries, wv, pub, round(wv - pub, 1)])
cols = ["date", "forbes_id", "forbes_name", "state", "country_citizenship", "source",
        "industries", "forbes_worth", "forbes_public_worth", "forbes_private_worth"]
panel = pd.DataFrame(rows, columns=cols).astype(object)
sports = panel["forbes_id"] == people.loc[11, "forbes_id"]
no_split = rng.uniform(size=len(panel)) < 0.03
panel.loc[sports | no_split, ["forbes_public_worth", "forbes_private_worth"]] = None
panel.loc[rng.uniform(size=len(panel)) < 0.005, "forbes_worth"] = None
panel = panel.sort_values(["date", "forbes_id"]).reset_index(drop=True)
# The real CSVs carry a trailing space on many source values; so does this one.
trail = rng.uniform(size=len(panel)) < 0.2
panel.loc[trail, "source"] = panel.loc[trail, "source"] + " "

overrides = pd.DataFrame({
    "forbes_id": people.loc[[4, 5, 6], "forbes_id"].to_list(),
    "rule": ["include", "include", "exclude"],
    "note": ["course example: state on file is Nevada, counted as California",
             "course example: no state on file, counted as California",
             "course example: state on file is California, never counted"],
})
ca_ids = people.loc[(people["state"] == "California")
                    | people["forbes_id"].isin(overrides.loc[overrides.rule == "include",
                                                             "forbes_id"]), "forbes_id"]
cik = pd.DataFrame({"forbes_id": ca_ids.to_list(),
                    "cik": rng.choice(np.arange(1000000, 2000000), size=len(ca_ids),
                                      replace=False).astype(object)})
cik.loc[rng.uniform(size=len(cik)) < 0.25, "cik"] = None


def write(df, path):
    # None -> empty field, as the real bundle writes missing values.
    df.to_csv(path, index=False, na_rep="", lineterminator="\n")


write(panel, DATA / "rtb_sample.csv")
write(cik, DATA / "rtb_ca_cik.csv")
write(overrides, DATA / "rtb_residency_overrides.csv")
print(f"data/rtb_sample.csv: {len(panel):,} rows ({n_people} people x {n_dates} dates); "
      f"rtb_ca_cik {len(cik)}, overrides {len(overrides)}")

# --- reference results -------------------------------------------------------------
RTB_COLUMNS = [("date", "TEXT"), ("forbes_id", "TEXT"), ("forbes_name", "TEXT"),
               ("state", "TEXT"), ("country_citizenship", "TEXT"), ("source", "TEXT"),
               ("industries", "TEXT"), ("forbes_worth", "REAL"),
               ("forbes_public_worth", "REAL"), ("forbes_private_worth", "REAL")]
EXPORT_ORDER = {
    "rtb_ca_eoy": "date, forbes_worth DESC, forbes_id",
    "rtb_ca_2026_01_01_industry": "(industries = 'Total'), fraction_forbes_worth DESC, industries",
    "rtb_ca_aggregate": "date",
}
if EXPECTED.exists():
    shutil.rmtree(EXPECTED)
EXPECTED.mkdir(parents=True)

with tempfile.TemporaryDirectory() as tmp:
    con = sqlite3.connect(Path(tmp) / "rtb.sqlite")
    n = solution.load_csv(con, DATA / "rtb_sample.csv", "rtb_all_combined", RTB_COLUMNS,
                          index_on=("date", "forbes_id"))
    solution.load_csv(con, DATA / "rtb_ca_cik.csv", "rtb_ca_cik",
                      [("forbes_id", "TEXT"), ("cik", "INTEGER")])
    solution.load_csv(con, DATA / "rtb_residency_overrides.csv", "rtb_residency_overrides",
                      [("forbes_id", "TEXT"), ("rule", "TEXT"), ("note", "TEXT")])

    # Drill 1: a profile of the loaded table.
    prof = []
    for name, typ in RTB_COLUMNS:
        n_null, n_distinct = con.execute(
            f"SELECT SUM({name} IS NULL), COUNT(DISTINCT {name}) FROM rtb_all_combined").fetchone()
        total = con.execute(f"SELECT SUM({name}) FROM rtb_all_combined").fetchone()[0] \
            if typ == "REAL" else ""
        prof.append({"column": name, "type": typ, "n_rows": n, "n_null": n_null,
                     "n_distinct": n_distinct, "sum": total})
    pd.DataFrame(prof).to_csv(EXPECTED / "load_profile.csv", index=False, lineterminator="\n")

    # Drill 2: the three exports.
    counts = solution.run_and_export(con, ROOT / "module-07" / "01_rtb_ca.sql",
                                     list(EXPORT_ORDER), EXPECTED / "exports", EXPORT_ORDER)
    con.close()
for t, k in counts.items():
    print(f"  data/expected/exports/{t}.csv: {k} rows")

# Drill 3: a pretend authors' sheet for the daily aggregate, with a vintage gap
# (it stops 5 dates earlier), one cell off by 1e-9 (noise, within tolerance) and
# one cell off by 0.25 (a real difference).
agg = pd.read_csv(EXPECTED / "exports" / "rtb_ca_aggregate.csv")
key = agg.iloc[:-5].copy()
key = key.drop(columns=["forbes_private_worth"])  # the sheet does not have it
key.loc[10, "forbes_worth_total"] += 1e-9
key.loc[40, "forbes_worth_top4"] += 0.25
key.to_csv(EXPECTED / "answer_key_aggregate.csv", index=False, float_format="%.17g",
           lineterminator="\n")
res = solution.compare(agg, key, ["date"], ["n_billionaires", "forbes_worth_total",
                                            "forbes_worth_top4"])
(EXPECTED / "compare_result.json").write_text(json.dumps(res, indent=1) + "\n")
print("  compare_result:", res)


# Drill 4: an "R" export folder (same doubles, written with 17 significant
# digits, as R's writer sometimes does) and a "bad" one (one value moved by
# 1e-6, beyond the 1e-9 parity tolerance).
def rewrite(src, dst, change=None):
    dst.mkdir(parents=True, exist_ok=True)
    for t in EXPORT_ORDER:
        with open(src / f"{t}.csv", newline="") as f:
            rows = list(csv.reader(f))
        for r in rows[1:]:
            for j, v in enumerate(r):
                try:
                    x = float(v)
                except ValueError:
                    continue
                if "." in v or "e" in v:
                    r[j] = "%.17g" % x
        if change and t == change[0]:
            r = rows[change[1]]
            r[change[2]] = repr(float(r[change[2]]) + 1e-6)
        with open(dst / f"{t}.csv", "w", newline="") as f:
            csv.writer(f, lineterminator="\n").writerows(rows)


rewrite(EXPECTED / "exports", EXPECTED / "parity_r")
rewrite(EXPECTED / "exports", EXPECTED / "parity_bad", change=("rtb_ca_aggregate", 5, 2))
par = {
    "parity_r": solution.parity(EXPECTED / "exports", EXPECTED / "parity_r", list(EXPORT_ORDER)),
    "parity_bad": solution.parity(EXPECTED / "exports", EXPECTED / "parity_bad", list(EXPORT_ORDER)),
}
(EXPECTED / "parity_results.json").write_text(json.dumps(par, indent=1) + "\n")
print("  parity_results:", {k: {t: v["ok"] for t, v in d.items()} for k, d in par.items()})
