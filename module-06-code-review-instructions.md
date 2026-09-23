# Instructions: build Module 6 — Reading and Reviewing Someone Else's Python

**This file is a spec, not the module.** Read it, then build `module-06/`
following the house conventions in `../CLAUDE.md` (courses collection) and
this repo's own `learning-plan.md` / existing modules 1-5. Verify your
understanding against the actual source files below before writing
anything — don't take this document's descriptions of the code on faith.

## Why this module, and why it's a deliberate domain exception

Every module so far uses the ride-sharing synthetic data
(`data/drivers.csv`, `rides.csv`, ...), per the courses collection's stated
convention ("ride-sharing... unless there's a specific reason not to").
This module has that reason: the point isn't the data, it's the skill of
**reading and reviewing an unfamiliar Python codebase you didn't write** —
a real thing that comes up in interviews ("here's some code, walk me
through it" / "find the bug" / "how would you extend this") and on the
job (reviewing a PR, onboarding onto a new repo). Synthetic ride-sharing
toy code doesn't exercise that skill; real code with real structure does.
Say so explicitly in `concepts.md`'s opening, so the domain break reads as
a choice, not an oversight.

## Source material

The review subject is `aiscen`, a real ~1,100-line Python package that
reproduces an economics paper's model, at:

```
/Users/fernando/Desktop/sandbox/opa-ai-macro-econ-scenarios/aiscen/
```

This is a **separate, live git repository** — read from it, never write to
it. Copy the specific snippets/functions you want to teach from into this
course's own `module-06/` files (as illustrative excerpts, not a live
import — the module should not depend on that repo existing). Re-read each
file yourself before writing about it; the summaries below are a starting
map, not a substitute.

Eight files, in **recommended review order** (this is itself the first
lesson — read in dependency order, leaves first, not alphabetical or
file-listing order):

| Order | File | Lines | What it is |
|---|---|---|---|
| 1 | `numerics.py` | 39 | Two solver primitives: `bisect`, `expand_and_bisect`. No classes, no imports from the package itself. |
| 2 | `params.py` | 170 | The parameter layer: `Fixed` and `Scenario` frozen dataclasses, a `SCENARIOS` dict of named instances, a `scenario_from_2030_values()` constructor. |
| 3 | `paths.py` | 89 | Time paths: small pure math functions (`logistic`, `logistic_slope`, ...) plus a `Paths` dataclass. |
| 4 | `steady.py` | 92 | `SteadyState` dataclass; `solve()` calls `numerics.bisect` to find the model's steady state. |
| 5 | `statics.py` | 247 | The largest file: several dataclasses (`Frictionless`, `Actual`, `FirstOrder`) and many small functions, some prefixed `_` (private helpers). |
| 6 | `simulate.py` | 225 | `Month` and `Result` dataclasses; `run()` is the main entry point — the monthly solve loop everything else feeds into. |
| 7 | `slop.py` | 112 | A what-if extension built on top of the model, using `dataclasses.replace()` to fork a scenario without mutating it. |
| 8 | `report.py` | 144 | The consumption layer: turns a `Result` into publication-style tables and a diff string. |

Notice the shape: `numerics.py` imports nothing from the package;
`report.py` (read last) imports from `simulate.py` and `params.py`. That's
the general strategy worth teaching explicitly, not just per-file trivia:
**skim imports first to find the dependency graph, then read leaves before
the functions that call them, and find the one or two "verb" functions
(here, `run()`) that are the actual entry point** — everything else exists
to support that call.

## Idioms worth pointing at, file by file (verify each against the source)

Frame every one of these as "here's the Python idiom, here's the R mental
model it maps to" — that contrast is this whole course's reason to exist.

- **`numerics.py`** — a function passed as a plain argument (`bisect(f, lo,
  hi)`) is Python's version of R's `uniroot(f, ...)`; nothing special
  syntactically, but worth naming since R users sometimes expect functions
  to need special "functional" ceremony they don't in Python.
- **`params.py`** — `@dataclass(frozen=True)` is the closest Python gets to
  R's copy-on-modify semantics: an *immutable* record type. Contrast with a
  plain R `list()`, which is copy-on-modify by default but never
  enforces immutability. `SCENARIOS` as a `dict` of named instances is the
  Python equivalent of a named `list` of parameter objects in R.
- **`paths.py`** — plain functions with type hints (`-> float`) as inline,
  unenforced documentation — contrast with R's total absence of a type
  hint convention outside of packages like `checkmate`.
- **`steady.py`** — importing a solver you wrote in a sibling module
  (`from .numerics import bisect`) and a function returning a `tuple`
  (`effective_search`) as this package's version of R's multiple-return
  idiom (`list(a = ..., b = ...)`).
- **`statics.py`** — the leading-underscore convention (`_y_of_dlnr`,
  `_price_index_resid`) as Python's (unenforced, convention-only) way of
  marking "not part of this module's public interface" — contrast with R's
  `::: ` internal-access operator and NAMESPACE exports, which *are*
  enforced by the package system.
- **`simulate.py`** — check whether `Month`/`Result` use `field(...)` for
  any default value (e.g. a list or dict default) and if so, explain the
  Python mutable-default-argument trap it exists to avoid — a footgun R
  doesn't have, since R's default arguments are re-evaluated per call
  (lazy evaluation) rather than created once at def time.
- **`slop.py`** — `dataclasses.replace(scen, a_anchor=..., g_a=...)` to
  produce a modified copy of a frozen object. This is the single best
  "aha" moment for an R user: it's exactly the mental model of
  `modifyList()` or reassigning a field on a copied list, made explicit
  because the object refuses to be mutated in place.
- **`report.py`** — a small `pct()` formatting helper and functions that
  build and return a `dict` shaped like a table row/column — the Python
  analogue of building a `tibble::tibble()` row by hand.

## What to build

Standard **concept → show → drill** trio, matching modules 1-5 exactly
(see `../CLAUDE.md` "Module structure" and this repo's own module-05 for
the closest precedent — it's also a synthesis/capstone-style module).

- **`module-06/concepts.md`** — open with the domain-exception note above
  in one short paragraph, then state the code-reading strategy as its own
  named checklist (imports → entry point → leaves-first), then one section
  per file (in the order above) covering: what the file is for in one
  sentence, the one or two idioms worth naming from the list above, and
  the R-equivalent framing for each. Keep the economics itself out of it
  entirely — a reader shouldn't need to know what `psi` or `rho` mean; the
  lesson is about Python structure, not the model's substance.
- **`module-06/slides.Rmd`** — house xaringan boilerplate from
  `../CLAUDE.md` (Course Map on slide 1, the standard CSS/knitr chunks,
  16:9). Structure: a strategy slide (the checklist) before touching any
  code, then one or two slides per file showing the actual excerpted
  snippet with the idiom highlighted (`highlightLines`), closing with a
  synthesis slide restating the checklist as something to run on *any*
  new codebase, not just this one. Use `.small[]` for any snippet over
  ~15 lines, per this collection's dense-content convention.
- **`module-06/exercise.py`** — a drill in this course's existing
  `# ===== Q1. Title =====` section-header style, but reviewing rather
  than writing: give the learner a short unannotated snippet (pulled from
  one of the eight files, e.g. a function from `statics.py` they haven't
  seen explained) and a fill-in-the-blank comment asking them to name the
  idiom and its R equivalent, for 3-4 snippets across different files.
  Answers can go in a trailing comment block, same pattern as this
  course's existing exercises use for solutions.

## Bookkeeping — do all of these, per `../CLAUDE.md`

- Add Module 6 to the table in `learning-plan.md` and to `README.md`'s
  modules table.
- Add it to `index.html`'s nav with a status cell.
- Update the **Course Map slide (slide 1)** in every existing module
  (1 through 5) to include Module 6, not just the new module's own Course
  Map — this collection's convention requires updating it everywhere when
  a module is added.
- Use the `sync-course-map` skill to do the Course Map update rather than
  hand-editing five files, and `audit-module` + `verify-slides` (or
  `qa-deck` for a full pass) to check the new module before calling it
  done, matching this collection's usual build workflow.

## Explicitly out of scope

- Do not explain what the `aiscen` model itself computes (labor markets,
  AI scenarios, etc.) — that's a different repo's subject matter and would
  bury the Python lesson.
- Do not add a dependency from this course to the `opa-ai-macro-econ-scenarios`
  repo (no imports, no path references at runtime) — copy the illustrative
  snippets in as static text/code blocks.
- Do not touch `opa-ai-macro-econ-scenarios` itself in any way while building
  this module.
