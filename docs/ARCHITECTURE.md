# Architecture

## Goal

A desktop calculator app in Python with a Tkinter GUI, in the style of the Windows Calculator. Pure stdlib, runs on Windows. Mouse + keyboard input, correct operator precedence, decimals, parentheses. Division by zero / malformed input → "Error" display, no crashes.

## Design decisions (options considered and why)

### 1. Arithmetic engine: Shunting-yard algorithm

**Chosen**: Shunting-yard (tokenize → RPN → evaluate).

**Alternatives considered**:
- `eval()`: dangerous, not a real engine, trivial to break, doesn't teach anything.
- Recursive descent parser: more code for the same result; shunting-yard is the classic calculator algorithm, well-understood and easy to debug step-by-step.

**Why shunting-yard**: It cleanly separates tokenization, precedence handling (via a precedence table), and evaluation. Each phase is independently testable. No recursion depth issues for practical expressions.

### 2. Expression representation: ASCII internally, Unicode for display

**Internal** (engine + controller): `+`, `-`, `*`, `/` — standard ASCII operators.

**Display**: `×` (U+00D7) for multiply, `÷` (U+00F7) for divide. The controller translates between the two representations. Keyboard input maps `*` → multiply, `/` → divide.

### 3. Controller state machine

States are implicit (flag-driven, not a formal FSM):

- `expression` (str): the current expression in ASCII form.
- `display` (str): what the user sees — expression with Unicode operators, or the result after `=`, or "Error".
- `result_shown` (bool): after `=` is pressed. Next digit starts fresh; next operator continues from the result.

**Why flag-driven**: With only ~8 actions and 1 flag, a formal state machine is overkill. The flag + rules cover all transitions cleanly.

### 4. Error handling: string sentinel, never exceptions

The engine returns `"Error"` (a string) for any problem. The controller treats `"Error"` as displayable state. The user can always press `C` to clear or any other key to attempt recovery. No exception ever propagates from engine or controller.

### 5. Package layout

```
calc/
    __init__.py       # empty (package marker)
    __main__.py       # python -m calc entry point
    engine.py         # evaluate(expression: str) -> str
    controller.py     # CalculatorController class (headless)
    view.py           # CalculatorView class (Tkinter)
tests/
    __init__.py
    test_engine.py
    test_controller.py
    test_view.py
    test_view_takefocus.py
    test_view_wiring.py
    test_package_wiring.py
pyproject.toml        # calc script entry point + dev deps
```

### 6. Tkinter as the GUI toolkit

**Chosen**: Tkinter (Python stdlib). No extra dependencies.

**Window**: Fixed size (non-resizable), title "Calculator", gray background (#f0f0f0).

**Layout** (Windows Calculator-inspired):

```
[              Display (Label, right-aligned, Segoe UI 24pt)            ]
[  (  ]  [  )  ]  [  C  ]  [  ⌫  ]
[  7  ]  [  8  ]  [  9  ]  [  ÷  ]
[  4  ]  [  5  ]  [  6  ]  [  ×  ]
[  1  ]  [  2  ]  [  3  ]  [  −  ]
[  .  ]  [  0  ]  [  =  ]  [  +  ]
```

Button colors:
- Digits / operators / parens / decimal: light gray (#e0e0e0)
- Clear (C): red (#ff6b6b)
- Equals (=): blue (#4dabf7)

### 7. Keyboard mapping

| Key | Action |
|-----|--------|
| `0`–`9` | digit |
| `.` | decimal point |
| `+` | add |
| `-` | subtract |
| `*` | multiply |
| `/` | divide |
| `(` | left parenthesis |
| `)` | right parenthesis |
| Enter / Return | equals (`=`) |
| KP_Enter | equals (`=`) |
| Backspace | backspace (`⌫`) |
| Escape / Delete | clear (`C`) |
| KP_0–KP_9 | digits |
| KP_Decimal | `.` |
| KP_Add | `+` |
| KP_Subtract | `-` |
| KP_Multiply | `*` |
| KP_Divide | `/` |

### 8. Engine API contract

```python
def evaluate(expression: str) -> str:
    """
    Evaluate an arithmetic expression string.

    The expression uses ASCII operators: +, -, *, /.
    Supports parentheses and decimal numbers.

    Returns:
        str: The result as a string (e.g. "14", "3.5", "0"), or "Error".

    Never raises. All error conditions (division by zero, malformed
    syntax, mismatched parentheses) return the string "Error".
    """
```

### 9. Controller API contract

```python
class CalculatorController:
    display: str          # read-only, what the view should show
    expression: str       # read-only, internal ASCII expression (for debugging)

    def press(self, key: str) -> None:
        """
        Process a key/button press.

        key is one of:
          "0"–"9", ".", "+", "-", "*", "/", "(", ")",
          "=", "C", "backspace"
        """
```

### 10. View API contract

```python
class CalculatorView:
    def __init__(self, controller: CalculatorController):
        """Build the Tkinter window, wire widgets to controller."""

    def refresh(self) -> None:
        """Read controller.display and update the display widget."""

    def run(self) -> None:
        """Start the Tkinter main loop."""
```

### 11. Operator precedence table

| Operator | Precedence | Associativity |
|----------|-----------|---------------|
| `+`, `-` | 1 | left |
| `*`, `/` | 2 | left |

Parentheses override precedence as usual.

### 12. What we do NOT support (out of scope)

- Unary minus / negation (e.g., `-5` as input)
- Scientific functions (sin, cos, sqrt, etc.)
- Percentage, memory keys
- History
- Keyboard shortcuts beyond those listed
- Copy/paste
- Theming / dark mode

## Data flow

```
User input (mouse click or keypress)
        │
        ▼
   view.py  ───press(key)───►  controller.py
                                   │
                              (manages state)
                                   │
                          ┌────────┼────────┐
                          │        │        │
                     expression  display  (updates)
                          │        │
                          ▼        │
                     engine.py     │
                     evaluate()    │
                          │        │
                          ▼        ▼
                     "14" or "Error"
```

1. View captures input → calls `controller.press(key)`.
2. Controller updates internal `expression` and `display`.
3. For `=`: controller calls `engine.evaluate(expression)` → sets `display` to result or "Error".
4. View calls `refresh()` → reads `controller.display` → updates the Tkinter Label/Entry.

## Current implementation status

**Pass 1 (STUBS) — COMPLETE. 166 tests green.** ✅

**Pass 2 (REAL) — in progress. 259 tests green.**

| Module | Stub | Real |
|--------|------|------|
| `calc/engine.py` | ✅ `evaluate()` with canned results (`"1+1"` → `"2"`, `"2*3"` → `"6"`, `"1/0"` → `"Error"`, else `"STUB"`). Never raises. | ✅ Full shunting-yard pipeline: `_tokenize()` → `_shunting_yard()` → `_eval_rpn()` → `_format_result()`. Correct precedence (`*/`=2, `+-`=1, left-assoc), parentheses, decimals (including `.5` leading-dot), whitespace tolerance. `_format_result()` guards against empty-string edge case. Division by zero / malformed / empty / non-str input → `"Error"`. Never raises. **111 engine tests green.** |
| `calc/controller.py` | ✅ `CalculatorController` with echo-mode `press()`: digits/operators/decimal/parens echo to display (`*`→`×`, `/`→`÷`); `=` shows `"STUB"`; `C` clears both; `backspace` removes last char. ASCII internally, Unicode for display. Properties `expression`/`display` are read-only. | — |
| `calc/view.py` | ✅ `CalculatorView` with full button grid (5×4, 20 buttons), right-aligned display (Segoe UI 24pt), mouse + keyboard bindings (standard + numpad), wired to controller via `press(key)` + `refresh()`. All buttons have `takefocus=False`. | — |
| `calc/__main__.py` + `pyproject.toml` | ✅ Package wired. `python -m calc` and `calc` command both launch. Entry point `main()` in `__main__.py` wires controller+view. `pyproject.toml` uses `setuptools.build_meta`. README exists. | — |
| Tests (6 files) | ✅ 166 tests green across `test_engine.py`, `test_controller.py`, `test_view.py`, `test_view_takefocus.py`, `test_view_wiring.py`, `test_package_wiring.py`. No test imports `tkinter` directly or creates a live display. | ✅ Engine tests are comprehensive (111 tests via `test_engine.py`): precedence, parentheses, decimals, division by zero, malformed input, whitespace, formatting, edge cases, never-raises contract, non-str input. Controller tests still reflect stub behavior (needs expansion for M2-real). |

**Next: M2-real — controller state machine (digit append, operator replace, decimal guard, result continuation, error recovery, `=` delegates to real engine).**
