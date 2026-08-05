# Failures

_Regressions: what broke, the proven root cause, and the fix._

- **`pyproject.toml` used private setuptools build-backend path** (M4-stub): The `build-backend` was set to `setuptools.backends._legacy:_Backend` — a private, internal path (note `_legacy` and `_Backend` both have `_` prefixes signalling internal API). This would cause `pip install` to fail on setuptools versions where that path doesn't exist or changed. Root cause: copying from an outdated/undocumented example. Fix: use the documented public value `setuptools.build_meta`. Guarded with two tests that assert the exact public value and assert the private path is absent from the raw file.
- **`_format_result` returned empty string for extremely small floats** (M1-real): When a float is so tiny (e.g. `~1e-20`) that `:.15f` formats to `"0.000000000000000"`, chaining `rstrip("0").rstrip(".")` yields `""` instead of `"0"`. Root cause: the rstrip chain discards every character when the formatted string is all zeros, leaving nothing. Fix: add `if not s: s = "0"` after the rstrip chain (`calc/engine.py:208-209`). Tested with values down to `5e-324`.
