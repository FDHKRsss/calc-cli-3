# Patterns

_Reusable techniques that worked, so they are reused not rediscovered._

- **Testing "never raises" functions**: wrap the call in `try/except Exception` and use `pytest.fail(f"…raised {type(exc).__name__}: {exc}")` inside the except block. This gives a clear failure message with the exception type and message rather than letting pytest catch an unexpected exception generically.
- **Testing Tkinter views without a live display**: export layout data (button grid, keyboard maps) as module-level constants (`BUTTONS`, `KEYBOARD_MAP`, `NUMPAD_MAP`) and test those directly — structure, completeness, Unicode labels. Use `inspect` to verify class method signatures (parameter names, counts) without instantiating. Never call `Tk()` or `mainloop()` in tests; validate the test file's own AST to confirm no direct `tkinter` import.
- **Guarding rstrip chains in number formatting**: When using `f"{value:.Nf}".rstrip("0").rstrip(".")` to format floats, always guard against the empty-string edge case: if the value is so small that all N decimal digits format as zero, the rstrip chain removes every character, leaving `""`. The fix is a one-liner: `if not s: s = "0"`.
