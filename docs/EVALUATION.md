# calc-cli-3 — Evaluation & Upgrade Report

- **Commit evaluated:** `4742442` (`milestone: M3-real & M4-real — view polish and package wiring complete, 365 tests green`)
- **Date:** 2026-08-05
- **Method:** independent post-run review — the full source, tests and docs were read, the test
  suite was re-run (365 passed, deterministic), and every defect below was **reproduced** against the
  shipped interpreter (not inferred from logs). Six dimensions were each evaluated and then
  adversarially re-verified.
- **Purpose:** a durable record of what the swarm actually delivered, so the next iteration can be
  scored against it and the upgrades below can be planned.

---

## 1. Verdict

The calculator is **architecturally excellent and correct for non-negative arithmetic, but not
ship-grade** — one table-stakes capability, *negative numbers*, is broken, and it fails in the worst
possible way for this product's own promise: several ordinary inputs return a **silently wrong number**
with no "Error" at all. The goal says the app must *"show a friendly Error … never a crash"*; a
confidently wrong answer is worse than the crash it forbids.

The engine / controller / view split is textbook, the arithmetic core (shunting-yard) is clean, and the
build is genuinely headless-testable. The 365-test suite, however, **overstates assurance**: it never
tests negative numbers (and two tests actively lock in the wrong behavior), and ~42% of tests validate
the GUI by reading source text rather than running it.

| Dimension | Score | One-line |
|---|:--:|---|
| Arithmetic engine | 5 / 10 | Clean shunting-yard; no unary minus; `-0` and large-number formatting bugs |
| Controller state machine | 4 / 10 | Solid for positives; negative numbers wrong in 4 transitions |
| GUI / view / keyboard | 6 / 10 | Correct thin view; minus-glyph mismatch, no `+/-`, `=` key unbound |
| Test-suite quality | 5 / 10 | Strong engine/controller tests; GUI tested by AST; blind to the headline bug |
| Architecture & packaging | 7 / 10 | Ship-grade layering & entry points; dirty tree at finalize |
| Goal coverage & product | 6 / 10 | Meets nearly every listed requirement except negatives |
| **Overall** | **≈ 5 / 10** | **Works and is well-built, but a headline feature is broken and untested.** |

---

## 2. How the build run went

From `logs/run-20260805-032515.log` (the framework side), the run was healthy and completed cleanly:

- **Outcome:** `FINISHED - goal complete`, `ALL_MILESTONES_DONE`; work branch pushed and `main`
  fast-forwarded. Re-running the suite here confirms **365 passed**, reproducible across reruns.
- **Progression:** two passes as designed — stubs (29 → 166 tests) → one environment self-heal →
  real (248 → 259 → 307 → 328 → 353 → **365**).
- **Stability:** no tracebacks, no timeouts, zero "rethink" escalations. The tester hit its inner
  step cap ("need more steps") 3× and was retried to green — benign.
- **Identity:** the run was correctly pinned to **FDHKRsss** (token-scoped); the machine's active
  account was left untouched. Commits are authored by FDHKRsss's GitHub no-reply identity.
- **One blemish:** the run was declared "delivered" over a **dirty working tree** — the final quality
  sweep deleted `tests/_check_view_ast.py` but never committed/pushed the deletion, so `origin` still
  ships the file. See §7.

---

## 3. What works well

- **Textbook architecture (verified by imports).** `engine.py` imports only `operator` + `typing`;
  `controller.py` imports only `calc.engine.evaluate`; `view.py` is the *only* module importing
  `tkinter` and contains no arithmetic. Layering is strictly one-directional: view → controller →
  engine. The view is genuinely thin (`_on_press` is `press(); refresh()`; `refresh()` is one line).
- **Correct core arithmetic.** Precedence and left-associativity are right; parentheses handle deep
  nesting iteratively (200-deep parens don't stack-overflow); leading-dot (`.5`) and trailing-dot
  (`5.`) decimals parse; division-by-zero is guarded *before* the division, not caught after.
- **The "never raises" contract genuinely holds.** An outer `try/except` plus structural validators
  return `"Error"` for every malformed shape — including non-string input (`None`, `5`).
- **Both entry points are real.** `main()` exists in `calc/__main__.py`; `python -m calc` and the
  `calc` console script (`calc.__main__:main`) both resolve (confirmed in generated egg-info).
- **Clean packaging & repo hygiene.** Public `setuptools.build_meta` backend; `requires-python
  ">=3.9"` is *accurate* (PEP 585 generics + `typing.Union`, no `X | Y`, no `match`); no build
  artifacts are committed.
- **Immediate keyboard input.** Buttons are `takefocus=False`, bindings are on the root, and
  `focus_set()` runs in `__init__`, so typing works on launch without clicking. Numpad is covered.

---

## 4. Confirmed defects (all reproduced)

Ranked most-severe first. Every row was reproduced against the shipped code; repros are collected in
the Appendix.

| # | Severity | Defect | Symptom |
|:--:|:--:|---|---|
| 1 | **High** | Engine has no unary minus | `-5`, `3*-2`, `(-2)` → `Error` |
| 2 | **High** | Negative literals silently mis-evaluated (controller) | `−5` → `5`; `(3)×−2` → `1`; `2×(−3)` → `6`; `−3+5` → `8` |
| 3 | **High** | Cannot continue from a negative result | `2−5=` (=`-3`) then `+2=` → `Error` |
| 4 | **High** | GUI event-wiring has **zero** executed test coverage | mis-wiring every key to `9` still passes all tests |
| 5 | Medium | `-0` display | `0.3−0.1−0.2` → `-0` (and a test *asserts* this) |
| 6 | Medium | Float noise on large magnitudes | `123456789.123*1` → `123456789.122999995946884` |
| 7 | Medium | Minus glyph mismatch | button shows `−` (U+2212), display shows `-` (U+002D) |
| 8 | Low | Overflow → generic `Error` | `1e309*10` → `Error` (no "too big" signal) |
| 9 | Low | `=` physical key unbound | only Return / numpad-Enter / clicking `=` evaluate |
| 10 | Low | No paren-balance guard | `)(` is accepted verbatim into the display |

### The negative-number cluster (#1–#3) — the headline problem

All three share one root cause: **the engine treats `-` only as binary subtraction and has no unary/sign
concept, and the controller has no negative-literal concept.** The consequences are severe because they
are *silent*:

- **`_shunting_yard` rejects a `-` in number position** (`engine.py:155-156`: `if expect_number:
  return None`). So `evaluate('-5')`, `evaluate('3*-2')`, `evaluate('(-2)')` all return `"Error"`.
- **The controller drops the `-` three different ways** rather than making a negative number:
  - leading `-` on an empty expression is swallowed (`controller.py:139-140`) → `−5` becomes `5`;
  - `-` after another operator **replaces** it (`controller.py:141-144`) → `(3)×−2` becomes `(3)-2 = 1`;
  - `-` after `(` is swallowed (`controller.py:145-146`) → `2×(−3)` becomes `2×(3) = 6`.
- **Negative results can't be reused.** On operator-after-result the controller copies the display
  straight back into the expression (`controller.py:117`), so a `-3` result rebuilds the expression
  `-3+2`, which the engine then rejects → `Error`. The app can *produce and display* a negative number
  it cannot *consume*.

> This is the single most important finding: the goal targets Windows-Calculator behaviour and promises
> "never a crash — a friendly Error." Instead, the most common negative-number interactions return a
> **plausible wrong number with no signal**. That is a worse failure than an honest `Error`.

### #4 — the GUI's own wiring is never executed by a test

The two things the view is actually responsible for — the `self._root.bind(...)` keyboard bindings and
the button `command=` callbacks — have **no executed coverage**. This was proven by mutation: rewiring
every binding and every button command to fire `_on_press("9")` regardless of the real key still leaves
**all view/package tests green (154 passed)**. `test_view_wiring.py` bypasses `__init__` with
`object.__new__` and calls `_on_press` directly; `test_package_wiring.py` mocks `CalculatorView`
entirely; `test_view_polish.py` / `test_view_takefocus.py` are AST assertions ("the source text
contains this literal"). A broken keyboard, wrong grid, or non-firing lambda would ship green.

### #5–#6 — display formatting

`_format_result` (`engine.py:222-234`) uses `f"{value:.15f}"` — a *fixed* 15 fractional digits,
magnitude-blind:

- results that cancel to a tiny negative render as `-0` (`0.3-0.1-0.2`), and
  `test_engine.py:327-333` *asserts `-0` as correct*, so the suite protects the bug;
- large-magnitude results leak floating-point noise into the display
  (`123456789.123*1` → `123456789.122999995946884`).

The fix is significant-figure formatting + normalizing any zero-valued result to `"0"`.

---

## 5. Goal coverage

| Goal requirement | Status | Note |
|---|:--:|---|
| Tkinter (stdlib only), Windows-styled window | ✅ Met | display + 5×4 grid, no third-party deps |
| Buttons: 0-9 `.` `+ − × ÷` `( )` `C` `⌫` `=` | ✅ Met | all 20 controller keys present |
| Mouse **and** keyboard input (+ numpad) | ⚠️ Partial | works, but `=` physical key unbound; no `+/-` |
| Correct operator precedence | ✅ Met | shunting-yard, left-associative |
| Decimals | ✅ Met | incl. leading-dot `.5` |
| Parentheses | ✅ Met | deep nesting safe |
| **Negative numbers** | ❌ **Missed** | unary minus unsupported end-to-end (defects #1–#3) |
| Div-by-zero / malformed → friendly "Error", keep typing | ⚠️ Partial | true for div-by-zero & garbage; **violated** for negatives (silent wrong answers) |
| Never a crash / stack trace | ✅ Met | `evaluate()` never raises |
| Pure engine · headless controller · thin view | ✅ Met | strictly layered, GUI-free logic |
| Unit-testable without a display | ✅ Met | no test opens a live display |
| `calc` entry point (`python -m calc` / `calc`) | ✅ Met | both verified |
| pytest suite over engine + controller | ✅ Met | but see §6 for coverage gaps |
| Short README (launch + window look) | ✅ Met | accurate ASCII mock, fonts, colors |

Two Windows-Calculator parity gaps beyond the goal's literal checklist: repeated `=` does **not**
repeat the last operation (`2+3==` → `5`, not `8`), and there's no `%`, memory keys, or history strip.

---

## 6. Test-suite assessment

365 green tests, but the number flatters the build:

- **Genuinely strong:** the engine (~111) and controller (~89) behavioral suites — precedence,
  parentheses, decimals, div-by-zero, ~35 malformed-input cases, an explicit "never raises" fuzz over
  14 adversarial key sequences, and headless state-machine recovery. These are real, parametrized, and
  meet the "testable without a display" requirement.
- **Blind to the headline bug:** *zero* negative-number tests. `test_negative_results` only checks that
  subtraction *produces* a negative; nothing feeds one back in. Worse, **two tests lock in the wrong
  behavior** — `test_no_leading_operator` (`test_controller.py:90`) asserts a leading `-` is swallowed,
  and `test_engine.py:162` asserts `1+-2 → Error`. A correct fix must *change* these tests, so the suite
  currently resists the fix rather than driving it.
- **GUI tested by reading source:** 154 tests (~42%) are AST / string-literal / mocked-widget
  assertions with no executed wiring (see defect #4). `takefocus=False` is asserted 6 times; colors and
  fonts are pinned as exact source literals, so harmless refactors (rename `_root`, `tk.Button` →
  `ttk.Button`, extract a `COLORS` constant) break tests with no behavior change.
- **Missing:** any live-Tk smoke test (even one skipped-without-display construction), equals-time
  malformed-expression coverage at the controller layer, and coverage measurement (no `pytest-cov`).

---

## 7. Upgrade roadmap (prioritized)

### P0 — correctness (do first)

1. **Add unary minus end-to-end (engine + controller + result continuation).** *(Effort: M–L)* Teach
   `_shunting_yard` to accept `-` in number position as negation (emit a unary-neg RPN op or fold the
   sign into the next literal, highest precedence, right-associative); give the controller a
   negative-literal path for `-` at expression start and after `(`; and wrap a negative result in
   parentheses when continuing (feed `(-3)+2`). **This one change fixes defects #1, #2 and #3** and turns
   `−5=`→`-5`, `(3)×−2=`→`-6`, `2−5=` then `+2=`→`-1`.
2. **No silent wrong answers.** *(Effort: S)* Until (1) lands, the operator-replace rule that turns
   `× −` into subtraction must return `Error`, never a plausible number. Add a regression test asserting
   *no* keystroke sequence yields a numerically wrong non-`Error` result.
3. **Add the negative-number test matrix and remove the two lock-in tests.** *(Effort: M)* Convert the
   suite's worst blind spot into a regression anchor.
4. **Add a finalize clean-tree gate (framework).** *(Effort: S)* `git status --porcelain` must be empty
   before a run declares success; commit + push the sweep. Prevents the dirty-tree finish this run had.

### P1 — quality & fidelity

5. **Rewrite `_format_result`** to format by significant digits and normalize negative zero — fixes `-0`
   (#5) and large-number noise (#6). Replace `test_engine.py:327-333`. *(Effort: M)*
6. **Add executed GUI wiring tests** with a patched Tk root: assert every keysym binds and every
   callback routes to `_on_press` with the correct key; add one skip-if-no-display live smoke test.
   Closes defect #4. *(Effort: M)*
7. **Fix the minus glyph** (#7): map `-`→U+2212 in `_to_display` (keeping the internal ASCII expression),
   so the display matches the button and the README. *(Effort: S)*
8. **Remove swarm-internal docs from the deliverable** (`DIRECTIVE.md`, `CHECKUP.md`, `CONTEXT.md`,
   `docs/lessons/*`) — they document the agent machinery, not the calculator. *(Effort: S)*

### P2 — parity & polish

9. **Add a `+/-` negate control** (button + key), backed by the P0 engine work. *(Effort: M)*
10. **Windows-Calc parity:** repeat-last-operation on repeated `=`; bind the `=` key; initialize the
    display to `0`; add `%`. *(Effort: S–M)*
11. **Distinguish overflow / non-finite** from malformed input (#8) — a clearer signal than a shared
    `Error`. *(Effort: S)*
12. **Consider `Decimal`** (or a precision cap + thousands separators) to remove float artifacts. Add
    `pytest-cov` with a branch-coverage gate on engine + controller. *(Effort: M)*

---

## 8. Notes for the agentswarm framework

These are process observations from this run, useful for improving the *builder*, not the calculator:

- **No post-run evaluation artifact.** The framework produces internal working memory
  (`docs/lessons/*`, `CHECKUP.md`) but no evaluation of the delivered product. This report fills that
  gap manually; a built-in "evaluate the deliverable" step at finalize would make each run self-scoring.
- **Finalize ran over a dirty tree.** The final molt deleted a file but the deletion was never
  committed/pushed (see §2, defect in §4-arch). A clean-tree assertion + commit/push of the sweep would
  fix this (roadmap P0-4).
- **The green suite hid the headline defect.** 365 passing tests coexisted with a broken, silently-wrong
  core feature *and* two tests that encode the bug as correct. The framework's audit/molt gates trusted
  the count; they could add an adversarial "can any input produce a wrong number, not just a crash?"
  check, and flag tests that assert an operator is *ignored* as suspicious.

---

## Appendix — reproductions

Run from the repo root with the project interpreter (all outputs observed on commit `4742442`):

```python
from calc.engine import evaluate
from calc.controller import CalculatorController
def seq(keys):
    c = CalculatorController()
    for k in keys: c.press(k)
    return c.display

evaluate('-5')                      # -> 'Error'   (want -5)      defect #1
evaluate('3*-2')                    # -> 'Error'                  defect #1
seq(['-','5','='])                  # -> '5'       (want -5)      defect #2
seq(['(','3',')','*','-','2','='])  # -> '1'       (want -6)      defect #2
seq(['2','*','(','-','3',')','='])  # -> '6'       (want -6)      defect #2
seq(['-','3','+','5','='])          # -> '8'       (want 2)       defect #2
seq(['2','-','5','='])              # -> '-3'      (correct)
seq(['2','-','5','=','+','2','='])  # -> 'Error'   (want -1)      defect #3
evaluate('0.3-0.1-0.2')             # -> '-0'                     defect #5
evaluate('123456789.123*1')         # -> '123456789.122999995946884'  defect #6
evaluate('1'+'0'*308+'*10')         # -> 'Error'   (overflow)    defect #8
seq(['2','+','3','=','='])          # -> '5'       (Windows: 8)   parity gap
```
