"""Tests for calc.controller — M2 stub."""

import pytest
from calc.controller import CalculatorController


# ---------------------------------------------------------------------------
# M5-stub: trivial import / module smoke test
# ---------------------------------------------------------------------------

def test_controller_importable():
    """The controller module is importable and exposes CalculatorController."""
    from calc import controller
    assert hasattr(controller, "CalculatorController")
    assert callable(controller.CalculatorController)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_initial_state_empty():
    """A fresh controller starts with empty expression and display."""
    ctrl = CalculatorController()
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# Properties are read-only
# ---------------------------------------------------------------------------

def test_expression_is_read_only():
    """expression is a read-only property — attempting to set it raises."""
    ctrl = CalculatorController()
    with pytest.raises(AttributeError):
        ctrl.expression = "anything"


def test_display_is_read_only():
    """display is a read-only property — attempting to set it raises."""
    ctrl = CalculatorController()
    with pytest.raises(AttributeError):
        ctrl.display = "anything"


# ---------------------------------------------------------------------------
# Digit echo
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("digit", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
def test_single_digit_echo(digit):
    """Pressing a digit echoes it to both expression and display."""
    ctrl = CalculatorController()
    ctrl.press(digit)
    assert ctrl.expression == digit
    assert ctrl.display == digit


def test_multiple_digits_build_number():
    """Pressing several digits builds a multi-digit number."""
    ctrl = CalculatorController()
    for ch in "42":
        ctrl.press(ch)
    assert ctrl.expression == "42"
    assert ctrl.display == "42"


def test_decimal_point():
    """Pressing '.' echoes it to both expression and display."""
    ctrl = CalculatorController()
    ctrl.press(".")
    assert ctrl.expression == "."
    assert ctrl.display == "."


def test_decimal_number():
    """Building a decimal number like '3.14' works."""
    ctrl = CalculatorController()
    for ch in "3.14":
        ctrl.press(ch)
    assert ctrl.expression == "3.14"
    assert ctrl.display == "3.14"


# ---------------------------------------------------------------------------
# Operator echo with Unicode mapping
# ---------------------------------------------------------------------------

def test_multiply_operator_unicode():
    """Pressing '*' echoes '*' to expression and '×' to display."""
    ctrl = CalculatorController()
    ctrl.press("*")
    assert ctrl.expression == "*"
    assert ctrl.display == "\u00d7"  # ×


def test_divide_operator_unicode():
    """Pressing '/' echoes '/' to expression and '÷' to display."""
    ctrl = CalculatorController()
    ctrl.press("/")
    assert ctrl.expression == "/"
    assert ctrl.display == "\u00f7"  # ÷


def test_add_operator_passthrough():
    """Pressing '+' echoes '+' unchanged."""
    ctrl = CalculatorController()
    ctrl.press("+")
    assert ctrl.expression == "+"
    assert ctrl.display == "+"


def test_subtract_operator_passthrough():
    """Pressing '-' echoes '-' unchanged."""
    ctrl = CalculatorController()
    ctrl.press("-")
    assert ctrl.expression == "-"
    assert ctrl.display == "-"


def test_left_paren_passthrough():
    """Pressing '(' echoes '(' unchanged."""
    ctrl = CalculatorController()
    ctrl.press("(")
    assert ctrl.expression == "("
    assert ctrl.display == "("


def test_right_paren_passthrough():
    """Pressing ')' echoes ')' unchanged."""
    ctrl = CalculatorController()
    ctrl.press(")")
    assert ctrl.expression == ")"
    assert ctrl.display == ")"


# ---------------------------------------------------------------------------
# Mixed expression building
# ---------------------------------------------------------------------------

def test_build_simple_expression():
    """Building '1+2' produces correct expression and display."""
    ctrl = CalculatorController()
    for key in ["1", "+", "2"]:
        ctrl.press(key)
    assert ctrl.expression == "1+2"
    assert ctrl.display == "1+2"


def test_build_expression_with_unicode_ops():
    """Building '8/2' produces ASCII internally, Unicode on display."""
    ctrl = CalculatorController()
    for key in ["8", "/", "2"]:
        ctrl.press(key)
    assert ctrl.expression == "8/2"
    assert ctrl.display == "8\u00f72"  # 8÷2


def test_complex_expression():
    """Building '(1+2)*3' produces correct internal and display strings."""
    ctrl = CalculatorController()
    for key in ["(", "1", "+", "2", ")", "*", "3"]:
        ctrl.press(key)
    assert ctrl.expression == "(1+2)*3"
    assert ctrl.display == "(1+2)\u00d73"  # (1+2)×3


# ---------------------------------------------------------------------------
# Equals
# ---------------------------------------------------------------------------

def test_equals_shows_stub():
    """Pressing '=' sets display to 'STUB'."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")
    assert ctrl.display == "STUB"


def test_equals_preserves_expression():
    """Pressing '=' does NOT clear or change the internal expression."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")
    assert ctrl.expression == "1+2"


def test_equals_on_empty():
    """Pressing '=' on a fresh controller shows 'STUB'."""
    ctrl = CalculatorController()
    ctrl.press("=")
    assert ctrl.display == "STUB"
    assert ctrl.expression == ""


# ---------------------------------------------------------------------------
# Clear (C)
# ---------------------------------------------------------------------------

def test_clear_on_fresh_controller():
    """Pressing 'C' on a fresh controller keeps both empty."""
    ctrl = CalculatorController()
    ctrl.press("C")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_clear_after_building():
    """Pressing 'C' after building an expression clears everything."""
    ctrl = CalculatorController()
    for key in ["4", "2", "+", "7"]:
        ctrl.press(key)
    ctrl.press("C")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_clear_after_equals():
    """Pressing 'C' after '=' clears the STUB and the expression."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    assert ctrl.display == "STUB"
    ctrl.press("C")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_continue_after_clear():
    """After clearing, the user can start a fresh expression."""
    ctrl = CalculatorController()
    ctrl.press("5")
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press("C")
    ctrl.press("7")
    ctrl.press("-")
    ctrl.press("2")
    assert ctrl.expression == "7-2"
    assert ctrl.display == "7-2"


# ---------------------------------------------------------------------------
# Backspace
# ---------------------------------------------------------------------------

def test_backspace_single_char():
    """Backspace removes the last character from both expression and display."""
    ctrl = CalculatorController()
    for key in ["1", "2", "3"]:
        ctrl.press(key)
    ctrl.press("backspace")
    assert ctrl.expression == "12"
    assert ctrl.display == "12"


def test_backspace_operator():
    """Backspace removes an operator (and its Unicode display form)."""
    ctrl = CalculatorController()
    ctrl.press("4")
    ctrl.press("*")
    ctrl.press("backspace")
    assert ctrl.expression == "4"
    assert ctrl.display == "4"


def test_backspace_unicode_divide():
    """Backspace on '÷' removes the underlying '/' from both."""
    ctrl = CalculatorController()
    ctrl.press("8")
    ctrl.press("/")
    ctrl.press("backspace")
    assert ctrl.expression == "8"
    assert ctrl.display == "8"


def test_backspace_on_empty():
    """Backspace on an empty controller does not crash."""
    ctrl = CalculatorController()
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_backspace_until_empty():
    """Repeated backspace eventually leaves both empty without error."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""
    # One more — shouldn't crash
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# Typing after equals (stub behavior)
# ---------------------------------------------------------------------------

def test_typing_after_equals_appends_to_display():
    """After '=', pressing a digit appends to the STUB display."""
    ctrl = CalculatorController()
    ctrl.press("4")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")
    # display is now "STUB"
    ctrl.press("5")
    # In stub mode, display becomes "STUB5" and expression "4+25"
    assert ctrl.display == "STUB5"
    assert ctrl.expression == "4+25"


def test_clear_clears_stub_and_allows_new_expression():
    """After '=' then 'C', a fresh expression can be built."""
    ctrl = CalculatorController()
    ctrl.press("3")
    ctrl.press("+")
    ctrl.press("4")
    ctrl.press("=")
    ctrl.press("C")
    ctrl.press("9")
    assert ctrl.expression == "9"
    assert ctrl.display == "9"


# ---------------------------------------------------------------------------
# No tkinter
# ---------------------------------------------------------------------------

def test_no_tkinter_import_in_controller():
    """The controller module must never import tkinter — it's headless."""
    import ast
    import inspect
    from calc import controller

    source = inspect.getsource(controller)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "tkinter" not in alias.name.lower(), \
                    f"controller.py imports tkinter: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "tkinter" not in node.module.lower(), \
                    f"controller.py imports from tkinter: {node.module}"
