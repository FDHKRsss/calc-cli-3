# Failures

_Regressions: what broke, the proven root cause, and the fix._

- **`pyproject.toml` used private setuptools build-backend path** (M4-stub): The `build-backend` was set to `setuptools.backends._legacy:_Backend` — a private, internal path (note `_legacy` and `_Backend` both have `_` prefixes signalling internal API). This would cause `pip install` to fail on setuptools versions where that path doesn't exist or changed. Root cause: copying from an outdated/undocumented example. Fix: use the documented public value `setuptools.build_meta`. Guarded with two tests that assert the exact public value and assert the private path is absent from the raw file.
