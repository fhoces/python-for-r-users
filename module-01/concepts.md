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
import pandas as pd                # whole module, alias as pd
import numpy as np
from statsmodels.formula.api import ols    # specific name from a module
```

R equivalent: `library(...)`, but Python is **explicit** — you have to
name the module every time you use a function from it (`pd.read_csv`,
not `read_csv`). This is verbose but makes scripts easier to read.

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
