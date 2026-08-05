# Project context (durable directives all agents must always honor)

_Seeded from the goal; the architect refines this to the essence -- keep it short._

A desktop calculator app in Python with a graphical UI, in the style of the Windows Calculator: a result display and a grid of clickable buttons (digits 0-9, decimal point, + − × ÷, parentheses, C to clear, ⌫ backspace, =). Built with Tkinter from the Python standard library (no extra dependencies), runs on Windows. Supports both mouse clicks and keyboard input, correct operator precedence, decimals and parentheses. Division by zero or malformed input shows a friendly "Error" in the display and lets the user keep typing — never a crash or a stack trace.
Architecture (important): put ALL arithmetic in a pure, GUI-free `engine` module, and a headless `controller` that turns button/key presses into display state. The Tkinter layer is a thin view that only wires widgets to the controller, so the logic is fully unit-testable without a display.
Ship a `calc` entry point that opens the window (`python -m calc` or `calc`), a pytest suite covering the engine and controller (precedence, parentheses, decimals, division by zero, clear/backspace, malformed input) — no test may require a live display — and a short README with how to launch it and what the window looks like.

**Established (do not regress):**
- `calc/engine.py`: `evaluate(expression: str) -> str` — ASCII operators only, never raises, returns `"Error"` for any problem.
- Tests: `tests/test_engine.py` (engine), `tests/test_controller.py` (controller). No test may import `tkinter` or create a live display.
- Full API contracts are in `docs/ARCHITECTURE.md`.
