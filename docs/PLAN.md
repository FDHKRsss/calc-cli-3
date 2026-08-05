# Plan

## Goal(s)

A desktop calculator app in Python with a graphical UI, in the style of the Windows Calculator: a result display and a grid of clickable buttons (digits 0-9, decimal point, + − × ÷, parentheses, C to clear, ⌫ backspace, =). Built with Tkinter from the Python standard library (no extra dependencies), runs on Windows. Supports both mouse clicks and keyboard input, correct operator precedence, decimals and parentheses. Division by zero or malformed input shows a friendly "Error" in the display and lets the user keep typing — never a crash or a stack trace.

Architecture: put ALL arithmetic in a pure, GUI-free `engine` module, and a headless `controller` that turns button/key presses into display state. The Tkinter layer is a thin view that only wires widgets to the controller, so the logic is fully unit-testable without a display.

Ship a `calc` entry point that opens the window (`python -m calc` or `calc`), a pytest suite covering the engine and controller (precedence, parentheses, decimals, division by zero, clear/backspace, malformed input) — no test may require a live display — and a short README with how to launch it and what the window looks like.

---

## Milestones

### M1: Engine module — pure arithmetic (`calc/engine.py`)

The `evaluate(expression: str) -> str` function. Shunting-yard algorithm: tokenize → RPN → evaluate. Returns result string or `"Error"`. Never raises.

- [x] M1 -- stub: `evaluate()` returns canned results based on trivial input matching.
- [ ] M1 -- real: Full shunting-yard implementation with tokenizer, precedence handling, RPN evaluation, all error cases.

### M2: Controller module — headless state machine (`calc/controller.py`)

`CalculatorController` class with `press(key)` method. Manages `expression`, `display`, `result_shown` flag. Delegates `=` to engine.

- [ ] M2 -- stub: `press()` echoes key to display, `=` shows `"STUB"`, clear/backspace work trivially.
- [ ] M2 -- real: Full state machine with all behaviors (digit append, operator replace, decimal guard, result continuation, error recovery).

### M3: View module — Tkinter GUI (`calc/view.py`)

`CalculatorView` class. Creates window, display, button grid. Wires mouse clicks and keyboard to controller. `refresh()` updates display.

- [ ] M3 -- stub: Full button layout and keyboard bindings, wired to (stub) controller. Display updates work.
- [ ] M3 -- real: Polish — ensure display font/size matches Windows Calculator style, window title, focus handling so keyboard works immediately.

### M4: Package wiring — entry points, pyproject.toml, README

`python -m calc` and `calc` command both launch the app. README describes how to launch and what the window looks like.

- [ ] M4 -- stub: `__main__.py` imports and launches the view. `pyproject.toml` with `[project.scripts]` entry. App runs end-to-end (with stubs). README exists with launch instructions and window description.
- [ ] M4 -- real: Verify both entry points work. Finalize `pyproject.toml` metadata. Polish README to match the delivered window appearance.

### M5: Test suite (`tests/`)

pytest suite covering engine and controller. No test requires a live display.

- [ ] M5 -- stub: One trivial import test per module (engine, controller). (Note: engine import test already exists in `tests/test_engine.py`, written alongside M1-stub. Remaining: controller import test — blocked until M2-stub creates `calc/controller.py`.)
- [ ] M5 -- real: Comprehensive tests — engine: precedence, parentheses, decimals, division by zero, malformed input (mismatched parens, empty, trailing operator, multiple decimals). controller: digit building, operator sequences, clear/backspace, equals with valid/invalid expressions, error recovery, decimal guard, result continuation.

---

## Pass execution order

**Pass 1 (STUBS)**: M1-stub → M2-stub → M3-stub → M4-stub → M5-stub. End result: app launches, window appears with full button layout, buttons echo to display, `=` shows "STUB". Tests pass trivially.

**Pass 2 (REAL)**: M1-real → M2-real → M3-real → M4-real → M5-real. End result: fully functional calculator with correct arithmetic.

## Human notes

_None yet._
