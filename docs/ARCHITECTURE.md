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
pyproject.toml        # calc script entry point + dev deps
```

### 6. Tkinter as the GUI toolkit

**Chosen**: Tkinter (Python stdlib). No extra dependencies.

**Window**: Fixed size (~320×400), title "Calculator", non-resizable (or minimally resizable with grid weight).

**Layout** (Windows Calculator-inspired):

```
[              Display (Entry, read-only, right-aligned)            ]
[  (  ]  [  )  ]  [  C  ]  [  ⌫  ]
[  7  ]  [  8  ]  [  9  ]  [  ÷  ]
[  4  ]  [  5  ]  [  6  ]  [  ×  ]
[  1  ]  [  2  ]  [  3  ]  [  −  ]
[  .  ]  [  0  ]  [  =  ]  [  +  ]
```

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
| Backspace | backspace (`⌫`) |
| Escape / Delete | clear (`C`) |

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
