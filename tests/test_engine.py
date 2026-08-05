"""Tests for calc.engine — M1 stub."""

import pytest
from calc.engine import evaluate


# ---------------------------------------------------------------------------
# Import / module smoke test (M5-stub: one trivial import test per module)
# ---------------------------------------------------------------------------

def test_engine_importable():
    """The engine module is importable and exposes evaluate()."""
    from calc import engine
    assert hasattr(engine, "evaluate")
    assert callable(engine.evaluate)


# ---------------------------------------------------------------------------
# Canned results (M1-stub contract)
# ---------------------------------------------------------------------------

def test_canned_1_plus_1():
    assert evaluate("1+1") == "2"


def test_canned_2_times_3():
    assert evaluate("2*3") == "6"


def test_canned_division_by_zero():
    assert evaluate("1/0") == "Error"


# ---------------------------------------------------------------------------
# Fallback / unknown expressions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr", [
    "2+2",
    "10-5",
    "3.14*2",
    "(1+2)*3",
    "42",
    "",
    "  1+1  ",
    "1++1",
    "abc",
    "1/(2-2)",
    ")(",
    "1..2",
    "1+",
    "*5",
])
def test_unknown_returns_stub(expr):
    """Any expression not in the canned map returns 'STUB'."""
    assert evaluate(expr) == "STUB"


# ---------------------------------------------------------------------------
# Type contract
# ---------------------------------------------------------------------------

def test_return_type_is_str():
    """evaluate() always returns a str, never None, int, float, etc."""
    result = evaluate("1+1")
    assert isinstance(result, str)
    assert result is not None

    result = evaluate("1/0")
    assert isinstance(result, str)

    result = evaluate("garbage")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Never raises
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr", [
    "",
    " ",
    "\x00",
    "1+1",
    "1/0",
    "(" * 1000,
    "\n\t",
    "2**3",
    "1 + 2",
    "one + two",
])
def test_never_raises(expr):
    """evaluate() must never raise an exception — the contract says so."""
    try:
        result = evaluate(expr)
    except Exception as exc:
        pytest.fail(f"evaluate({expr!r}) raised {type(exc).__name__}: {exc}")
    assert isinstance(result, str)
