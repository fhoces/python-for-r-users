# Quiz questions: Loading, Running SQL and Checking a Reproduction

Generated from `quiz.json` by `tools/quiz/make_clips.py`; do not edit by hand. Each concept has three levels: Warm-up (1), Core (2) and Deep (3). Questions marked (code) show a code block on the quiz page; the audio says "Look at the code on the screen" instead of reading it. The answer key is at the bottom.

## 1. Chunked reading
**Warm-up.** (code) Look at the code on the screen. What does the chunksize argument change about what read csv returns?

```python
for chunk in pd.read_csv(path, dtype=str,
                         keep_default_na=False,
                         chunksize=5000):
    rows = convert(chunk)
    con.executemany(insert, rows)
```

- A) One data frame, but the file is read five thousand bytes at a time
- B) An iterator of data frames, five thousand rows each, instead of one data frame
- C) Only the first five thousand rows, as a quick preview of the file
- D) The whole file split into five thousand equal parts, after it is read into memory

**Core.** Why does the real loader send rows to SQLite in batches of a hundred thousand, rather than all at once?
- A) SQLite rejects any single insert call with more than a hundred thousand rows
- B) Batches let SQLite build its indexes in parallel while the rows keep arriving
- C) Smaller batches make it easier for SQLite to guess each column's type correctly
- D) Memory then holds one batch at a time, whatever the size of the file

**Deep.** (code) Look at the code on the screen. What would go wrong if you deleted the last two lines?

```python
batch = []
for row in reader:
    batch.append([cast(v) for cast, v
                  in zip(casts, row)])
    if len(batch) >= BATCH:
        con.executemany(insert, batch)
        n += len(batch)
        batch = []
con.executemany(insert, batch)
n += len(batch)
```

- A) The leftover rows after the last full batch would never be inserted
- B) Nothing, because the loop already inserts every batch, including the last one
- C) The count would be right, but the last batch would be inserted twice
- D) The table would be empty, because execute many only commits on the final call

## 2. Empty string, NaN and None
**Warm-up.** The raw file writes a missing worth as an empty field. Which Python value makes SQLite store a real null?
- A) An empty string
- B) The string NULL
- C) None
- D) Zero

**Core.** (code) Look at the code on the screen. Why strip the spaces before testing for an empty field?

```python
v = v.strip(" \t")
row.append(float(v) if v != "" else None)
```

- A) A field of only spaces is missing too, and readr trims spaces the same way
- B) Strip turns an empty string into None, so the test after it is only a safety net
- C) Float refuses any string with spaces around it, so strip is needed for the conversion
- D) SQLite stores trailing spaces as a separate type, which would break the sums

**Deep.** A loader reads with pandas' defaults. Someone's name in the file is the word null. What happens to it?
- A) It is kept as the text null, because only empty fields become missing values
- B) Pandas raises an error, because a text column cannot hold a missing value
- C) It becomes None in pandas, and then the string None in SQLite
- D) Pandas turns it into N a N, so the name arrives in SQLite as a null

## 3. executescript versus execute
**Warm-up.** (code) Look at the code on the screen. The file holds eight statements. What happens?

```python
sql = Path("01_rtb_ca.sql").read_text()
con.execute(sql)
```

- A) Python raises an error, because execute runs exactly one statement
- B) Only the first statement runs, and the other seven are silently ignored
- C) All eight run, because execute splits the text at each semicolon
- D) All eight run, but none of them is saved until you call commit

**Core.** Execute script hits an error in the fifth statement. What state is the database in?
- A) Nothing has changed, because execute script rolls back the whole script
- B) Every statement except the fifth has run, since it skips the one that failed
- C) The first four statements have run, and their changes stay
- D) The database is locked until you call rollback on the connection

**Deep.** (code) Look at the code on the screen. Why is this a bad use of execute script?

```python
fid = input("id to delete: ")
sql = ("DELETE FROM rtb_ca_cik "
       f"WHERE forbes_id = '{fid}';")
con.executescript(sql)
```

- A) Execute script cannot run a delete statement, only create table and drop table statements
- B) No placeholders, so typed input lands inside the SQL and can add statements
- C) The semicolon at the end makes execute script run the delete twice
- D) Input returns bytes, and execute script cannot read bytes as SQL text

## 4. Parameter binding
**Warm-up.** In the loader's insert statement, what do the question marks stand for?
- A) Columns whose type SQLite should guess from the first row it receives
- B) Optional values that a row is allowed to leave out
- C) Wildcards that match any column name in the table
- D) Placeholders that SQLite fills from each row given to execute many

**Core.** (code) Look at the code on the screen. What happens when this runs?

```python
name = "Rhea O'Dunmore"
sql = ("INSERT INTO people VALUES "
       f"('{name}', {worth})")
con.execute(sql)
```

- A) It works, because SQLite escapes apostrophes inside values on its own
- B) It fails, because the apostrophe in the name ends the SQL string early
- C) It inserts the name without the apostrophe, which SQLite quietly drops
- D) It works, but the worth is stored as text, because it came from an f string

**Deep.** Why is execute many with placeholders also faster than formatting one insert per row?
- A) Placeholders skip SQLite's type checks, so each row is written without inspection
- B) Execute many writes the rows in parallel over several connections
- C) SQLite parses the statement once and reuses it for every row
- D) Formatted inserts must each be committed alone, while placeholders commit together

## 5. Indexes after the load
**Warm-up.** (code) Look at the code on the screen. Why create the indexes after loading the rows rather than before?

```python
load_all_rows(con)
con.execute("CREATE INDEX idx_date "
            "ON rtb_all_combined (date)")
con.execute("CREATE INDEX idx_id "
            "ON rtb_all_combined (forbes_id)")
```

- A) SQLite cannot create an index on a table that has no rows yet
- B) An index created before the load would only cover the first batch of rows
- C) Building an index once over finished data beats updating it on every insert
- D) Indexes created early would make execute many reject rows with repeated dates

**Core.** Why does the loader index the date and forbes id columns in particular?
- A) The SQL filters, groups and joins on those columns
- B) They are the only two columns with no missing values
- C) SQLite needs an index on every text column it is asked to sort
- D) Together they form the primary key, which SQLite needs before it accepts inserts

**Deep.** (code) Look at the code on the screen. When is this trade acceptable?

```python
con.execute("PRAGMA journal_mode = OFF")
con.execute("PRAGMA synchronous = OFF")
```

- A) Always, because SQLite keeps a backup copy of the database file anyway
- B) Only for tables with fewer than a hundred thousand rows
- C) When the indexes are created before the load, since they protect the data
- D) When the database is a build artifact you can rebuild from the raw files

## 6. Deterministic exports
**Warm-up.** Why does every export query include an order by, even when the table was created already sorted?
- A) Without it, SQLite deliberately returns rows in a random order on every call
- B) A table has no guaranteed row order, so only an order by fixes it
- C) The order by also removes duplicate rows before they are written
- D) The CSV writer needs sorted rows to write the header line correctly

**Core.** (code) Look at the code on the screen. Why does the runner write floats with repr?

```python
>>> x = 0.1 + 0.2
>>> f"{x:.6f}"
'0.300000'
>>> repr(x)
'0.30000000000000004'
```

- A) Repr rounds to six decimals, which matches the authors' spreadsheet
- B) The fixed six-decimal format is too slow to write for millions of rows
- C) Repr pads every value to the same width, so the columns line up
- D) Repr is the shortest text that reads back as exactly the same number

**Deep.** The year-end export sorts by date, then worth descending, then forbes id. What is the forbes id for?
- A) It breaks ties, so people with equal worth always come out in the same order
- B) It groups each person's rows together across the seven dates
- C) It is the primary key, which every order by is required to end with
- D) It puts the top four first, since their ids sort before everyone else's

## 7. merge with indicator
**Warm-up.** (code) Look at the code on the screen. What does the underscore merge column hold?

```python
m = ours.merge(key, on="date", how="outer",
               indicator=True)
m["_merge"].value_counts()
```

- A) For each row, whether it was in both tables, only the left, or only the right
- B) The number of times each date matched, so duplicates show up as twos
- C) True where the values in both tables are equal, and false elsewhere
- D) The name of the table that each value column came from

**Core.** Why compare a result with an answer key by merging on the key, not row by row?
- A) Merging is faster than looping over rows in pandas
- B) A row by row check needs both tables to have exactly the same column order and names
- C) An extra row near the top would shift every later row and fake differences
- D) A merge also rounds the numbers, so tiny differences disappear

**Deep.** (code) Look at the code on the screen. When do these two counts mislead you?

```python
m = ours.merge(key, on="date", how="inner")
only_ours = len(ours) - len(m)
only_key = len(key) - len(m)
```

- A) Never. With an inner join, both counts are always exact
- B) When a date repeats on one side, since the inner join multiplies its rows
- C) When a value column has nulls, because inner joins drop any row with a null
- D) When the tables have different column names besides the date

## 8. Tolerance versus exact equality
**Warm-up.** The checker passes numbers that differ by up to one in a million. Why not demand exact equality?
- A) The answer keys round every value to six decimal places
- B) Python cannot compare two floats with an equals sign
- C) It allows for small vintage gaps, such as one missing person
- D) Adding the same numbers in a different order changes the last digits

**Core.** (code) Look at the code on the screen. One person is missing from our list. Can a wider tolerance make this check pass?

```python
TOL = 1e-6
ok = (n_ours == n_key
      and max_abs_diff <= TOL)
```

- A) Yes, if the tolerance is wider than that person's worth
- B) No. The counts differ, and counts must match exactly
- C) Yes, because a missing person only changes the sum, not the comparison
- D) No, because the largest difference becomes infinite whenever a row is missing

**Deep.** Suppose the R and Python exports agree to zero difference on every number, yet a few lines differ as text. How can that happen?
- A) R rounds to fifteen digits, so its numbers are slightly different
- B) R writes missing values as N A, which the parity check reads as text
- C) R sometimes writes seventeen digits where Python writes sixteen
- D) R sorts ties in a different order, which moves a few lines around

## 9. Exit codes
**Warm-up.** (code) Look at the code on the screen. Who is the exit code for?

```python
def main():
    ...
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
```

- A) Python's own error log, which records it whenever the code is not zero
- B) The person reading the output, since it is printed as the last line
- C) Whatever ran the script. A shell, a Makefile or a C I job can branch on it
- D) The next import of this module, which reads it as a cached result

**Core.** What is the R equivalent of sys dot exit with one?
- A) quit, with status equal to one
- B) warning, with a message
- C) returning one from the script's last function
- D) invisible of one at the end of the script

**Deep.** (code) Look at the code on the screen. Drill two fails. What happens?

```python
python module-07/check.py && \
  git commit -am "drills"
```

- A) The commit runs, because the checker still printed its report
- B) The commit runs, but git marks it as a failed commit
- C) The shell reruns the checker until it exits with zero
- D) Nothing is committed, since the checker exits with one

## 10. The R equivalents
**Warm-up.** Python runs the whole SQL file with execute script. What does the R twin do instead?
- A) It calls D B I db execute once on the whole file, which runs every statement
- B) It splits the file into statements and runs each through D B I db execute
- C) It passes the file to the sqlite3 program with a system call
- D) It calls Python's execute script through the reticulate package

**Core.** (code) Look at the code on the screen. Which R code is the closest match to this loop?

```python
reader = pd.read_csv("rtb_sample.csv",
                     chunksize=5000)
for chunk in reader:
    chunk.to_sql("rtb", con,
                 if_exists="append",
                 index=False)
```

- A) read csv with n max of five thousand, then D B I db write table
- B) D B I db write table on the whole file, which streams it in chunks by itself
- C) A for loop over read lines, appending one row at a time
- D) readr's read csv chunked, with a callback that appends each chunk through D B I

**Deep.** Which R check is closest to the checker's numeric test?
- A) max of abs of a minus b, at most one in a million
- B) all equal of a and b, which also uses the largest absolute difference
- C) identical of a and b, after rounding both to six decimals
- D) a equals equals b, wrapped in all

## 11. Function by function twins
**Warm-up.** Why does each Python file in the twin keep the same function names as its R file?
- A) Because Python can call R functions by name through a bridge package
- B) So each function can be checked side by side with its R original
- C) Because the R targets pipeline runs the Python files under those names
- D) Because Python requires a module's functions to match its file name

**Core.** (code) Look at the code on the screen. Why do the comments give R's version of each index?

```python
a = int(anchor[0])                 # 0-based; R's anchor_i is a + 1
D23 = np.mean(pareto_b_emp[a:n])   # average Pareto b above anchor
below = np.arange(a)               # R: seq_len(anchor_i - 1)
n_above_proj[below] = B[a] * (A[a] / A[below]) ** D24
```

- A) A converter reads the comments to write the matching R file
- B) Numpy needs the R index to line the arrays up with the years
- C) R counts from one and numpy from zero, so each comment ties the line to its R twin
- D) The parity test prints the R index when two values differ

**Deep.** The R code reproduces an odd spreadsheet rule for one average row. What should the Python twin do?
- A) Reproduce the same rule, since the twin exists to be compared with the R
- B) Compute the textbook average and let the parity test flag the gap
- C) Leave that row out, since spreadsheet quirks are not part of the analysis
- D) Fix the rule in Python only, since the Python version is the newer one

## 12. Reading a sheet with openpyxl
**Warm-up.** (code) Look at the code on the screen. What does data only equals true change?

```python
wb = openpyxl.load_workbook(
    path, data_only=True, read_only=True)
ws = wb["summary"]
for row in ws.iter_rows(values_only=True):
    ...
```

- A) Only cells holding data are read, so every empty cell is skipped on loading
- B) Cell formats such as dates and percentages are dropped on reading
- C) The workbook opens without its macros, which makes loading faster
- D) Formula cells return the value Excel last computed, not the formula text

**Core.** The twin's frame names its columns A, B, C and starts its index at one. Why?
- A) Because pandas cannot load a sheet unless the columns carry Excel letters
- B) So cell G16 is read as row sixteen, column G, like the R line it mirrors
- C) Because openpyxl numbers rows from one, and pandas cannot renumber them
- D) So that positional and label lookups always return the same cell

**Deep.** (code) Look at the code on the screen. Data ends in row twelve, and row twenty five has one bold but empty cell. How many rows does the frame keep?

```python
rows = [list(r) for r in ws.iter_rows(values_only=True)]
while rows and all(v is None for v in rows[-1]):
    rows.pop()
df = pd.DataFrame(rows, columns=excel_col_letters(width))
df.index = range(1, len(df) + 1)
```

- A) Twenty five, because the formatted cell makes the row count as used
- B) Twenty four, because the loop removes the last row once and then stops
- C) Twelve, because trailing rows that are entirely empty are dropped, as readxl does
- D) Thirteen, because one empty row is kept to mark the end of the data

## 13. A cell as R's as numeric sees it
**Warm-up.** A cell holds the text one, underscore, zero zero zero. What do R's as numeric and Python's float return?
- A) R gives missing, while float returns one thousand
- B) Both return one thousand, since both ignore underscores in numbers
- C) Both give missing, since an underscore is not a digit in either
- D) R gives one thousand, while float raises a value error

**Core.** (code) Look at the code on the screen. Why test for a bool before testing for a number?

```python
def to_num(v):
    if v is None or isinstance(v, bool):
        return math.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    ...
```

- A) Openpyxl returns booleans as text, so they would reach float and raise
- B) A bool would make float raise an error, since float rejects true and false
- C) Booleans mark formula cells, which have to be read with data only
- D) In Python true counts as an int, so it would become one, where R gives missing

**Deep.** Which of these cells gives missing in R but a number from Python's float?
- A) A number with spaces around it
- B) A cell holding true
- C) The text n slash a
- D) An empty cell

## 14. Indexes and sequences, R versus numpy
**Warm-up.** (code) Look at the code on the screen. In R, x minus one drops the first element. What does the last line give here?

```python
x = np.array([10.0, 20.0, 30.0, 40.0])
x[-1]
```

- A) Twenty, thirty and forty, the same three values that R would give
- B) An error, because numpy only accepts indexes of zero or more
- C) Forty, the last element, because negative indexes count from the end
- D) Ten, twenty and thirty, because minus one drops the last element of the array

**Core.** A yearly panel starts in 2018. In R the 2021 value is x four. Which numpy index gives it?
- A) Four, because the twin keeps R's index to stay comparable
- B) Three, because numpy counts from zero
- C) Five, because Python ranges stop one before their end
- D) Minus four, counting back from the end of an eight year panel

**Deep.** (code) Look at the code on the screen. R's sequence from zero to point two by point zero zero one has two hundred and one values. What do the two lengths show?

```python
r_like = 0 + np.arange(201) * 0.001
py_way = np.arange(0, 0.2, 0.001)
len(r_like), len(py_way)
```

- A) Two hundred one both times, because arange includes its end point, as R's seq does
- B) Two hundred both times, because rounding loses the last step in both
- C) Two hundred one, then two hundred two, because arange overshoots by a step
- D) Two hundred one, then two hundred, because arange stops before its end point

## 15. Missing values and counts in pandas
**Warm-up.** In R, n counts the rows in each group. Which pandas method is its twin?
- A) Size, which counts rows whether or not their values are missing
- B) Count, which counts the rows in each group of the grouped data frame
- C) Nunique, which counts the distinct rows in each group
- D) Value counts, which tallies how many rows each group holds

**Core.** (code) Look at the code on the screen. Every 2019 option profit is missing. What does this give for 2019, and what did R give?

```python
g = d.groupby("year")
out = g[cols].sum(min_count=1) / 1000
out.insert(0, "n", g.size())
```

- A) Zero in both, since min count only matters for groups with no rows
- B) Not a number in both, since R's sum also needs at least one value
- C) Not a number here, but zero in R, whose sum with n a dot r m returns zero
- D) An error here, since min count only works on columns with no missing values at all

**Deep.** A re-pasted row differs from its original only in a re-typed dividend. Why does drop duplicates with no arguments keep it?
- A) It keeps the last copy by default, and the last copy is the re-typed one
- B) It compares every column, so the re-typed cell makes the rows different
- C) It skips every row that contains a missing value somewhere
- D) It compares only the index, and the index differs on every row

## 16. The parity test
**Warm-up.** (code) Look at the code on the screen. Why divide by the larger of one and the R value, not by the R value alone?

```python
rel = abs(py - r) / max(1.0, abs(r))
ok = rel <= 1e-9
```

- A) To avoid dividing by zero, which is the only case where it matters
- B) To make the test absolute for every value larger than one
- C) Near zero, a tiny divisor would turn rounding noise into a huge relative gap
- D) To round the values below one before they are compared

**Core.** An R total is two trillion dollars, and the Python value differs in the last place, by about two ten thousandths. Which test passes it?
- A) One in a billion, absolute, since the gap is far below a single dollar of the total
- B) None, since any gap in a dollar total means a bug somewhere
- C) Only an exact text match, since both sides print the same digits
- D) One in a billion, relative, since the gap is a tiny fraction of the value

**Deep.** (code) Look at the code on the screen. What should the parity test say about this column?

```python
r = pd.read_csv("r/tax_rates.csv", dtype=str,
                keep_default_na=False)
py = pd.read_csv("py/tax_rates.csv", dtype=str,
                 keep_default_na=False)
r["avg_wealth_m"].tolist()
# ['NA', '49317.082454441741']
py["avg_wealth_m"].tolist()
# ['0.0', '49317.08245444174']
```

- A) Fail, because missing in R and a number in Python is a real difference
- B) Pass, because the numbers present agree, and zero is Python's missing
- C) Pass, because the second values differ only in their last printed digits
- D) Fail, because the second values are written with different digits

## Answer key

- 1.1 Chunked reading, Warm-up: **B**. With a chunk size, read csv returns an iterator. Each step of the loop gives the next block of rows, so memory holds one block at a time.
- 1.2 Chunked reading, Core: **D**. The Forbes file has about six million rows. Batching keeps memory flat, and each batch still goes in with one call.
- 1.3 Chunked reading, Deep: **A**. Inside the loop a batch is sent only when it is full. The leftover rows after the loop need one more call. The loader's final count check would catch the gap.
- 2.1 Empty string, NaN and None, Warm-up: **C**. The SQLite driver turns None into null. An empty string is stored as a value, and the string NULL is just text.
- 2.2 Empty string, NaN and None, Core: **A**. R's read csv trims spaces by default, and Python's readers do not. Stripping first makes a blank field null and keeps text equal to R's. Float itself accepts surrounding spaces.
- 2.3 Empty string, NaN and None, Deep: **D**. By default pandas treats several strings as missing, null among them. Reading with d type string and keep default n a false keeps them as text.
- 3.1 executescript versus execute, Warm-up: **A**. Execute refuses more than one statement with an error. A file of statements needs execute script.
- 3.2 executescript versus execute, Core: **C**. Execute script runs statements in order and stops at the first error. What ran before it stays. That is why each block starts with drop table if exists.
- 3.3 executescript versus execute, Deep: **B**. Execute script has no placeholders, so it is for trusted files only. For values, use execute with a question mark.
- 4.1 Parameter binding, Warm-up: **D**. Each question mark is a parameter. The values travel separately, and SQLite handles quoting, types and None.
- 4.2 Parameter binding, Core: **B**. Formatting values into SQL breaks on quotes, turns None into the word None, and allows injection. Placeholders avoid all three.
- 4.3 Parameter binding, Deep: **C**. One prepared statement, many rows. Formatting a new string per row makes SQLite parse every one of them.
- 5.1 Indexes after the load, Warm-up: **C**. An index has to be kept up to date on each insert. Six million small updates cost far more than one build at the end.
- 5.2 Indexes after the load, Core: **A**. Indexes pay off on the columns queries search by. Every block of the SQL filters or groups by date, and the joins use forbes id.
- 5.3 Indexes after the load, Deep: **D**. Turning off the journal and syncing makes a crash able to corrupt the file. That is fine for a file rebuilt in seconds, and not for one that holds the only copy.
- 6.1 Deterministic exports, Warm-up: **B**. Storage order can change when data grow or an index is added. Sorting by a fixed key is the only guarantee.
- 6.2 Deterministic exports, Core: **D**. Six decimals loses information. Repr keeps exactly enough digits, so the file only changes when a number changes.
- 6.3 Deterministic exports, Deep: **A**. Two people can have the same worth on the same date. Without a tie-breaker their order could flip between runs.
- 7.1 merge with indicator, Warm-up: **A**. Indicator adds a column with both, left only or right only. Counting its values gives the key comparison in one line.
- 7.2 merge with indicator, Core: **C**. Aligning on the natural key makes the check immune to row order and to rows present on one side only.
- 7.3 merge with indicator, Deep: **B**. Repeated keys make the inner join bigger than either side, so the subtraction can even go negative. An outer merge with an indicator counts sides directly.
- 8.1 Tolerance versus exact equality, Warm-up: **D**. Floating-point sums depend on the order of addition, and two programs rarely add in the same order. The real differences were about one in a trillion.
- 8.2 Tolerance versus exact equality, Core: **B**. The tolerance only applies to numbers on rows both sides have. A missing person changes the count, which has no tolerance.
- 8.3 Tolerance versus exact equality, Deep: **C**. R's text to number conversion is not always correctly rounded in the sixteenth digit, so the R writer sometimes needs seventeen. The doubles are identical, which is why parity compares numbers, not text.
- 9.1 Exit codes, Warm-up: **C**. Zero means success, anything else failure. Programs that run the checker can act on it without reading any text.
- 9.2 Exit codes, Core: **A**. quit with a status sets the exit code of an R script. A warning leaves it at zero.
- 9.3 Exit codes, Deep: **D**. The double ampersand runs the second command only if the first exits with zero. The grader exits with one on any failing drill.
- 10.1 The R equivalents, Warm-up: **B**. D B I runs one statement per call, so run s q l dot R splits the text itself, skipping semicolons inside comments and strings.
- 10.2 The R equivalents, Core: **D**. read csv chunked calls your function on each block of rows, like the for loop over pandas chunks. n max only reads the first rows.
- 10.3 The R equivalents, Deep: **A**. The checker takes the largest absolute difference. all equal compares a mean relative difference, and identical has no tolerance at all.
- 11.1 Function by function twins, Warm-up: **B**. The twin exists to be compared. Same names, same order and same shapes let a reader hold the R line and the Python line together.
- 11.2 Function by function twins, Core: **C**. A 2018-based panel's 2021 value is x four in R and x three in numpy. Keeping the R index in a comment makes the translation checkable by eye.
- 11.3 Function by function twins, Deep: **A**. A twin that quietly improves on the R stops being a check. A change belongs in both languages, or in neither.
- 12.1 Reading a sheet with openpyxl, Warm-up: **D**. Each formula cell stores the formula and its last computed value. R's reader returns the value, so the twin asks for it too.
- 12.2 Reading a sheet with openpyxl, Core: **B**. With letters as columns and sheet rows as the index, the Python lookup reads like R's dollar G of sixteen, which keeps the translation easy to check.
- 12.3 Reading a sheet with openpyxl, Deep: **C**. Openpyxl reports every row up to the formatted cell. The loop pops empty rows from the end until a row holds a value, which matches readxl.
- 13.1 A cell as R's as numeric sees it, Warm-up: **A**. Python accepts underscores as digit separators, R does not. The twin's to num function checks for an underscore so it matches R.
- 13.2 A cell as R's as numeric sees it, Core: **D**. Bool is a subclass of int in Python, so float of true is one. R reads a true cell in a text column as the word true, and as numeric makes that missing.
- 13.3 A cell as R's as numeric sees it, Deep: **B**. Both languages read a number with spaces. Both reject n slash a, R with missing and Python with an error. Float fails on an empty cell. Only true becomes one in Python.
- 14.1 Indexes and sequences, R versus numpy, Warm-up: **C**. In Python a negative index counts back from the end. R's x minus one is a slice from one in Python.
- 14.2 Indexes and sequences, R versus numpy, Core: **B**. R's first element is one and numpy's is zero, so every R index drops by one. The twin writes three and keeps four in a comment.
- 14.3 Indexes and sequences, R versus numpy, Deep: **D**. Arange never includes its stop value. The twin writes R's formula, start plus a whole number times the step, so it gets R's values.
- 15.1 Missing values and counts in pandas, Warm-up: **A**. Count skips missing values, like count of a column in SQL. A kept row with no worth is still a person, so the twin uses size.
- 15.2 Missing values and counts in pandas, Core: **C**. Plain pandas sum gives zero for an all missing group, as R does. Min count of one turns that zero into not a number.
- 15.3 Missing values and counts in pandas, Deep: **B**. Without a subset, a duplicate must match in every column. R's duplicated on year, id and worth, and pandas with that subset, both drop the copy.
- 16.1 The parity test, Warm-up: **C**. A check that should be zero and holds one in ten to the thirteenth would make a harmless gap look like a big one. The floor turns the test absolute near zero.
- 16.2 The parity test, Core: **D**. Two ten thousandths is far more than one in a billion, so an absolute test fails. Relative to two trillion, it is about one part in ten to the sixteenth.
- 16.3 The parity test, Deep: **A**. Missing values must sit in the same cells, whatever the tolerance. The second values are the same double, written two ways.
