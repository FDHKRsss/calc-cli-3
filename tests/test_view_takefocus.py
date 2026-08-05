"""Tests for calc.view — takefocus=False on all buttons.

Validates that every tk.Button created in CalculatorView._create_buttons()
has takefocus=False, preventing buttons from stealing keyboard focus.
This is done via AST inspection — no live Tkinter display is required.

Because the buttons are created in a loop from a single tk.Button(...)
call, we verify that the one call site includes takefocus=False, which
guarantees all 20 runtime buttons inherit it.
"""

import ast
import inspect

from calc import view


def _get_create_buttons_ast() -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Walk the view module AST and return the _create_buttons FunctionDef node."""
    source = inspect.getsource(view)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CalculatorView":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name == "_create_buttons":
                        return item
    raise AssertionError("Could not find CalculatorView._create_buttons in view.py AST")


def _get_tk_button_calls(func_node: ast.FunctionDef) -> list[ast.Call]:
    """Return all tk.Button(...) call nodes from the function AST."""
    result: list[ast.Call] = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                    and node.func.attr == "Button"
                ):
                    result.append(node)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_takefocus_present_on_button_call():
    """The tk.Button() call in _create_buttons includes takefocus=False.

    Since all 20 buttons are created from one call site inside a loop,
    verifying this single call covers every runtime button.
    """
    func_node = _get_create_buttons_ast()
    button_calls = _get_tk_button_calls(func_node)

    assert len(button_calls) == 1, (
        f"Expected exactly 1 tk.Button() call site in _create_buttons, "
        f"found {len(button_calls)}"
    )

    call = button_calls[0]
    found = False
    for kw in call.keywords:
        if kw.arg == "takefocus":
            if isinstance(kw.value, ast.Constant) and kw.value.value is False:
                found = True
                break
            if isinstance(kw.value, ast.Name) and kw.value.id == "False":
                found = True
                break

    assert found, (
        "The tk.Button() in _create_buttons() is missing takefocus=False. "
        f"Keywords present: {[kw.arg for kw in call.keywords]}"
    )


def test_all_20_buttons_inherit_takefocus():
    """The button layout has 20 entries and the single call site has takefocus=False.

    Combined, this means all 20 runtime buttons will have takefocus=False.
    """
    func_node = _get_create_buttons_ast()
    button_calls = _get_tk_button_calls(func_node)

    # There must be exactly one tk.Button() call that the loop uses
    assert len(button_calls) == 1

    # Verify the call has takefocus=False
    call = button_calls[0]
    has_takefocus_false = any(
        kw.arg == "takefocus"
        and (
            (isinstance(kw.value, ast.Constant) and kw.value.value is False)
            or (isinstance(kw.value, ast.Name) and kw.value.id == "False")
        )
        for kw in call.keywords
    )
    assert has_takefocus_false, "tk.Button() missing takefocus=False"

    # Verify the BUTTONS layout has exactly 20 entries (5 rows × 4 columns)
    assert hasattr(view, "BUTTONS"), "view module missing BUTTONS constant"
    total_buttons = sum(len(row) for row in view.BUTTONS)
    assert total_buttons == 20, (
        f"BUTTONS layout has {total_buttons} entries, expected 20 (5 rows × 4 cols)"
    )


def test_takefocus_not_set_to_true():
    """No tk.Button in _create_buttons has takefocus=True or takefocus=1."""
    func_node = _get_create_buttons_ast()
    button_calls = _get_tk_button_calls(func_node)

    for call in button_calls:
        for kw in call.keywords:
            if kw.arg == "takefocus":
                if isinstance(kw.value, ast.Constant):
                    assert kw.value.value is not True, (
                        f"takefocus=True found at line ~{call.lineno}"
                    )
                    assert kw.value.value != 1, (
                        f"takefocus=1 found at line ~{call.lineno}"
                    )
                if isinstance(kw.value, ast.Name):
                    assert kw.value.id != "True", (
                        f"takefocus=True (Name node) found at line ~{call.lineno}"
                    )


def test_takefocus_is_last_keyword():
    """takefocus=False appears as a keyword argument (best practice: clarity)."""
    func_node = _get_create_buttons_ast()
    button_calls = _get_tk_button_calls(func_node)

    call = button_calls[0]
    # Check that 'takefocus' is among the keywords
    kw_names = [kw.arg for kw in call.keywords]
    assert "takefocus" in kw_names, (
        f"takefocus not found in keywords: {kw_names}"
    )
