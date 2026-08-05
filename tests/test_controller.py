"""Tests for calc.controller — M2-real state machine."""

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
# M2-real: No leading operator (operator on empty expression is ignored)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("op", ["+", "-", "*", "/"])
def test_no_leading_operator(op):
    """Pressing an operator on an empty expression is ignored."""
    ctrl = CalculatorController()
    ctrl.press(op)
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# Unicode operator mapping (display layer)
# ---------------------------------------------------------------------------

def test_multiply_operator_unicode_after_digit():
    """Pressing '*' after a digit maps to '×' in display."""
    ctrl = CalculatorController()
    ctrl.press("3")
    ctrl.press("*")
    assert ctrl.expression == "3*"
    assert ctrl.display == "3\u00d7"


def test_divide_operator_unicode_after_digit():
    """Pressing '/' after a digit maps to '÷' in display."""
    ctrl = CalculatorController()
    ctrl.press("8")
    ctrl.press("/")
    assert ctrl.expression == "8/"
    assert ctrl.display == "8\u00f7"


def test_add_operator_after_digit():
    """Pressing '+' after a digit echoes unchanged."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("+")
    assert ctrl.expression == "1+"
    assert ctrl.display == "1+"


def test_subtract_operator_after_digit():
    """Pressing '-' after a digit echoes unchanged."""
    ctrl = CalculatorController()
    ctrl.press("5")
    ctrl.press("-")
    assert ctrl.expression == "5-"
    assert ctrl.display == "5-"


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
# M2-real: Operator replacement (last-char operator gets replaced)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("first,second", [
    ("+", "-"),
    ("+", "*"),
    ("+", "/"),
    ("-", "+"),
    ("*", "/"),
    ("/", "*"),
    ("/", "+"),
])
def test_operator_replacement(first, second):
    """When the last char is an operator, pressing another operator replaces it."""
    ctrl = CalculatorController()
    ctrl.press("3")
    ctrl.press(first)
    ctrl.press(second)
    assert ctrl.expression == f"3{second}"
    # Display: first char "3", then second's display form
    from calc.controller import CalculatorController as CC
    assert ctrl.display == f"3{CC._to_display(second)}"


def test_operator_replacement_twice():
    """Replacing an operator twice works correctly."""
    ctrl = CalculatorController()
    ctrl.press("7")
    ctrl.press("+")
    ctrl.press("-")
    ctrl.press("*")
    assert ctrl.expression == "7*"
    assert ctrl.display == "7\u00d7"


def test_operator_not_replaced_when_last_is_digit():
    """Operator after a digit appends, does not replace."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("2")
    ctrl.press("+")
    assert ctrl.expression == "12+"
    assert ctrl.display == "12+"


# ---------------------------------------------------------------------------
# M2-real: No operator after '('
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("op", ["+", "-", "*", "/"])
def test_no_operator_after_open_paren(op):
    """Operator right after '(' is ignored."""
    ctrl = CalculatorController()
    ctrl.press("(")
    ctrl.press(op)
    assert ctrl.expression == "("
    assert ctrl.display == "("


def test_operator_allowed_after_digit_in_parens():
    """Operator after a digit inside parens is allowed."""
    ctrl = CalculatorController()
    ctrl.press("(")
    ctrl.press("3")
    ctrl.press("+")
    assert ctrl.expression == "(3+"
    assert ctrl.display == "(3+"


# ---------------------------------------------------------------------------
# M2-real: Decimal guard (no double dot in same number)
# ---------------------------------------------------------------------------

def test_double_decimal_ignored():
    """Pressing '.' when current number already has a dot is ignored."""
    ctrl = CalculatorController()
    ctrl.press("3")
    ctrl.press(".")
    ctrl.press("1")
    ctrl.press(".")
    assert ctrl.expression == "3.1"
    assert ctrl.display == "3.1"


def test_decimal_after_operator_allowed():
    """After an operator, '.' starts a new number so it's allowed."""
    ctrl = CalculatorController()
    ctrl.press("5")
    ctrl.press("+")
    ctrl.press(".")
    ctrl.press("7")
    assert ctrl.expression == "5+.7"
    assert ctrl.display == "5+.7"


def test_decimal_after_open_paren_allowed():
    """After '(', '.' starts a new number so it's allowed."""
    ctrl = CalculatorController()
    ctrl.press("(")
    ctrl.press(".")
    ctrl.press("5")
    assert ctrl.expression == "(.5"
    assert ctrl.display == "(.5"


def test_double_decimal_across_operator():
    """Two dots separated by an operator are both allowed (different numbers)."""
    ctrl = CalculatorController()
    ctrl.press("2")
    ctrl.press(".")
    ctrl.press("5")
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press(".")
    ctrl.press("1")
    assert ctrl.expression == "2.5+3.1"
    assert ctrl.display == "2.5+3.1"


def test_leading_dot_decimal_guard():
    """Starting with '.' then pressing '.' again is ignored."""
    ctrl = CalculatorController()
    ctrl.press(".")
    ctrl.press(".")
    assert ctrl.expression == "."
    assert ctrl.display == "."


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
# Equals — real engine delegation
# ---------------------------------------------------------------------------

def test_equals_evaluates_expression():
    """Pressing '=' delegates to engine and shows the result."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")
    assert ctrl.display == "3"


def test_equals_preserves_expression():
    """Pressing '=' does NOT clear or change the internal expression."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")
    assert ctrl.expression == "1+2"


def test_equals_on_empty_shows_error():
    """Pressing '=' on a fresh controller shows 'Error'."""
    ctrl = CalculatorController()
    ctrl.press("=")
    assert ctrl.display == "Error"
    assert ctrl.expression == ""


def test_equals_with_precedence():
    """'=' respects operator precedence: 2+3*4 = 14."""
    ctrl = CalculatorController()
    for key in ["2", "+", "3", "*", "4"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "14"


def test_equals_with_parentheses():
    """'=' respects parentheses: (2+3)*4 = 20."""
    ctrl = CalculatorController()
    for key in ["(", "2", "+", "3", ")", "*", "4"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "20"


def test_equals_with_decimals():
    """'=' works with decimals: 0.1+0.2."""
    ctrl = CalculatorController()
    for key in ["0", ".", "1", "+", "0", ".", "2"]:
        ctrl.press(key)
    ctrl.press("=")
    # 0.1 + 0.2 = 0.3 (floating point — accept reasonable result)
    result = float(ctrl.display)
    assert abs(result - 0.3) < 1e-10


def test_equals_division_by_zero():
    """Division by zero shows 'Error'."""
    ctrl = CalculatorController()
    for key in ["5", "/", "0"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "Error"


# ---------------------------------------------------------------------------
# M2-real: result_shown flag — behavior after '='
# ---------------------------------------------------------------------------

def test_digit_after_result_starts_fresh():
    """After '=', pressing a digit starts a new expression."""
    ctrl = CalculatorController()
    ctrl.press("4")
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")  # display = "6"
    ctrl.press("5")
    assert ctrl.expression == "5"
    assert ctrl.display == "5"


def test_operator_after_result_continues():
    """After '=', pressing an operator continues from the result."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")  # display = "9"
    ctrl.press("+")
    assert ctrl.expression == "9+"
    assert ctrl.display == "9+"


def test_operator_after_result_then_evaluate():
    """After '=', continue with operator and evaluate again."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")  # 9
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press("=")  # 9 + 3
    assert ctrl.display == "12"


def test_decimal_after_result_starts_fresh():
    """After '=', pressing '.' starts a new number."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    ctrl.press(".")
    ctrl.press("5")
    assert ctrl.expression == ".5"
    assert ctrl.display == ".5"


def test_open_paren_after_result_starts_fresh():
    """After '=', pressing '(' starts a new expression."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    ctrl.press("(")
    ctrl.press("3")
    ctrl.press(")")
    assert ctrl.expression == "(3)"
    assert ctrl.display == "(3)"


def test_close_paren_after_result_ignored():
    """After '=', pressing ')' clears and ignores (no crash)."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    ctrl.press(")")
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# M2-real: Error recovery
# ---------------------------------------------------------------------------

def test_error_digit_clears_and_starts_fresh():
    """After 'Error', pressing a digit clears and starts fresh."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    assert ctrl.display == "Error"
    ctrl.press("5")
    assert ctrl.expression == "5"
    assert ctrl.display == "5"


def test_error_operator_ignored():
    """After 'Error', pressing an operator is ignored (expression empty)."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    assert ctrl.display == "Error"
    ctrl.press("+")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_error_clear_resets():
    """After 'Error', pressing 'C' clears normally."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    assert ctrl.display == "Error"
    ctrl.press("C")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_error_decimal_starts_fresh():
    """After 'Error', pressing '.' starts a fresh decimal number."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    ctrl.press(".")
    ctrl.press("5")
    assert ctrl.expression == ".5"
    assert ctrl.display == ".5"


def test_error_open_paren_starts_fresh():
    """After 'Error', pressing '(' starts fresh."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    ctrl.press("(")
    ctrl.press("2")
    ctrl.press(")")
    assert ctrl.expression == "(2)"
    assert ctrl.display == "(2)"


def test_error_close_paren_clears_and_ignores():
    """After 'Error', pressing ')' clears and ignores."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    ctrl.press(")")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_error_backspace_clears_all():
    """After 'Error', backspace clears everything."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    assert ctrl.display == "Error"
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_error_multiple_keys_recovery():
    """After 'Error', the user can type a full new expression."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
    assert ctrl.display == "Error"
    # Type a new expression
    for key in ["7", "+", "8"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "15"


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
    """Pressing 'C' after '=' clears the result and the expression."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    assert ctrl.display == "9"
    ctrl.press("C")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_clear_after_error():
    """Pressing 'C' after an error clears everything."""
    ctrl = CalculatorController()
    ctrl.press("1")
    ctrl.press("/")
    ctrl.press("0")
    ctrl.press("=")
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
# M2-real: Backspace after result / error
# ---------------------------------------------------------------------------

def test_backspace_after_result_clears_all():
    """After '=', backspace clears everything (Windows Calculator behavior)."""
    ctrl = CalculatorController()
    ctrl.press("5")
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press("=")  # displays "8"
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""


def test_backspace_after_single_digit_equals():
    """After '9=', backspace clears everything."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    ctrl.press("backspace")
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# M2-real: result_shown reset after clear
# ---------------------------------------------------------------------------

def test_result_shown_reset_after_clear():
    """After C, result_shown is reset — operator after C is ignored."""
    ctrl = CalculatorController()
    ctrl.press("9")
    ctrl.press("=")
    ctrl.press("C")  # result_shown reset
    ctrl.press("+")  # operator on empty → ignored
    assert ctrl.expression == ""
    assert ctrl.display == ""


# ---------------------------------------------------------------------------
# M2-real: operator after '(' is ignored even after backspace
# ---------------------------------------------------------------------------

def test_operator_after_open_paren_after_backspace():
    """After clearing back to '(', another operator is ignored."""
    ctrl = CalculatorController()
    ctrl.press("(")
    ctrl.press("3")
    ctrl.press("+")
    ctrl.press("backspace")  # removes '+' → "(3"
    ctrl.press("backspace")  # removes '3' → "("
    ctrl.press("*")  # operator after '(' → ignored
    assert ctrl.expression == "("
    assert ctrl.display == "("


# ---------------------------------------------------------------------------
# M2-real: End-to-end calculator flows
# ---------------------------------------------------------------------------

def test_full_calculation_flow():
    """A realistic sequence: 12.5 * 2 = 25, then clear, then new calc."""
    ctrl = CalculatorController()
    for key in ["1", "2", ".", "5", "*", "2"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "25"
    ctrl.press("C")
    assert ctrl.expression == ""
    ctrl.press("7")
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press("=")
    assert ctrl.display == "10"


def test_chained_result_continuation():
    """Chain result continuations: 5+3= → +2= → 10."""
    ctrl = CalculatorController()
    ctrl.press("5")
    ctrl.press("+")
    ctrl.press("3")
    ctrl.press("=")  # 8
    ctrl.press("+")
    ctrl.press("2")
    ctrl.press("=")  # 8+2
    assert ctrl.display == "10"


def test_complex_expression_with_everything():
    """Expression with parens, decimals, precedence: (3.5+6.5)*2/5."""
    ctrl = CalculatorController()
    for key in ["(", "3", ".", "5", "+", "6", ".", "5", ")", "*", "2", "/", "5"]:
        ctrl.press(key)
    ctrl.press("=")
    assert ctrl.display == "4"


# ---------------------------------------------------------------------------
# M2-real: Never raises contract
# ---------------------------------------------------------------------------

def test_press_never_raises():
    """No sequence of presses should ever raise an exception."""
    ctrl = CalculatorController()

    # Try many combinations that might be problematic
    sequences = [
        ["="],
        ["C", "C", "C"],
        ["backspace", "backspace", "backspace"],
        [")", ")", ")"],
        ["(", "(", "("],
        ["+", "-", "*", "/"],
        [".", ".", "."],
        ["1", "/", "0", "=", "+", "+", "+"],
        ["9", "=", ")", "(", ".", "+"],
        ["1", "/", "0", "=", "5", "+", "3", "="],
        ["1", "+", "+", "+", "2", "="],
        ["(", "+", ")", "="],
        [".", "5", "+", ".", "3", "="],
        ["1", ".", ".", "2", "+", "3", ".", ".", "4", "="],
    ]

    for seq in sequences:
        ctrl = CalculatorController()
        for key in seq:
            try:
                ctrl.press(key)
            except Exception as e:
                pytest.fail(
                    f"press({key!r}) raised {type(e).__name__}: {e} "
                    f"in sequence {seq!r}"
                )


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
