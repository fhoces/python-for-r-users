# Module 1: Python for R Users — The Cheat Sheet

## What this module covers

If you've used R seriously, you already know what data analysis looks like.
Python is just a different syntax over the same ideas. This module is the
**translation layer** — for every R idiom, here's the Python equivalent —
plus the small handful of Python-specific concepts that don't exist in R.

By the end of this module you should be able to read any Python data
analysis script and have a rough sense of what it does, even if you've
never written Python yourself.

## The big differences in 90 seconds

| | R | Python |
|---|---|---|
| Indexing starts at | 1 | **0** |
| Inclusive ranges? | Yes (`1:5` = 1,2,3,4,5) | No (`range(1,5)` = 0,1,2,3,4) |
| Assignment | `<-` (or `=`) | `=` |
| Statement separator | newline | newline (no semicolons) |
| Indentation | cosmetic | **load-bearing** (it defines blocks) |
| Vectorized? | Everything is | Lists no, NumPy/pandas yes |
| Missing values | `NA` (typed) | `None` / `np.nan` (untyped) |
| Comments | `#` | `#` |
| String escape | `"\n"` | `"\n"` |
| Function call | `f(x, y = 2)` | `f(x, y=2)` |

The biggest mental shift: **indentation is part of the syntax**. Python
has no `{}` for blocks; the indentation level *is* the block. A
4-space indent is standard.

## Variables and basic types

```python
# Numbers
x = 42
y = 3.14

# Strings
name = "Allison"
greeting = f"Hello, {name}!"     # f-string interpolation

# Booleans (capitalized!)
is_ready = True
is_done  = False

# None (Python's NULL)
maybe = None
```

R-isms that don't work: `<-` is two characters in Python (`<`
followed by `-`), so `x <- 5` is parsed as "is x less than minus 5"
and returns `False`. Use `=`.

## Lists, tuples, dicts, sets

These are the four core Python data structures.

### List — ordered, mutable

```python
nums = [1, 2, 3, 4, 5]
nums[0]                # → 1   (zero-indexed!)
nums[-1]               # → 5   (negative indices count from end)
nums[1:3]              # → [2, 3]   (right end exclusive)
nums.append(6)         # mutates in place
len(nums)              # → 6
```

R equivalent: a `list()` (sort of). Python lists are NOT vectorized —
`nums + 1` doesn't work. For vectorized math you need NumPy or pandas.

### Tuple — ordered, immutable

```python
point = (3.0, 4.0)
x, y = point           # destructuring
```

R has no exact equivalent. Use tuples for fixed-size, fixed-meaning
collections (return values, dict keys, etc.).

### Dict — key-value, like a named R list

```python
ride = {"id": 42, "fare": 15.5, "city": "SF"}
ride["fare"]                       # → 15.5
ride.get("missing", "default")     # → "default" instead of error
ride.keys()                        # dict_keys(['id', 'fare', 'city'])
ride.items()                       # iterable of (key, value)
"city" in ride                     # → True
```

This is the workhorse data structure for everything not in a DataFrame.

### Set — unordered, unique

```python
seen = {1, 2, 3, 2, 1}             # → {1, 2, 3}
seen.add(4)
3 in seen                          # → True
```

Same as R's `unique()` semantically; faster lookup than a list.

## Comprehensions: the Python idiom

This is the one piece of syntax that doesn't directly translate from
R but is essential to write idiomatic Python.

```python
# List comprehension
squares = [x ** 2 for x in range(10)]
# → [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# With a filter
evens = [x for x in range(20) if x % 2 == 0]
# → [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Dict comprehension
square_map = {x: x ** 2 for x in range(5)}
# → {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

R equivalent: `sapply()`, `purrr::map()`, or a `for` loop. The Python
comprehension is shorter and considered more "Pythonic" than the loop
version.

## Control flow

```python
if x > 0:
    print("positive")
elif x == 0:
    print("zero")
else:
    print("negative")

for item in nums:
    print(item)

while x > 0:
    x -= 1
```

The `:` after the condition and the indentation are both required.
There are no parentheses around the condition.

## Functions

```python
def mph(distance, minutes):
    """Compute miles per hour given distance (mi) and time (min)."""
    return distance / (minutes / 60)

mph(5, 15)   # → 20.0

# Default arguments
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet("Maya")               # → 'Hello, Maya!'
greet("Maya", "Welcome")    # → 'Welcome, Maya!'

# Lambda (anonymous function, like R's \(x) ...)
square = lambda x: x ** 2
```

R equivalent: `function(distance, minutes) { ... }`. The Python `def`
keyword is the only way to define a multi-line function — no curly
braces.

## File I/O and CSV reading

```python
# Read a text file
with open("notes.txt") as f:
    content = f.read()

# Read a CSV (using pandas — covered in detail in Module 2)
import pandas as pd
rides = pd.read_csv("data/rides.csv")
rides.head()
```

The `with` statement is Python's resource-management idiom (R has no
direct equivalent — sort of like `withr::with_*` from the withr package).

## Imports

```python
import os                          # standard library first

import numpy as np
import pandas as pd                # whole module, alias as pd
from statsmodels.formula.api import ols    # specific name from a module
```

R equivalent: `library(...)`, but Python is **explicit** — you have to
name the module every time you use a function from it (`pd.read_csv`,
not `read_csv`). This is verbose but makes scripts easier to read.

**Import order is a convention.** Standard-library modules (`os`, `csv`,
`pathlib`) come first, then a blank line, then third-party packages
(`numpy`, `pandas`, `statsmodels`), alphabetical within each group. Linters
such as Ruff flag any other order (rule I001), and "Organize imports" in
the editor fixes it. When a `def` or `class` follows the imports, leave two
blank lines before it (PEP 8 puts two blank lines around every top-level
function). Ruff flags a single blank line under the same rule. Neither the order
nor the spacing changes what the code does.

## The 10 things that trip up R users

1. **Zero-indexing.** `x[0]` is the first element, not `x[1]`. Slicing
   is right-exclusive: `x[1:3]` is items 1 and 2.
2. **Indentation is syntax.** A misplaced space breaks your script.
3. **No vectorized math on lists.** `[1,2,3] + 1` is a `TypeError`. Use
   NumPy or pandas.
4. **`==` for comparison, `=` for assignment.** Like R, but Python doesn't
   have `<-`.
5. **Booleans are `True`/`False`, capitalized.** `true` is undefined.
6. **`None` instead of `NULL`/`NA`.** No type information. NumPy and
   pandas use `np.nan` for missing floats.
7. **Method calls vs function calls.** `nums.append(6)` mutates `nums`
   in place; `sorted(nums)` returns a new sorted copy without mutating.
   You'll mix these up at first.
8. **Mutability.** Lists, dicts, and sets are mutable; tuples and
   strings are not. Default function arguments are evaluated *once* at
   definition time, which leads to subtle bugs with mutable defaults.
9. **`for` loops are cheap and idiomatic.** R culture frowns on
   `for`; Python culture is fine with them, especially with comprehensions.
10. **`print()` is a function**, not a statement. `print "hello"`
    doesn't work in Python 3.

## In the wild: real code from one reproduction

Modules 1 to 5 each end with a short slide of real Python. The source is
one reproduction: the BSZ step of
[`fhoces/opa-prop40`](https://github.com/fhoces/opa-prop40), folder
`bsz-analysis/py/`. BSZ is a paper on California billionaires. Module 7
reads that same code file by file. The excerpts are condensed to a few
lines of each function, with the names unchanged. Ignore what the code
computes. The point is the idiom, read with its R twin next to it.

### A dict of functions (`load_bundle.py`)

```python
LOADERS = {
    "rtb_all_combined": load_rtb_all_combined,
    "rtb_ca_cik": load_rtb_ca_cik,
    "comp_daily_form4": load_comp_daily_form4,   # needs a query's output, so never by default
}
DEFAULT_TABLES = [t for t in LOADERS if t != "comp_daily_form4"]

def main(argv):
    wanted = argv or DEFAULT_TABLES
    unknown = [t for t in wanted if t not in LOADERS]
    if unknown:
        sys.exit(f"Unknown table(s): {', '.join(unknown)}. Known: {', '.join(LOADERS)}")
    for table in wanted:
        n = LOADERS[table](con, root)
```

One `load_<table>()` function per raw input, and a registry that maps a
name to the function. Adding an input means writing one function and one
line in `LOADERS`; `main()` never changes. The idioms, with their R twins:

- `LOADERS[table](con, root)`: a function is a value, so the dict can hold
  it and the call applies to whatever the lookup returns. R: a named list
  of functions, `loaders[[table]](con, root)`.
- `argv or DEFAULT_TABLES`: an empty list is falsy, so `or` picks the
  default. R: `if (length(argv)) argv else default`.
- `for t in LOADERS` walks the keys (R: `names(loaders)`), and
  `", ".join(LOADERS)` joins them (R: `paste(names(loaders), collapse = ", ")`).
- `sys.exit("text")` prints to stderr and exits with code 1. R: `stop()`.

### Three comprehension moves

```python
FORM4_INT = {
    "filer_cik", "document_type", "table", "num_owners", "single_owner",
} | {f"owner_{k}_{i}" for k in ("director", "officer", "ten_percent", "other")
     for i in range(1, 11)}
...
if h in FORM4_INT:        # R: h %in% form4_int
```

A set literal joined to a set comprehension by the union operator. The two
`for` clauses read like nested loops, outer first, so 4 kinds times 10
slots give 40 names, each built by an f-string. R would write
`paste0("owner_", rep(kinds, each = 10), "_", 1:10)`. Membership on a set
is a hash lookup; on a list it scans the list; the code reads the same.

`compute_shortrunseries.py` merges dicts with `**` and then names the keys
the way R's `unlist()` names a nested list, which is what its parity test
compares against:

```python
for k, v in {**pub, "top3": AG14, "top2": AH14}.items():
    out[f"top5_public_b.{k}"] = v     # R: c(pub, top3 = AG14, top2 = AH14), then unlist()
```

The exercise file ends with a drill on the registry pattern (Q6).

### Running the real thing: `score_tab5_cell()` (exercise Q7)

The excerpts above are condensed. Q7 copies one function whole, from
`compute_tab5.py`, and runs it. `score_tab5_cell()` is the estimating
function behind the repo's
[explorer](https://fhoces.github.io/opa-prop40/bsz-analysis/site/explorer/).
It takes a dict of eight inputs and six assumptions, and it returns a dict of
seven outcomes. This drill keeps the economics, because the numbers are the
check. The defaults are the authors' base scenario, and the drill reproduces
the explorer's main estimate of $106.8 billion.

The Module 1 idioms it uses, with their R twins:

- Keyword arguments with defaults, `def f(inp, avoidance=0.10, ...)`. R
  writes the same thing as `function(inp, avoidance = 0.10, ...)`. A call
  that names one argument keeps the defaults for the rest.
- The one-line if/else, `x if cond else 0`. R writes `if (cond) x else 0`.
  The function uses it to switch a term off.
- A dict as the return value. R would return a named list.
- `**settings` unpacks a dict into keyword arguments. R does this with
  `do.call()`.
- A dict comprehension that sweeps one argument over its levels. R would use
  `sapply()` over a named vector.

## Interview-style questions for this module

1. Write a function `mph(distance, minutes)` that returns miles per
   hour.
2. Given `rides = [{'city':'SF','fare':12}, {'city':'NY','fare':18},
   {'city':'SF','fare':9}]`, compute the average fare for SF.
3. Read `data/rides.csv` with pandas and show the first 5 rows.
4. Invert a dict (swap keys and values), assuming all values are unique.
5. Given a list of numbers, return only the unique even numbers in
   sorted order.

The exercise file works through all of these.

## What's next

Module 2 introduces **pandas**, which is to Python what `dplyr` is to
R. Module 3 covers joins and merges. Module 4 covers regressions and
A/B tests with `statsmodels` (the R-style formula interface). Module 5
puts it all together in an end-to-end interview scenario.
