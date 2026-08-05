# Patterns

_Reusable techniques that worked, so they are reused not rediscovered._

- **Testing "never raises" functions**: wrap the call in `try/except Exception` and use `pytest.fail(f"…raised {type(exc).__name__}: {exc}")` inside the except block. This gives a clear failure message with the exception type and message rather than letting pytest catch an unexpected exception generically.
