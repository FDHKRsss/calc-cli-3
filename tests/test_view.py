"""Tests for calc.view — M3 stub.

These tests validate the view module's data structures (button layout,
keyboard maps) and class interface WITHOUT creating a live Tkinter
display.  No test imports tkinter directly or calls mainloop().
"""

import inspect

import pytest

from calc.controller import CalculatorController
from calc.view import BUTTONS, KEYBOARD_MAP, NUMPAD_MAP, CalculatorView


# ---------------------------------------------------------------------------
# Module import smoke test
# ---------------------------------------------------------------------------

def test_view_module_importable():
    """The view module is importable and exposes CalculatorView."""
    from calc import view
    assert hasattr(view, "CalculatorView")
    assert callable(view.CalculatorView)


# ---------------------------------------------------------------------------
# BUTTONS layout structure
# ---------------------------------------------------------------------------

def test_buttons_is_list_of_lists():
    """BUTTONS is a list of rows, each row is a list of tuples."""
    assert isinstance(BUTTONS, list)
    assert len(BUTTONS) > 0
    for row in BUTTONS:
        assert isinstance(row, list)
        for item in row:
            assert isinstance(item, tuple)
            assert len(item) == 2
            label, key = item
            assert isinstance(label, str)
            assert isinstance(key, str)


def test_buttons_five_rows():
    """The layout has exactly 5 rows (as in Windows Calculator)."""
    assert len(BUTTONS) == 5


def test_buttons_four_per_row():
    """Each row has exactly 4 buttons (4-column grid)."""
    for i, row in enumerate(BUTTONS):
        assert len(row) == 4, f"Row {i} has {len(row)} buttons, expected 4"


def test_buttons_all_keys_unique():
    """No controller key should appear twice in the button layout."""
    keys = [key for row in BUTTONS for _, key in row]
    assert len(keys) == len(set(keys)), \
        f"Duplicate keys found: {[k for k in set(keys) if keys.count(k) > 1]}"


# ---------------------------------------------------------------------------
# BUTTONS — specific required keys
# ---------------------------------------------------------------------------

# All controller keys that must appear in the button grid.
REQUIRED_BUTTON_KEYS = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ".", "+", "-", "*", "/", "(", ")", "=", "C", "backspace",
}


def test_buttons_all_required_keys_present():
    """Every required key appears in the button layout."""
    keys = {key for row in BUTTONS for _, key in row}
    missing = REQUIRED_BUTTON_KEYS - keys
    assert not missing, f"Missing button keys: {missing}"


def test_buttons_no_extraneous_keys():
    """The button layout has exactly the 20 required keys (no extras)."""
    keys = {key for row in BUTTONS for _, key in row}
    assert keys == REQUIRED_BUTTON_KEYS


def test_buttons_row1():
    """Row 1: ( ) C backspace"""
    row = BUTTONS[0]
    keys = [key for _, key in row]
    assert keys == ["(", ")", "C", "backspace"]


def test_buttons_row2():
    """Row 2: 7 8 9 /"""
    row = BUTTONS[1]
    keys = [key for _, key in row]
    assert keys == ["7", "8", "9", "/"]


def test_buttons_row3():
    """Row 3: 4 5 6 *"""
    row = BUTTONS[2]
    keys = [key for _, key in row]
    assert keys == ["4", "5", "6", "*"]


def test_buttons_row4():
    """Row 4: 1 2 3 -"""
    row = BUTTONS[3]
    keys = [key for _, key in row]
    assert keys == ["1", "2", "3", "-"]


def test_buttons_row5():
    """Row 5: . 0 = +"""
    row = BUTTONS[4]
    keys = [key for _, key in row]
    assert keys == [".", "0", "=", "+"]


# ---------------------------------------------------------------------------
# BUTTONS — Unicode display labels
# ---------------------------------------------------------------------------

def test_divide_button_label_is_unicode_divide():
    """The '/' button shows the Unicode division sign (÷)."""
    for row in BUTTONS:
        for label, key in row:
            if key == "/":
                assert label == "\u00f7", f"Label for '/' is {label!r}, expected '\u00f7'"
                return
    pytest.fail("No button with key '/' found")


def test_multiply_button_label_is_unicode_multiply():
    """The '*' button shows the Unicode multiplication sign (×)."""
    for row in BUTTONS:
        for label, key in row:
            if key == "*":
                assert label == "\u00d7", f"Label for '*' is {label!r}, expected '\u00d7'"
                return
    pytest.fail("No button with key '*' found")


def test_subtract_button_label_is_unicode_minus():
    """The '-' button shows the Unicode minus sign (−)."""
    for row in BUTTONS:
        for label, key in row:
            if key == "-":
                assert label == "\u2212", f"Label for '-' is {label!r}, expected '\u2212'"
                return
    pytest.fail("No button with key '-' found")


def test_backspace_button_label_is_unicode_erase():
    """The backspace button shows the Unicode erase symbol (⌫)."""
    for row in BUTTONS:
        for label, key in row:
            if key == "backspace":
                assert label == "\u232b", f"Label for 'backspace' is {label!r}, expected '\u232b'"
                return
    pytest.fail("No button with key 'backspace' found")


def test_digit_labels_match_keys():
    """Digit button labels match their controller keys (0-9)."""
    for row in BUTTONS:
        for label, key in row:
            if key.isdigit():
                assert label == key, f"Label {label!r} != key {key!r}"


def test_dot_label():
    """The '.' button shows '.' as its label."""
    for row in BUTTONS:
        for label, key in row:
            if key == ".":
                assert label == ".", f"Label for '.' is {label!r}"
                return
    pytest.fail("No button with key '.' found")


def test_equals_label():
    """The '=' button shows '=' as its label."""
    for row in BUTTONS:
        for label, key in row:
            if key == "=":
                assert label == "=", f"Label for '=' is {label!r}"
                return
    pytest.fail("No button with key '=' found")


def test_plus_label():
    """The '+' button shows '+' as its label."""
    for row in BUTTONS:
        for label, key in row:
            if key == "+":
                assert label == "+", f"Label for '+' is {label!r}"
                return
    pytest.fail("No button with key '+' found")


def test_clear_label():
    """The 'C' button shows 'C' as its label."""
    for row in BUTTONS:
        for label, key in row:
            if key == "C":
                assert label == "C", f"Label for 'C' is {label!r}"
                return
    pytest.fail("No button with key 'C' found")


def test_paren_labels_match_keys():
    """Parenthesis button labels match their keys."""
    for row in BUTTONS:
        for label, key in row:
            if key in ("(", ")"):
                assert label == key, f"Label {label!r} != key {key!r}"


# ---------------------------------------------------------------------------
# KEYBOARD_MAP
# ---------------------------------------------------------------------------

def test_keyboard_map_is_dict():
    """KEYBOARD_MAP is a dict of str -> str."""
    assert isinstance(KEYBOARD_MAP, dict)
    for k, v in KEYBOARD_MAP.items():
        assert isinstance(k, str)
        assert isinstance(v, str)


def test_keyboard_map_digits():
    """KEYBOARD_MAP maps '0'–'9' to themselves."""
    for digit in "0123456789":
        assert KEYBOARD_MAP.get(digit) == digit, \
            f"KEYBOARD_MAP missing or wrong for '{digit}'"


def test_keyboard_map_operators():
    """KEYBOARD_MAP maps operator keysyms to controller keys."""
    assert KEYBOARD_MAP.get("period") == "."
    assert KEYBOARD_MAP.get("plus") == "+"
    assert KEYBOARD_MAP.get("minus") == "-"
    assert KEYBOARD_MAP.get("asterisk") == "*"
    assert KEYBOARD_MAP.get("slash") == "/"


def test_keyboard_map_parens():
    """KEYBOARD_MAP maps parenthesis keysyms."""
    assert KEYBOARD_MAP.get("parenleft") == "("
    assert KEYBOARD_MAP.get("parenright") == ")"


def test_keyboard_map_action_keys():
    """KEYBOARD_MAP maps Return, BackSpace, Escape, Delete."""
    assert KEYBOARD_MAP.get("Return") == "="
    assert KEYBOARD_MAP.get("KP_Enter") == "="
    assert KEYBOARD_MAP.get("BackSpace") == "backspace"
    assert KEYBOARD_MAP.get("Escape") == "C"
    assert KEYBOARD_MAP.get("Delete") == "C"


def test_keyboard_map_no_bindings_missing():
    """All essential keyboard actions have a binding."""
    required = {
        "Return", "KP_Enter", "BackSpace", "Escape", "Delete",
        "period", "plus", "minus", "asterisk", "slash",
        "parenleft", "parenright",
    }
    for d in "0123456789":
        required.add(d)
    missing = required - set(KEYBOARD_MAP.keys())
    assert not missing, f"Missing keyboard bindings: {missing}"


# ---------------------------------------------------------------------------
# NUMPAD_MAP
# ---------------------------------------------------------------------------

def test_numpad_map_is_dict():
    """NUMPAD_MAP is a dict of str -> str."""
    assert isinstance(NUMPAD_MAP, dict)
    for k, v in NUMPAD_MAP.items():
        assert isinstance(k, str)
        assert isinstance(v, str)


def test_numpad_map_digits():
    """NUMPAD_MAP maps KP_0–KP_9 to '0'–'9'."""
    for digit in range(10):
        keysym = f"KP_{digit}"
        assert NUMPAD_MAP.get(keysym) == str(digit), \
            f"NUMPAD_MAP missing or wrong for '{keysym}'"


def test_numpad_map_decimal():
    """NUMPAD_MAP maps KP_Decimal to '.'."""
    assert NUMPAD_MAP.get("KP_Decimal") == "."


def test_numpad_map_operators():
    """NUMPAD_MAP maps numpad operator keysyms."""
    assert NUMPAD_MAP.get("KP_Add") == "+"
    assert NUMPAD_MAP.get("KP_Subtract") == "-"
    assert NUMPAD_MAP.get("KP_Multiply") == "*"
    assert NUMPAD_MAP.get("KP_Divide") == "/"


def test_numpad_map_covers_all_standard_numpad():
    """NUMPAD_MAP covers the standard numpad keys (0-9, decimal, 4 ops)."""
    expected = {f"KP_{d}" for d in range(10)}
    expected.update({"KP_Decimal", "KP_Add", "KP_Subtract", "KP_Multiply", "KP_Divide"})
    assert set(NUMPAD_MAP.keys()) == expected, \
        f"Expected {sorted(expected)}, got {sorted(NUMPAD_MAP.keys())}"


# ---------------------------------------------------------------------------
# CalculatorView class interface
# ---------------------------------------------------------------------------

def test_calculator_view_exists():
    """CalculatorView is a class."""
    assert inspect.isclass(CalculatorView)


def test_calculator_view_has_refresh():
    """CalculatorView has a refresh() method."""
    assert hasattr(CalculatorView, "refresh")
    assert callable(CalculatorView.refresh)


def test_calculator_view_has_run():
    """CalculatorView has a run() method."""
    assert hasattr(CalculatorView, "run")
    assert callable(CalculatorView.run)


def test_calculator_view_init_accepts_controller():
    """CalculatorView.__init__ accepts a CalculatorController."""
    sig = inspect.signature(CalculatorView.__init__)
    params = list(sig.parameters.keys())
    # Expected: self, controller
    assert len(params) >= 2, f"Expected at least 2 params, got {params}"
    assert "controller" in params, f"Expected 'controller' param, got {params}"


def test_calculator_view_refresh_signature():
    """refresh() takes no arguments beyond self."""
    sig = inspect.signature(CalculatorView.refresh)
    params = list(sig.parameters.keys())
    assert params == ["self"], f"Expected ['self'], got {params}"


def test_calculator_view_run_signature():
    """run() takes no arguments beyond self."""
    sig = inspect.signature(CalculatorView.run)
    params = list(sig.parameters.keys())
    assert params == ["self"], f"Expected ['self'], got {params}"


# ---------------------------------------------------------------------------
# No tkinter import in test file itself
# ---------------------------------------------------------------------------

def test_view_test_file_does_not_import_tkinter():
    """This test file itself must not import tkinter directly."""
    import ast

    source = inspect.getsource(inspect.getmodule(
        test_view_test_file_does_not_import_tkinter
    ))
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "tkinter" not in alias.name.lower(), \
                    f"test_view.py imports tkinter: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "tkinter" not in node.module.lower(), \
                    f"test_view.py imports from tkinter: {node.module}"


# ---------------------------------------------------------------------------
# Edge cases: consistency between BUTTONS and keyboard maps
# ---------------------------------------------------------------------------

def test_all_button_keys_have_keyboard_mapping():
    """Every button key should have at least one keyboard binding."""
    button_keys = {key for row in BUTTONS for _, key in row}

    # All controller actions reachable via keyboard
    keyboard_actions = set(KEYBOARD_MAP.values())
    numpad_actions = set(NUMPAD_MAP.values())
    all_keyboard_actions = keyboard_actions | numpad_actions

    # Every button key should have some keyboard path
    # (backspace and C are covered via BackSpace and Escape/Delete in KEYBOARD_MAP)
    missing = button_keys - all_keyboard_actions
    assert not missing, f"Button keys without any keyboard binding: {missing}"
