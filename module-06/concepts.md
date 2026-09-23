# Module 6: Reading and Reviewing Someone Else's Python

## Why this module breaks the pattern

Every module so far has used the same synthetic ride-sharing data. This one
doesn't, on purpose. The skill here isn't "do something with a dataset" —
it's **reading and reviewing a Python codebase you didn't write**, which is
a real and recurring task: "here's some code, walk me through it" or "find
the bug" in an interview, reviewing a PR or onboarding onto an unfamiliar
repo on the job. Synthetic ride-sharing toy code doesn't exercise that
skill, because you already know its shape before you open the file. Real
code with real structure does.

The review subject is `aiscen`, a ~1,100-line Python package that
reproduces an economics working paper's model, across eight files. You
don't need to know what the model computes — nothing here depends on
understanding labor markets or AI scenarios. The point is entirely
Python structure: how the files depend on each other, what each idiom is
doing, and how it maps onto something you already know from R.

## The strategy: how to read a codebase you didn't write

Before opening any file, three moves, in this order:

1. **Skim imports first, to find the dependency graph.** A file that
   imports nothing from the package is a leaf; a file that imports from
   several siblings sits near the top of the graph. This tells you the
   *order* to read in before you've understood a single function.
2. **Read leaves before the functions that call them.** Understanding a
   solver primitive in isolation is easier than understanding it while
   also holding the three callers that use it in your head.
3. **Find the one or two "verb" functions — the actual entry point.**
   Most files exist to support a single call that does the real work
   (here, `simulate.run()`). Everything else is scaffolding for that call.

Applied to `aiscen`, the import graph gives a clean read order:
`numerics.py` imports nothing from the package at all — pure leaf.
`report.py`, read last, imports from both `simulate.py` and `params.py` —
it's consuming the output of everything before it. The eight files below
are in exactly that dependency order, not alphabetical order.

## 1. `numerics.py` — solver primitives

Two functions, `bisect` and `expand_and_bisect`. No classes, no imports
from the rest of the package — the leaf of the dependency graph.

```python
def bisect(f, lo: float, hi: float, tol: float = 1e-14, maxiter: int = 200) -> float:
    """Bisection on a sign change in [lo, hi]."""
    ...
```

**Idiom: a function passed as a plain argument.** `bisect(f, lo, hi)` takes
`f` — some other function — as its first argument, with zero special
syntax. This is Python's version of R's `uniroot(f, ...)`. R users
sometimes expect "passing a function to a function" to need some kind of
functional-programming ceremony (as in `purrr`'s `~` formula shorthand);
in both languages, functions are just values you can hand around, and
Python's version of that is exactly this unadorned.

## 2. `params.py` — the parameter layer

Two frozen dataclasses, `Fixed` and `Scenario`; a `SCENARIOS` dict of
three named instances; a `scenario_from_2030_values()` constructor
function.

```python
@dataclass(frozen=True)
class Fixed:
    sigma: float = 0.5
    s_L0: float = 0.60
    ...
```

**Idiom: `@dataclass(frozen=True)` as an immutable record type.** This is
the closest thing Python has to R's copy-on-modify semantics — except
Python *enforces* it. Try `fixed.sigma = 0.6` on a frozen instance and you
get a `FrozenInstanceError`. Contrast with a plain R `list()`: R's
copy-on-modify means assigning `x$sigma <- 0.6` to a copy of a list never
touches the original binding, but nothing stops you from mutating the copy
itself — R has no "this object refuses to change" concept built in the way
`frozen=True` gives you here.

```python
SCENARIOS = {s.name: s for s in (MODEST, SUBSTANTIAL, EXTREME)}
```

**Idiom: a `dict` of named instances.** This is the Python equivalent of a
named `list()` of parameter objects in R — `SCENARIOS[["modest"]]` would be
the R spelling of `SCENARIOS["modest"]`. Built here with a dict
comprehension, the same comprehension syntax from Module 1.

## 3. `paths.py` — time paths

Small, pure math functions (`logistic`, `logistic_slope`,
`logistic_midpoint`) plus a `Paths` dataclass that bundles them.

```python
def logistic_slope(anchor: float, target: float, ceiling: float, years: float) -> float:
    ...
```

**Idiom: type hints as inline, unenforced documentation.** The
`-> float` and `anchor: float` annotations tell a reader (and an IDE) what
the function expects and returns, but Python does nothing to check them at
runtime — call `logistic_slope("a", "b", "c", "d")` and it fails inside the
function body with a normal `TypeError`, not at the call site. R has no
equivalent convention outside of add-on packages like `checkmate`; base R
functions carry no type signature at all, enforced or otherwise.

## 4. `steady.py` — the steady state

A `SteadyState` dataclass and `solve()`, which calls `numerics.bisect` to
find the values that make ten labor-market conditions hold at once.

```python
from .numerics import bisect
```

**Idiom: the relative import.** `from .numerics import bisect` — the
leading dot — means "from the sibling module `numerics.py` in this same
package," as opposed to a top-level `import numerics` that would look for
an independent installed package of that name. This is Python's way of
saying a file belongs to a package rather than standing alone; R's package
namespace system does the equivalent job differently, resolving
`::`-qualified names by NAMESPACE declarations rather than relative file
paths.

```python
def effective_search(U_C: float, U_N: float, mu: float) -> tuple:
    """Equation (33): S_C = U_C + mu U_N, S_N = mu U_C + U_N."""
    return U_C + mu * U_N, mu * U_C + U_N
```

**Idiom: returning a `tuple` for multiple values.** `return a, b` (really
`return (a, b)`) is Python's version of R's multiple-return idiom,
`list(a = ..., b = ...)`. The caller unpacks it the same way you'd pull
elements out of an R list, just positionally: `S_C, S_N =
effective_search(...)`.

## 5. `statics.py` — the largest file

Several dataclasses (`Frictionless`, `Actual`, `FirstOrder`) and a long
run of small functions, several of them prefixed with an underscore:
`_y_of_dlnr`, `_price_index_resid`, `_wages_at_employment`.

```python
def _price_index_resid(f, LamC, B, wtC, wtN, dlnr) -> float:
    """First row of (39): the CES price index equals one (the numeraire)."""
    ...
```

**Idiom: the leading underscore as "not public."** A name starting with
`_` is Python's convention-only signal that a function is an internal
helper, not part of the module's interface for outside callers — nothing
in the language actually blocks `from statics import _price_index_resid`
elsewhere. Contrast with R, where the `:::` operator and a package's
NAMESPACE file *do* enforce which names are exported and which aren't; a
non-exported R function can't be reached with `::` at all. Python's
underscore convention is a social contract, not a wall.

## 6. `simulate.py` — the entry point

A `Month` dataclass (one row of simulated output) and a `Result`
dataclass, plus `run()` — the function everything else in the package
exists to support.

```python
@dataclass
class Result:
    fixed: Fixed
    scen: Scenario
    paths: Paths
    ss: "SteadyState"
    months: list = field(default_factory=list)
```

**Idiom: `field(default_factory=list)` and the mutable-default-argument
trap.** Writing `months: list = []` directly, instead of going through
`field(default_factory=list)`, would create **one** list object at class
*definition* time and share it across every `Result` instance ever
created — appending to one instance's `months` would silently leak into
every other instance's. `default_factory` tells the dataclass "call `list()`
fresh for each new instance" instead. This is a genuine Python footgun that
R doesn't have: R's default arguments are re-evaluated lazily on *each
call*, so `f <- function(x, y = list()) ...` never shares one `y` across
calls the way a naively-written Python default would.

`run()` itself is the file's — and the package's — verb function: every
other file exists to be called from inside this one loop.

## 7. `slop.py` — a what-if extension

A sensitivity analysis built on top of the model, forking scenarios
without mutating them.

```python
def scale_gain(scen: Scenario, a_2030: float, name: str = None) -> Scenario:
    k = a_2030 / gain_2030(scen)
    return replace(scen, name=name or f"a={a_2030:.2f}",
                   a_anchor=scen.a_anchor * k, g_a=scen.g_a * k)
```

**Idiom: `dataclasses.replace()` to produce a modified copy.** This is the
single best "aha" moment in the package for an R user. `replace(scen,
a_anchor=..., g_a=...)` returns a *new* `Scenario` with just those two
fields changed and everything else copied — exactly the mental model of R's
`modifyList()`, or reassigning a field on a copy of a list
(`scen2 <- scen; scen2$a_anchor <- ...`). The difference is that because
`Scenario` is frozen, you're not *allowed* to do the R-style
copy-then-mutate; `replace()` is the only door in, which makes the
copy-on-modify idea explicit instead of implicit.

## 8. `report.py` — the consumption layer

Turns a `Result` into publication-style tables: a `pct()` formatting
helper, and functions that build a `dict` shaped like one column of a
table.

```python
PCT = 100.0

def pct(dln: float) -> float:
    """Percent above the no-AI path from a log gap."""
    return (math.exp(dln) - 1.0) * PCT
```

```python
return {
    "GDP, pct above no-AI": pct(m.dlnY),
    "Average wage, pct above no-AI": pct(m.dlnw_avg),
    ...
}
```

**Idiom: building and returning a `dict` as a table row/column.** There's
no special "table row" type here — just a plain dict mapping row labels to
values, built by hand and returned. This is the Python analogue of
building a `tibble::tibble(...)` row (or a named vector) one field at a
time in R: no framework, just a literal you construct yourself.

## Closing exercise: transfer the checklist to code you haven't seen explained

The exercise file pulls four more snippets from these same eight files —
things not walked through above — and asks you to name the idiom and its R
equivalent yourself before checking the answer. The goal isn't to
memorize these eight files; it's to leave with a checklist (imports →
entry point → leaves first) you can run on *any* unfamiliar codebase,
including whatever you're handed in an actual interview.
