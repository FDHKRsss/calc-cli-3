# Project context (durable directives all agents must always honor)

_Seeded from the goal; the architect refines this to the essence -- keep it short._

A desktop calculator app in Python with a graphical UI, in the style of the Windows Calculator: a result display and a grid of clickable buttons (digits 0-9, decimal point, + − × ÷, parentheses, C to clear, ⌫ backspace, =). Built with Tkinter from the Python standard library (no extra dependencies), runs on Windows. Supports both mouse clicks and keyboard input, correct operator precedence, decimals and parentheses. Division by zero or malformed input shows a friendly "Error" in the display and lets the user keep typing — never a crash or a stack trace.
Architecture (important): put ALL arithmetic in a pure, GUI-free `engine` module, and a headless `controller` that turns button/key presses into display state. The Tkinter layer is a thin view that only wires widgets to the controller, so the logic is fully unit-testable without a display.
Ship a `calc` entry point that opens the window (`python -m calc` or `calc`), a pytest suite covering the engine and controller (precedence, parentheses, decimals, division by zero, clear/backspace, malformed input) — no test may require a live display — and a short README with how to launch it and what the window looks like.

**Established (do not regress):**
- `calc/engine.py` (M1-stub): `evaluate(expression: str) -> str` — ASCII operators only, never raises, returns `"Error"` for any problem. Currently canned results.
- `calc/controller.py` (M2-stub): `CalculatorController` with `expression`/`display` read-only str and `press(key)`. Echo mode: keys appear in display (`*`→`×`, `/`→`÷`); `=` → `"STUB"`; `C` clears both; `backspace` removes last char. ASCII internally, Unicode for display.
- `calc/view.py` (M3-stub): `CalculatorView` with full button grid (5×4, 20 buttons), right-aligned display (Segoe UI 24pt), mouse + keyboard bindings (standard + numpad), wired to controller via `press(key)` + `refresh()`. All buttons have `takefocus=False`.
- `calc/__main__.py` + `pyproject.toml` (M4-stub): Package wired. `python -m calc` and `calc` command both launch. Entry point `main()` in `__main__.py` wires controller+view. **pyproject.toml build-backend must be the documented public value `setuptools.build_meta`** — never use a private/internal path like `setuptools.backends._legacy:_Backend` (the `_` prefixes signal internal API). Tests guard this.
- Tests (6 files): `tests/test_engine.py`, `tests/test_controller.py`, `tests/test_view.py`, `tests/test_view_takefocus.py`, `tests/test_view_wiring.py`, `tests/test_package_wiring.py`. No test may import `tkinter` directly or create a live display.
- **Pass 1 (STUBS) complete** — 166 tests pass. Next: Pass 2 (REAL) starting with M1-real (shunting-yard engine).
- Full API contracts are in `docs/ARCHITECTURE.md`.
