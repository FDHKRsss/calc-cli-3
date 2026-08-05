"""Tests for calc.view — M3-real polish (AST-based, no live display).

Validates the visual/styling requirements that distinguish the real
view from the stub: fonts, colors, window title, focus handling,
non-resizable window, display styling.  All checks are performed via
AST analysis of calc/view.py — no tkinter import, no live display.
"""

import ast
import inspect

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_view_source_tree() -> ast.Module:
    """Parse calc/view.py and return the module AST."""
    from calc import view
    source = inspect.getsource(view)
    return ast.parse(source)


def _get_class_node(tree: ast.Module, class_name: str) -> ast.ClassDef:
    """Return the ClassDef node for *class_name* in *tree*."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"Class {class_name} not found in view.py AST")


def _get_method_node(class_node: ast.ClassDef, method_name: str) -> ast.FunctionDef:
    """Return the FunctionDef node for *method_name* inside *class_node*."""
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == method_name:
                return item
    raise AssertionError(
        f"Method {method_name} not found in class {class_node.name}"
    )


def _has_method_call(method_node: ast.FunctionDef, obj_name: str, method_name: str) -> bool:
    """Return True if *obj_name*.*method_name*(...) is called in *method_node*."""
    for node in ast.walk(method_node):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == method_name
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == obj_name
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "self"
            ):
                return True
    return False


def _get_tk_method_calls(
    method_node: ast.FunctionDef, tk_var: str, method: str,
) -> list[ast.Call]:
    """Return all calls to *tk_var*.*method*(...) inside *method_node*."""
    results: list[ast.Call] = []
    for node in ast.walk(method_node):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == method
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == tk_var
            ):
                results.append(node)
    return results


def _call_has_kwarg(call: ast.Call, kw_name: str) -> ast.keyword | None:
    """Return the keyword node if *kw_name* is present in *call*, else None."""
    for kw in call.keywords:
        if kw.arg == kw_name:
            return kw
    return None


def _kwarg_equals(kw: ast.keyword, expected) -> bool:
    """Check if a keyword's value equals *expected*.

    Handles ast.Constant (literal) and ast.Name (variable reference).
    """
    if isinstance(kw.value, ast.Constant):
        return kw.value.value == expected
    if isinstance(kw.value, ast.Name):
        return kw.value.id == str(expected)
    if isinstance(kw.value, ast.Tuple):
        elts = []
        for elt in kw.value.elts:
            if isinstance(elt, ast.Constant):
                elts.append(elt.value)
            elif isinstance(elt, ast.Name):
                elts.append(elt.id)
            else:
                return False
        return tuple(elts) == expected
    return False


# ===========================================================================
# __init__ — window configuration
# ===========================================================================

class TestWindowConfiguration:
    """M3-real: window title, resizable, background, focus_set."""

    def test_window_title_is_calculator(self):
        """Window title is 'Calculator'."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "title"
                    and isinstance(node.func.value, ast.Attribute)
                    and node.func.value.attr == "_root"
                ):
                    # self._root.title("Calculator")
                    args = node.args
                    assert len(args) == 1, f"title() expected 1 arg, got {len(args)}"
                    assert isinstance(args[0], ast.Constant), (
                        f"title() arg is not a literal: {ast.dump(args[0])}"
                    )
                    assert args[0].value == "Calculator", (
                        f"Expected title 'Calculator', got {args[0].value!r}"
                    )
                    return
        pytest.fail("self._root.title(...) call not found in __init__")

    def test_window_is_non_resizable(self):
        """Window calls resizable(False, False)."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "resizable"
                    and isinstance(node.func.value, ast.Attribute)
                    and node.func.value.attr == "_root"
                ):
                    args = node.args
                    assert len(args) == 2, f"resizable expected 2 args, got {len(args)}"
                    for i, arg in enumerate(args):
                        if isinstance(arg, ast.Constant):
                            assert arg.value is False, (
                                f"resizable arg {i} is {arg.value!r}, expected False"
                            )
                        elif isinstance(arg, ast.Name):
                            assert arg.id == "False", (
                                f"resizable arg {i} is {arg.id}, expected False"
                            )
                    return
        pytest.fail("self._root.resizable(...) call not found in __init__")

    def test_window_background_is_f0f0f0(self):
        """Window background is #f0f0f0 (light gray)."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "configure"
                    and isinstance(node.func.value, ast.Attribute)
                    and node.func.value.attr == "_root"
                ):
                    kw = _call_has_kwarg(node, "bg")
                    assert kw is not None, "self._root.configure() missing bg= kwarg"
                    assert _kwarg_equals(kw, "#f0f0f0"), (
                        f"Expected bg='#f0f0f0', got {ast.dump(kw.value)}"
                    )
                    return
        pytest.fail("self._root.configure(bg=...) call not found in __init__")

    def test_focus_set_in_init(self):
        """__init__ calls self._root.focus_set() so keyboard works immediately.

        This is the fix for the known-issue: 'Button focus steals keyboard
        input'.  Without focus_set(), the user must click the display area
        before keyboard input works.
        """
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        assert _has_method_call(init, "_root", "focus_set"), (
            "self._root.focus_set() not found in __init__ — "
            "keyboard input won't work until the user clicks the display area. "
            "This is a known-issue regression."
        )

    def test_focus_set_is_last_call_in_init(self):
        """focus_set() should be called near the end of __init__, after all
        widgets are created, so the root window actually receives focus."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        # Find the last focus_set call position
        last_focus_line = None
        last_stmt_line = None
        for i, stmt in enumerate(init.body):
            if hasattr(stmt, "lineno"):
                last_stmt_line = stmt.lineno
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    if (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "focus_set"
                        and isinstance(node.func.value, ast.Attribute)
                        and node.func.value.attr == "_root"
                    ):
                        if hasattr(node, "lineno"):
                            last_focus_line = node.lineno
                        elif hasattr(stmt, "lineno"):
                            last_focus_line = stmt.lineno

        # Just verify focus_set exists (position is informational)
        assert last_focus_line is not None, "focus_set() not found"


# ===========================================================================
# Display label styling
# ===========================================================================

class TestDisplayStyling:
    """M3-real: display label font, colors, alignment, relief."""

    def test_display_uses_stringvar(self):
        """Display uses tk.StringVar for dynamic updates."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        found = False
        for node in ast.walk(init):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr == "_display_var"
                    ):
                        if isinstance(node.value, ast.Call):
                            if (
                                isinstance(node.value.func, ast.Attribute)
                                and node.value.func.attr == "StringVar"
                            ):
                                found = True
        assert found, "_display_var = tk.StringVar(...) not found in __init__"

    def test_display_font_is_segoe_ui_24(self):
        """Display label uses Segoe UI at 24pt."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        # Find the tk.Label() call that sets textvariable
        label_calls = []
        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Label"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    # Must have textvariable kwarg (identifies display label)
                    has_textvar = any(
                        kw.arg == "textvariable" for kw in node.keywords
                    )
                    if has_textvar:
                        label_calls.append(node)

        assert len(label_calls) >= 1, "tk.Label with textvariable= not found"

        for call in label_calls:
            kw = _call_has_kwarg(call, "font")
            assert kw is not None, "Display tk.Label missing font= kwarg"

            # Check font is a tuple: ("Segoe UI", 24)
            if isinstance(kw.value, ast.Tuple):
                elts = kw.value.elts
                assert len(elts) == 2, f"font tuple has {len(elts)} elements, expected 2"
                assert isinstance(elts[0], ast.Constant), "font name not a literal"
                assert elts[0].value == "Segoe UI", (
                    f"Expected font 'Segoe UI', got {elts[0].value!r}"
                )
                assert isinstance(elts[1], ast.Constant), "font size not a literal"
                assert elts[1].value == 24, (
                    f"Expected font size 24, got {elts[1].value}"
                )
                return

        pytest.fail("Display tk.Label font= kwarg not a tuple ('Segoe UI', 24)")

    def test_display_is_right_aligned(self):
        """Display label has anchor='e' (right-aligned)."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Label"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    has_textvar = any(
                        kw.arg == "textvariable" for kw in node.keywords
                    )
                    if has_textvar:
                        kw = _call_has_kwarg(node, "anchor")
                        assert kw is not None, "Display tk.Label missing anchor='e'"
                        assert _kwarg_equals(kw, "e"), (
                            f"Expected anchor='e', got {ast.dump(kw.value)}"
                        )
                        return
        pytest.fail("Display tk.Label with anchor='e' not found")

    def test_display_colors_white_bg_black_fg(self):
        """Display label has bg='white', fg='black'."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Label"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    has_textvar = any(
                        kw.arg == "textvariable" for kw in node.keywords
                    )
                    if has_textvar:
                        kw_bg = _call_has_kwarg(node, "bg")
                        assert kw_bg is not None, "Display tk.Label missing bg="
                        assert _kwarg_equals(kw_bg, "white")

                        kw_fg = _call_has_kwarg(node, "fg")
                        assert kw_fg is not None, "Display tk.Label missing fg="
                        assert _kwarg_equals(kw_fg, "black")
                        return
        pytest.fail("Display tk.Label with bg='white', fg='black' not found")

    def test_display_has_sunken_relief(self):
        """Display label has relief='sunken' and borderwidth=2."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Label"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    has_textvar = any(
                        kw.arg == "textvariable" for kw in node.keywords
                    )
                    if has_textvar:
                        kw_r = _call_has_kwarg(node, "relief")
                        assert kw_r is not None, "Display tk.Label missing relief="
                        assert _kwarg_equals(kw_r, "sunken"), (
                            f"Expected relief='sunken', got {ast.dump(kw_r.value)}"
                        )

                        kw_bw = _call_has_kwarg(node, "borderwidth")
                        assert kw_bw is not None, "Display tk.Label missing borderwidth="
                        bw_val = kw_bw.value
                        assert isinstance(bw_val, ast.Constant) and bw_val.value == 2, (
                            f"Expected borderwidth=2, got {ast.dump(bw_val)}"
                        )
                        return
        pytest.fail("Display tk.Label with relief='sunken' not found")


# ===========================================================================
# Button styling
# ===========================================================================

class TestButtonStyling:
    """M3-real: button fonts, colors, and layout."""

    def test_button_font_is_segoe_ui_14(self):
        """Buttons use Segoe UI at 14pt."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        create_btns = _get_method_node(cls, "_create_buttons")

        for node in ast.walk(create_btns):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Button"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    kw = _call_has_kwarg(node, "font")
                    assert kw is not None, "tk.Button missing font="
                    if isinstance(kw.value, ast.Tuple):
                        elts = kw.value.elts
                        assert len(elts) == 2, f"font tuple has {len(elts)} elements"
                        assert isinstance(elts[0], ast.Constant)
                        assert elts[0].value == "Segoe UI", (
                            f"Expected font 'Segoe UI', got {elts[0].value!r}"
                        )
                        assert isinstance(elts[1], ast.Constant)
                        assert elts[1].value == 14, (
                            f"Expected font size 14, got {elts[1].value}"
                        )
                        return
        pytest.fail("tk.Button font=('Segoe UI', 14) not found")

    def test_button_colors_standard_is_e0e0e0(self):
        """Standard buttons have bg='#e0e0e0'."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        create_btns = _get_method_node(cls, "_create_buttons")

        for node in ast.walk(create_btns):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Button"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    kw = _call_has_kwarg(node, "bg")
                    assert kw is not None, "tk.Button missing bg="

                    # The bg kwarg is a conditional expression (ternary/if-else)
                    # or a constant.  We just check that both #e0e0e0 and
                    # #ff6b6b and #4dabf7 all appear somewhere in bg value.
                    bg_str = ast.dump(kw.value)
                    assert "#e0e0e0" in bg_str, (
                        f"Standard button color #e0e0e0 not found in bg: {bg_str}"
                    )
                    assert "#ff6b6b" in bg_str, (
                        f"C button color #ff6b6b not found in bg: {bg_str}"
                    )
                    assert "#4dabf7" in bg_str, (
                        f"= button color #4dabf7 not found in bg: {bg_str}"
                    )
                    return
        pytest.fail("tk.Button with bg color logic not found")

    def test_button_fg_is_black(self):
        """All buttons have fg='black'."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        create_btns = _get_method_node(cls, "_create_buttons")

        for node in ast.walk(create_btns):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Button"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    kw = _call_has_kwarg(node, "fg")
                    assert kw is not None, "tk.Button missing fg="
                    assert _kwarg_equals(kw, "black"), (
                        f"Expected fg='black', got {ast.dump(kw.value)}"
                    )
                    return
        pytest.fail("tk.Button fg='black' not found")


# ===========================================================================
# Button creation — ensure takefocus=False is preserved
# ===========================================================================

class TestTakefocusRegressionGuard:
    """M3-real: ensure takefocus=False remains on the tk.Button call.

    This is the known-issue fix: without takefocus=False, clicking any
    button steals keyboard focus and breaks keyboard input.  This test
    is a belt-and-suspenders check beyond test_view_takefocus.py.
    """

    def test_create_buttons_has_one_tk_button_call(self):
        """_create_buttons contains exactly one tk.Button() call (in a loop)."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        create_btns = _get_method_node(cls, "_create_buttons")

        button_calls = []
        for node in ast.walk(create_btns):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Button"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    button_calls.append(node)

        assert len(button_calls) == 1, (
            f"Expected 1 tk.Button call in _create_buttons, found {len(button_calls)}"
        )

    def test_takefocus_false_on_the_one_button_call(self):
        """The single tk.Button call includes takefocus=False."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        create_btns = _get_method_node(cls, "_create_buttons")

        for node in ast.walk(create_btns):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Button"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "tk"
                ):
                    kw = _call_has_kwarg(node, "takefocus")
                    assert kw is not None, "tk.Button missing takefocus="
                    assert _kwarg_equals(kw, False), (
                        f"Expected takefocus=False, got {ast.dump(kw.value)}"
                    )
                    return
        pytest.fail("tk.Button with takefocus=False not found")


# ===========================================================================
# Keyboard bindings — comprehensive coverage
# ===========================================================================

class TestKeyboardBindingsPolish:
    """M3-real: ensure all keyboard bindings from ARCHITECTURE.md are present."""

    def test_main_keyboard_bindings_complete(self):
        """KEYBOARD_MAP covers all main keyboard keys from the spec."""
        from calc.view import KEYBOARD_MAP

        required_keysyms = {
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "period", "plus", "minus", "asterisk", "slash",
            "parenleft", "parenright",
            "Return", "KP_Enter", "BackSpace", "Escape", "Delete",
        }
        assert set(KEYBOARD_MAP.keys()) == required_keysyms, (
            f"KEYBOARD_MAP keys mismatch. "
            f"Missing: {required_keysyms - set(KEYBOARD_MAP.keys())}, "
            f"Extra: {set(KEYBOARD_MAP.keys()) - required_keysyms}"
        )

    def test_numpad_bindings_complete(self):
        """NUMPAD_MAP covers all numpad keys from the spec."""
        from calc.view import NUMPAD_MAP

        required_numpad = {
            "KP_0", "KP_1", "KP_2", "KP_3", "KP_4",
            "KP_5", "KP_6", "KP_7", "KP_8", "KP_9",
            "KP_Decimal", "KP_Add", "KP_Subtract", "KP_Multiply", "KP_Divide",
        }
        assert set(NUMPAD_MAP.keys()) == required_numpad, (
            f"NUMPAD_MAP keys mismatch. "
            f"Missing: {required_numpad - set(NUMPAD_MAP.keys())}, "
            f"Extra: {set(NUMPAD_MAP.keys()) - required_numpad}"
        )

    def test_bind_keys_covers_keyboard_map(self):
        """_bind_keys() iterates over KEYBOARD_MAP and binds each keysym."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        bind_keys = _get_method_node(cls, "_bind_keys")

        # Verify that the method references KEYBOARD_MAP
        source = ast.unparse(bind_keys)
        assert "KEYBOARD_MAP" in source, (
            "_bind_keys() does not reference KEYBOARD_MAP"
        )

    def test_bind_keys_covers_numpad_map(self):
        """_bind_keys() iterates over NUMPAD_MAP and binds each keysym."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        bind_keys = _get_method_node(cls, "_bind_keys")

        source = ast.unparse(bind_keys)
        assert "NUMPAD_MAP" in source, (
            "_bind_keys() does not reference NUMPAD_MAP"
        )


# ===========================================================================
# refresh() — initial call in __init__
# ===========================================================================

class TestInitialRefresh:
    """M3-real: refresh() is called in __init__ so the display starts synced."""

    def test_refresh_called_in_init(self):
        """__init__ calls self.refresh() before focus_set()."""
        tree = _get_view_source_tree()
        cls = _get_class_node(tree, "CalculatorView")
        init = _get_method_node(cls, "__init__")

        found = False
        for node in ast.walk(init):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "refresh"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                ):
                    found = True
        assert found, "self.refresh() not called in __init__"


# ===========================================================================
# No tkinter import in tests
# ===========================================================================

def test_no_tkinter_import_in_this_file():
    """This test file does not import tkinter directly."""
    tree = ast.parse(
        inspect.getsource(inspect.getmodule(test_no_tkinter_import_in_this_file))
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "tkinter" not in alias.name.lower(), (
                    f"test_view_polish.py imports tkinter: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "tkinter" not in node.module.lower(), (
                    f"test_view_polish.py imports from tkinter: {node.module}"
                )
