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
- [x] M1 -- real: Full shunting-yard implementation with tokenizer, precedence handling, RPN evaluation, all error cases.

### M2: Controller module — headless state machine (`calc/controller.py`)

`CalculatorController` class with `press(key)` method. Manages `expression`, `display`, `result_shown` flag. Delegates `=` to engine.

- [x] M2 -- stub: `press()` echoes key to display, `=` shows `"STUB"`, clear/backspace work trivially.
- [x] M2 -- real: Full state machine with all behaviors (digit append, operator replace, decimal guard, result continuation, error recovery). ✅ 89 controller tests green.

### M3: View module — Tkinter GUI (`calc/view.py`)

`CalculatorView` class. Creates window, display, button grid. Wires mouse clicks and keyboard to controller. `refresh()` updates display.

- [x] M3 -- stub: Full button layout and keyboard bindings, wired to (stub) controller. Display updates work.
- [x] M3 -- real: Polish — display Segoe UI 24pt, right-aligned, white bg, sunken relief. Buttons Segoe UI 14pt, `takefocus=False`, color-coded (C=#ff6b6b, ==#4dabf7, standard=#e0e0e0). Window title "Calculator", non-resizable, #f0f0f0 bg. `focus_set()` in `__init__` for immediate keyboard input. Complete keyboard bindings (standard + numpad). Docstring cleaned up — no "(stub)" traces. ✅ 21 polish tests green.

### M4: Package wiring — entry points, pyproject.toml, README

`python -m calc` and `calc` command both launch the app. README describes how to launch and what the window looks like.

- [x] M4 -- stub: `__main__.py` imports and launches the view. `pyproject.toml` with `[project.scripts]` entry. App runs end-to-end (with stubs). README exists with launch instructions and window description.
- [x] M4 -- real: Both entry points wired (`python -m calc` and `calc`). `pyproject.toml` uses `setuptools.build_meta`, has `[project.optional-dependencies]` dev extras. README polished: `# calc` title, Usage / Keyboard shortcuts / Window appearance (accurate ASCII art, font sizes, colors) / Running the tests sections. ✅ All package-wiring tests green.

### M5: Test suite (`tests/`)

pytest suite covering engine and controller. No test requires a live display.

- [x] M5 -- stub: One trivial import test per module (engine, controller).
- [x] M5 -- real (engine part): 111 engine tests — precedence, parentheses, decimals, division by zero, malformed input, formatting, edge cases.
- [x] M5 -- real (controller part): 89 controller tests — digit building, operator sequences, clear/backspace, equals with valid/invalid expressions, error recovery, decimal guard, result continuation.
- [x] M5 -- real (view/polish part): 21 view polish tests (AST-based, no live display).
- [x] M5 -- real (package wiring part): Package wiring tests — pyproject.toml, __main__, README accuracy, dev extras.

---

## Pass execution order

**Pass 1 (STUBS)**: M1-stub → M2-stub → M3-stub → M4-stub → M5-stub. ✅ **COMPLETE — 166 tests green.**

**Pass 2 (REAL)**: M1-real → M2-real → M3-real → M4-real. ✅ **COMPLETE — 365 tests green.**

**All milestones delivered.** 🎉

## Human notes

_None yet._
