"""Tests for calc.view — view-controller wiring and lambda closures.

These tests validate the integration between CalculatorView and
CalculatorController WITHOUT creating a live Tkinter display.
All Tkinter calls are patched so no X11/Wayland/Win32 display is needed.
"""

import ast
import inspect
from unittest.mock import MagicMock

import pytest

from calc.controller import CalculatorController
from calc.view import BUTTONS, CalculatorView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_create_buttons_ast() -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Walk the view module AST and return the _create_buttons FunctionDef node."""
    from calc import view
    source = inspect.getsource(view)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CalculatorView":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name == "_create_buttons":
                        return item
    raise AssertionError("Could not find CalculatorView._create_buttons in view.py AST")


def _make_testable_view(controller: CalculatorController) -> CalculatorView:
    """Return a CalculatorView whose Tkinter internals are replaced with mocks.

    Uses __new__ to bypass the real __init__ (which calls tk.Tk()).
    """
    view = object.__new__(CalculatorView)
    view._controller = controller
    view._display_var = MagicMock()
    view._root = MagicMock()
    return view


# ---------------------------------------------------------------------------
# Lambda closure safety — late-binding bug prevention
# ---------------------------------------------------------------------------

def test_button_commands_use_default_arg_not_late_binding():
    """Every tk.Button command lambda must use a default-argument pattern
    like `lambda k=key: ...`, NOT `lambda: self._on_press(key)`.

    The late-binding form captures the *loop variable*, so all 20 buttons
    would fire the same last key.  The default-argument pattern binds the
    current value at definition time.
    """
    func_node = _get_create_buttons_ast()

    for node in ast.walk(func_node):
        if not isinstance(node, ast.Lambda):
            continue

        # A safe lambda has at least one default argument (e.g. k=key).
        defaults = node.args.defaults
        assert len(defaults) >= 1, (
            f"Lambda at line ~{node.lineno} in _create_buttons() has NO default "
            f"arguments — this is the late-binding anti-pattern. "
            f"Use `lambda k=key: self._on_press(k)` instead of `lambda: self._on_press(key)`."
        )


# ---------------------------------------------------------------------------
# View-controller wiring: _on_press → controller.press() + refresh()
# ---------------------------------------------------------------------------

class TestViewWiring:
    """Integration tests: pressing a "button" in the view updates the controller
    and refreshes the display."""

    def test_digit_press_updates_display(self):
        """Pressing a digit via _on_press updates controller and display_var."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        view._on_press("7")
        assert ctrl.expression == "7"
        assert ctrl.display == "7"
        view._display_var.set.assert_called_once_with("7")

    def test_operator_press_updates_display_with_unicode(self):
        """Pressing '*' via _on_press shows '×' in display."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        view._on_press("4")
        view._display_var.set.reset_mock()
        view._on_press("*")
        assert ctrl.expression == "4*"
        assert ctrl.display == "4\u00d7"
        view._display_var.set.assert_called_once_with("4\u00d7")

    def test_equals_press_evaluates_expression(self):
        """Pressing '=' via _on_press delegates to engine and shows result."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        view._on_press("1")
        view._on_press("+")
        view._on_press("2")
        view._display_var.set.reset_mock()
        view._on_press("=")
        assert ctrl.display == "3"
        view._display_var.set.assert_called_once_with("3")

    def test_clear_press_resets_everything(self):
        """Pressing 'C' via _on_press clears expression and display."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        view._on_press("5")
        view._on_press("+")
        view._on_press("3")
        view._display_var.set.reset_mock()
        view._on_press("C")
        assert ctrl.expression == ""
        assert ctrl.display == ""
        view._display_var.set.assert_called_once_with("")

    def test_backspace_press_removes_last_char(self):
        """Pressing 'backspace' via _on_press removes last character."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        view._on_press("1")
        view._on_press("2")
        view._on_press("3")
        view._display_var.set.reset_mock()
        view._on_press("backspace")
        assert ctrl.expression == "12"
        assert ctrl.display == "12"
        view._display_var.set.assert_called_once_with("12")

    def test_full_expression_flow(self):
        """Building '(8/2)+3' through _on_press works end to end."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        for key in ["(", "8", "/", "2", ")", "+", "3"]:
            view._on_press(key)

        assert ctrl.expression == "(8/2)+3"
        assert ctrl.display == "(8\u00f72)+3"
        view._display_var.set.assert_called_with("(8\u00f72)+3")

    def test_every_button_key_works_via_on_press(self):
        """Every key in the BUTTONS layout is accepted by _on_press
        and produces a non-crashing state change."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        # Collect all unique keys from the button layout
        all_keys = []
        for row in BUTTONS:
            for _, key in row:
                if key not in all_keys:
                    all_keys.append(key)

        for key in all_keys:
            # Press the key — must not crash
            view._on_press(key)
            # After pressing, both expression and display should be strings
            assert isinstance(ctrl.expression, str), (
                f"After pressing {key!r}, expression is not a str: {ctrl.expression!r}"
            )
            assert isinstance(ctrl.display, str), (
                f"After pressing {key!r}, display is not a str: {ctrl.display!r}"
            )

    def test_on_press_always_calls_refresh(self):
        """Every _on_press call must update the display (call refresh)."""
        ctrl = CalculatorController()
        view = _make_testable_view(ctrl)

        for key in ["1", "+", "2", "=", "C", "5", "backspace"]:
            view._display_var.set.reset_mock()
            view._on_press(key)
            view._display_var.set.assert_called_once(), (
                f"_on_press({key!r}) did not call self._display_var.set()"
            )


# ---------------------------------------------------------------------------
# refresh() reads controller.display
# ---------------------------------------------------------------------------

def test_refresh_reads_controller_display():
    """refresh() must read controller.display and push it to the display widget."""
    ctrl = CalculatorController()
    view = _make_testable_view(ctrl)

    # Manually set up a known controller state
    ctrl.press("4")
    ctrl.press("2")

    view._display_var.set.reset_mock()
    view.refresh()
    view._display_var.set.assert_called_once_with("42")


def test_refresh_after_multiple_operations():
    """refresh() always shows the current controller.display value."""
    ctrl = CalculatorController()
    view = _make_testable_view(ctrl)

    ctrl.press("9")
    view.refresh()
    assert view._display_var.set.call_args_list[-1] == (("9",),)

    ctrl.press("+")
    view.refresh()
    assert view._display_var.set.call_args_list[-1] == (("9+",),)

    ctrl.press("1")
    view.refresh()
    assert view._display_var.set.call_args_list[-1] == (("9+1",),)

    ctrl.press("=")
    view.refresh()
    assert view._display_var.set.call_args_list[-1] == (("10",),)
