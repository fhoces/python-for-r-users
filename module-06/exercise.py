"""
Module 6: Reading and Reviewing Someone Else's Python -- Exercise

Four snippets, pulled from the same eight files as concepts.md/slides.html
but NOT walked through there. For each one: read it, and before running this
file (or at least before reading past the snippet), write down in your head
(or out loud) what the idiom is doing and what the R equivalent would be.
Then run the file -- the answer follows each snippet as a comment block.

This isn't about aiscen's economics. You don't need to know what `m`, `d`,
`a`, or `psi` mean to answer any of these -- only what the Python is doing.

Run with: python module-06/exercise.py
"""

# =============================================================================
# Q1. From paths.py -- what is `@classmethod` doing, and what's the R
#     equivalent?
# =============================================================================

print("Q1. From paths.py:\n")
print('''    @dataclass(frozen=True)
    class Paths:
        fixed: Fixed
        scen: Scenario
        kappa_m: float
        ...

        @classmethod
        def build(cls, fixed: Fixed, scen: Scenario) -> "Paths":
            years = fixed.t_target - fixed.t_anchor
            kappa_m = logistic_slope(scen.m_anchor, scen.m_2030, m_ceiling, years)
            return cls(fixed=fixed, scen=scen, kappa_m=kappa_m, ...)

    p = Paths.build(fixed, scen)   # <- called on the CLASS, not an instance
''')

# ----- ANSWER -----
# `@classmethod` marks `build` as an alternate constructor: it's called on the
# class itself (`Paths.build(fixed, scen)`), not on an existing instance, and
# `cls` stands in for `Paths` inside the method body, so `cls(...)` constructs
# the new object. It exists because dataclasses generate one obvious
# constructor (fill in every field), and `build` needs to do real computation
# (solving for kappa_m, kappa_d, ...) before it has values for those fields.
#
# R equivalent: R has no per-class named alternate-constructor syntax --
# there's no "attach this function to the class definition as a second way to
# build one." The equivalent is just a separate plain function,
# `build_paths <- function(fixed, scen) { ...; new_paths(...) }`, that a
# caller uses instead of calling the base constructor directly. Same idea,
# no dedicated syntax.


# =============================================================================
# Q2. From simulate.py, inside run() -- what is this, and is the R
#     equivalent actually different this time?
# =============================================================================

print("\nQ2. From simulate.py, inside run():\n")
print('''    def run(fixed, scen, t_end=2030.0):
        ...
        ss = steady.solve(f)          # ss and iota come from the outer scope
        iota = f.iota_match
        ...
        def hires(S: float, v: float) -> float:
            if S <= 0.0 or v <= 0.0:
                return 0.0
            return ss.chi * S * v / (S ** iota + v ** iota) ** (1.0 / iota)

        row.H_C, row.H_N = hires(row.S_C, row.v_C), hires(row.S_N, row.v_N)
''')

# ----- ANSWER -----
# `hires` is a function defined INSIDE another function (`run`), used only in
# that one loop and thrown away afterward. It reaches `ss` and `iota` from
# run()'s own local variables without them being passed in as arguments --
# a closure over the enclosing scope.
#
# R equivalent: this is one of the rare cases where the answer is "R does
# this exactly the same way." Defining a function inside another function,
# and having it close over the enclosing function's local variables, works
# identically in R (`hires <- function(S, v) { ... ss ... iota ... }`
# written inside another function body). Not every idiom here is a
# translation -- some things transfer directly, and recognizing THAT is
# also part of reading someone else's code quickly.


# =============================================================================
# Q3. From slop.py -- what does this for loop do that a base-R for loop
#     over the same data can't do in one step?
# =============================================================================

print("\nQ3. From slop.py:\n")
print('''    variants = [
        ("substantial (baseline)", base),
        ("all-in gain halved", scale_gain(base, a0 / 2, "slop-half")),
        ("gain halved, checking becomes new human work",
         replace(scale_gain(base, a0 / 2), name="slop-rho", rho=0.50)),
    ]
    for label, scen in variants:
        col = table3_column(run(f, scen))
        ...
''')

# ----- ANSWER -----
# `variants` is a plain list of 2-tuples (label, scenario). The for loop does
# tuple unpacking: `for label, scen in variants:` pulls BOTH elements of each
# tuple into two separate names in one line, no indexing needed.
#
# R equivalent: base R has no built-in tuple-unpacking in a for loop. The
# direct translation would iterate by index and pull each piece out by hand,
# e.g. `for (i in seq_along(variants)) { label <- variants[[i]][[1]];
# scen <- variants[[i]][[2]] }`, or restructure as two parallel vectors and
# use `Map()`/`purrr::map2()`. This is a case where the Python is genuinely
# more concise than idiomatic base R for the same operation.


# =============================================================================
# Q4. From report.py -- unpack this one piece at a time. What does the
#     OUTER comprehension build, and what does the INNER expression build?
# =============================================================================

print("\nQ4. From report.py:\n")
print('''    def build_table3(f=None, t=2030.0) -> dict:
        cols = {"No AI": no_ai_column(f, t)}
        for name in ("modest", "substantial", "extreme"):
            cols[name] = table3_column(simulate.run(f, SCENARIOS[name], t_end=t), t)
        return {row: tuple(cols[c][row] for c in ("No AI", "modest", "substantial", "extreme"))
                for row in ROW_ORDER}
''')

# ----- ANSWER -----
# Read it inside-out. The inner piece, `tuple(cols[c][row] for c in (...))`,
# is a GENERATOR expression fed straight into `tuple(...)`: for one `row`
# label, walk the four scenario columns and pull out that row's value from
# each, producing a 4-element tuple (one number per scenario).
# The outer piece, `{row: ... for row in ROW_ORDER}`, is a dict comprehension
# that repeats that inner step for every row label, so the whole expression
# builds "row label -> (No AI, modest, substantial, extreme) values" for
# every row in one shot -- a comprehension nested inside a comprehension.
#
# R equivalent: nested `sapply`/`lapply` over the same two loop variables --
# something like `setNames(lapply(ROW_ORDER, function(row) sapply(col_names,
# function(c) cols[[c]][[row]])), ROW_ORDER)`. Same two-level "for each row,
# for each column" structure, spelled with nested apply calls instead of
# nested comprehensions.


print("\nDone. Re-read concepts.md's checklist (imports -> entry point -> "
      "leaves first) and try applying it cold to a file you haven't opened yet.")
