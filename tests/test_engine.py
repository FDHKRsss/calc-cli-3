"""Tests for calc.engine — M1 real (shunting-yard)."""

import pytest
from calc.engine import evaluate


# ---------------------------------------------------------------------------
# Import / module smoke test
# ---------------------------------------------------------------------------

def test_engine_importable():
    """The engine module is importable and exposes evaluate()."""
    from calc import engine
    assert hasattr(engine, "evaluate")
    assert callable(engine.evaluate)


# ---------------------------------------------------------------------------
# Basic arithmetic (regression from stub era + expansions)
# ---------------------------------------------------------------------------

def test_canned_1_plus_1():
    assert evaluate("1+1") == "2"


def test_canned_2_times_3():
    assert evaluate("2*3") == "6"


@pytest.mark.parametrize("expr, expected", [
    ("10-5", "5"),
    ("8/2", "4"),
    ("42", "42"),
    ("0", "0"),
    ("999+1", "1000"),
])
def test_basic_operations(expr, expected):
    """Single-operation expressions compute correctly."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Operator precedence (M5-real requirement)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("2+3*4", "14"),      # * before +
    ("2*3+4", "10"),      # * before +
    ("10-6/2", "7"),      # / before -
    ("10/2-3", "2"),      # / before -
    ("2+3+4", "9"),       # left-associative +
    ("10-5-2", "3"),      # left-associative -
    ("8/2/2", "2"),       # left-associative /  → (8/2)/2 = 2
    ("2*3*4", "24"),      # left-associative *
    ("2+3-4+1", "2"),     # mixed + and -
    ("8/2*4", "16"),      # mixed * and /, left-assoc: (8/2)*4 = 16
    ("12/2/3", "2"),      # left-assoc: (12/2)/3 = 2
])
def test_precedence(expr, expected):
    """Operators respect precedence and left-associativity."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Parentheses (M5-real requirement)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("(2+3)*4", "20"),
    ("2*(3+4)", "14"),
    ("((1+2)*3)", "9"),
    ("(1+2)*(3+4)", "21"),
    ("((((1+2))))", "3"),
    ("(2+3)*(10-5)", "25"),
    ("10-(2+3)", "5"),
    ("(8/2)*3", "12"),
    ("8/(2*2)", "2"),
    ("((1))", "1"),
])
def test_parentheses(expr, expected):
    """Parentheses override default precedence."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Decimals (M5-real requirement)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("3.14*2", "6.28"),
    (".5+.5", "1"),
    (".5*2", "1"),
    ("0.25+0.25", "0.5"),
    ("1.5+2.5", "4"),
    ("5.0+5.0", "10"),
    ("0.1*10", "1"),
    ("2.5*4", "10"),
    ("9.9+0.1", "10"),
    ("0.001+0.002", "0.003"),
])
def test_decimals(expr, expected):
    """Decimal numbers (including leading-dot style) compute correctly."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Whitespace handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("  1+1  ", "2"),
    ("1 + 2", "3"),
    (" ( 1 + 2 ) * 3 ", "9"),
    ("1+  2  *3", "7"),
    ("\t1+2\n", "3"),
])
def test_whitespace(expr, expected):
    """Whitespace is silently ignored."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Division by zero (M5-real requirement)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr", [
    "1/0",
    "5/(2-2)",
    "0/0",
    "1/(1-1)",
    "100/(4-4)",
    "0.5/0",
    "1/(0)",
])
def test_division_by_zero(expr):
    """Division by zero returns 'Error', never raises."""
    assert evaluate(expr) == "Error"


# ---------------------------------------------------------------------------
# Malformed input (M5-real requirement)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr", [
    # Empty / whitespace-only
    "",
    "   ",
    "\n\t",
    # Trailing operator
    "1+",
    "2*",
    "3/",
    "5-",
    # Leading operator
    "*5",
    "/2",
    "+1",
    # Consecutive operators
    "1++1",
    "2**3",
    "1//2",
    "1+-2",
    # Mismatched parentheses
    "(1+2",
    "1+2)",
    ")(",
    "((1+2)",
    "(1+2))",
    # Empty parentheses
    "()",
    "( )",
    # Multiple decimal points in one number
    "1..2",
    "1.2.3",
    # Invalid characters
    "abc",
    "1+abc",
    "x+y",
    "#@!",
    "2+three",
    # Implicit multiplication not supported
    "2(3)",
    "(3)4",
    "2(3+4)",
    # Isolated decimal point
    "5 . 5",
    ". + 2",
])
def test_malformed_input(expr):
    """Malformed expressions return 'Error', never raise."""
    assert evaluate(expr) == "Error"


# ---------------------------------------------------------------------------
# Negative results (via subtraction)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("3-8", "-5"),
    ("0-1", "-1"),
    ("5-10", "-5"),
    ("2.5-10", "-7.5"),
    ("(2-5)*3", "-9"),
])
def test_negative_results(expr, expected):
    """Subtraction can produce negative results."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("4/2", "2"),             # whole number — no ".0"
    ("5/2", "2.5"),
    ("1/4", "0.25"),
    ("1/3", "0.333333333333333"),  # 15 significant digits, no trailing zeros
    ("10/3", "3.333333333333333"),
    ("0.0+0.0", "0"),         # zero is "0" not "0.0"
    ("0.1+0.2", "0.3"),       # formatted cleanly
])
def test_formatting(expr, expected):
    """Results are formatted without unnecessary .0 or scientific notation."""
    assert evaluate(expr) == expected


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_very_large_expression():
    """Long, deeply nested expressions don't crash."""
    # 200 nested parens around a simple addition
    expr = "(" * 200 + "1+1" + ")" * 200
    assert evaluate(expr) == "2"


def test_very_long_number():
    """Very long number literals are handled."""
    result = evaluate("12345678901234567890")
    assert isinstance(result, str)
    assert result != "Error"


def test_trailing_dot_on_number():
    """A trailing dot on a number (e.g., '5.') is tolerated."""
    assert evaluate("5.") == "5"
    assert evaluate("5.+3") == "8"


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

    result = evaluate("")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Never raises — handle any input (including non-str)
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


def test_non_string_input_returns_error():
    """Non-string inputs are caught by the outer try/except and return 'Error'."""
    assert evaluate(None) == "Error"   # type: ignore[arg-type]
    assert evaluate(42) == "Error"     # type: ignore[arg-type]
    assert evaluate(3.14) == "Error"   # type: ignore[arg-type]


# ===================================================================
# _format_result — tiny-float guard (M1-real fix: two-line guard)
# ===================================================================
# When a float is so tiny that "{:.15f}" renders as "0.000000000000000",
# the rstrip("0").rstrip(".") chain could (in theory on some Python
# implementations) produce an empty string.  The guard ``if not s: s = "0"``
# at calc/engine.py:208-209 prevents that.
#
# The tests below validate the current behavior on CPython (where the
# guard is purely defensive) AND assert that _format_result never returns
# an empty string or scientific notation for any float value.


def test_format_result_tiny_positive_is_zero():
    """Extremely small positive floats format as '0', never empty string."""
    from calc.engine import _format_result
    assert _format_result(1e-20) == "0"
    assert _format_result(1e-32) == "0"
    assert _format_result(1e-100) == "0"
    assert _format_result(5e-324) == "0"  # smallest positive subnormal
    assert _format_result(0.0) == "0"


def test_format_result_tiny_negative_is_minus_zero():
    """Extremely small negative floats format as '-0', never empty string."""
    from calc.engine import _format_result
    assert _format_result(-1e-20) == "-0"
    assert _format_result(-1e-32) == "-0"
    assert _format_result(-1e-100) == "-0"
    assert _format_result(-5e-324) == "-0"  # negative smallest subnormal


def test_format_result_never_empty():
    """_format_result must never return an empty string — the guard ensures this."""
    from calc.engine import _format_result
    import sys
    import math

    # A representative set of tricky float values
    edge_values = [
        0.0, -0.0,
        1.0, -1.0,
        0.5, -0.5,
        1e-20, -1e-20,
        1e-100, -1e-100,
        1e-200, -1e-200,
        1e-308, -1e-308,
        sys.float_info.min, -sys.float_info.min,
        sys.float_info.epsilon, -sys.float_info.epsilon,
        math.pi, -math.pi,
        1.0 / 3.0, -1.0 / 3.0,
        1e15, -1e15,
        1e-15, -1e-15,
    ]
    for v in edge_values:
        result = _format_result(v)
        assert isinstance(result, str), (
            f"_format_result({v!r}) returned non-str: {result!r}"
        )
        assert result != "", (
            f"_format_result({v!r}) returned empty string"
        )
        # Result must not contain scientific notation ('e' or 'E')
        assert "e" not in result.lower(), (
            f"_format_result({v!r}) = {result!r} contains scientific notation"
        )


def test_format_result_negative_zero_int_path():
    """-0.0 hits the int-equality branch and produces '0' (not '-0')."""
    from calc.engine import _format_result
    assert _format_result(-0.0) == "0"


# ---------------------------------------------------------------------------
# Integration: expressions producing near-zero results
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, expected", [
    # Product of two very small numbers → underflows to 0
    ("0.0000000000000001*0.0000000000000001", "0"),
    # Chain of tiny operations
    ("0.0000000000000001*0.0000000000000001*1000", "0"),
    # Subtraction that cancels to exactly zero
    ("0.0000000000000001-0.0000000000000001", "0"),
    ("1.5-1.5", "0"),
    # Very small result from division
    ("0.0000000000000001/1000000000000000", "0"),
    # (1-1) exactly zero
    ("(1-1)", "0"),
    ("(1-1)*999", "0"),
])
def test_near_zero_results(expr, expected):
    """Expressions producing extremely tiny or zero results format correctly."""
    assert evaluate(expr) == expected
