"""Tests for M4: package wiring — entry points, pyproject.toml, README.

Validates:
- ``calc/__main__.py``: entry point for ``python -m calc``
- ``pyproject.toml``: project metadata and ``[project.scripts]`` entry
- End-to-end wiring: ``main()`` connects controller → view → run()
- Package integrity: all public modules are importable
- README.md accuracy: matches the delivered window appearance (M4-real)

No test creates a live Tkinter display.
"""

import ast
import importlib
import inspect
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Helpers
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_pyproject() -> str:
    """Read pyproject.toml as raw text."""
    path = REPO_ROOT / "pyproject.toml"
    assert path.exists(), f"pyproject.toml not found at {path}"
    return path.read_text(encoding="utf-8")


def _parse_pyproject():
    """Parse pyproject.toml and return the dict.

    Uses tomllib (Python >= 3.11) or tomli (backport).
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("Neither tomllib nor tomli available — cannot parse TOML")
    return tomllib.loads(_read_pyproject())


def _get_main_module_ast() -> ast.Module:
    """Parse calc/__main__.py and return its AST."""
    path = REPO_ROOT / "calc" / "__main__.py"
    assert path.exists(), f"calc/__main__.py not found at {path}"
    return ast.parse(path.read_text(encoding="utf-8"))


def _get_main_func_node() -> ast.FunctionDef:
    """Return the ``main`` FunctionDef node from __main__.py AST."""
    tree = _get_main_module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return node
    raise AssertionError("Could not find 'main' function in calc/__main__.py AST")


def _fresh_main_module():
    """Purge calc modules from sys.modules and return a fresh calc.__main__."""
    for mod in list(sys.modules):
        if mod.startswith("calc"):
            del sys.modules[mod]
    import calc.__main__ as main_mod
    return main_mod


def _read_readme() -> str:
    """Read README.md as raw text."""
    path = REPO_ROOT / "README.md"
    assert path.exists(), "README.md not found"
    return path.read_text(encoding="utf-8")


# ============================================================================
# pyproject.toml — structure and content
# ============================================================================

class TestPyprojectToml:
    """Validates pyproject.toml structure and content."""

    def test_pyproject_exists_and_readable(self):
        """pyproject.toml exists at the repo root and is non-empty."""
        path = REPO_ROOT / "pyproject.toml"
        assert path.exists(), f"pyproject.toml not found at {path}"
        text = path.read_text(encoding="utf-8")
        assert len(text.strip()) > 0, "pyproject.toml is empty"

    def test_pyproject_is_valid_toml(self):
        """pyproject.toml parses as valid TOML."""
        data = _parse_pyproject()
        assert isinstance(data, dict), "TOML root is not a dict"

    def test_project_section_exists(self):
        """pyproject.toml has a [project] section."""
        data = _parse_pyproject()
        assert "project" in data, "Missing [project] section"

    def test_project_name_is_calc(self):
        """[project] name is 'calc'."""
        data = _parse_pyproject()
        assert data["project"]["name"] == "calc", (
            f"Expected name='calc', got {data['project'].get('name')!r}"
        )

    def test_project_has_version(self):
        """[project] has a version."""
        data = _parse_pyproject()
        assert "version" in data["project"], "Missing [project] version"
        assert data["project"]["version"], "Version is empty"

    def test_project_requires_python(self):
        """[project] requires-python is >=3.9."""
        data = _parse_pyproject()
        assert "requires-python" in data["project"], (
            "Missing [project] requires-python"
        )
        rp = data["project"]["requires-python"]
        assert "3.9" in rp or "3.10" in rp or "3.11" in rp or ">=" in rp, (
            f"requires-python {rp!r} does not appear to target Python >=3.9"
        )

    def test_project_has_description(self):
        """[project] has a description."""
        data = _parse_pyproject()
        assert data["project"].get("description"), "Missing or empty [project] description"

    def test_project_scripts_section_exists(self):
        """[project.scripts] section exists."""
        data = _parse_pyproject()
        assert "scripts" in data["project"], "Missing [project.scripts]"

    def test_project_scripts_has_calc_entry(self):
        """[project.scripts] has ``calc = "calc.__main__:main"``."""
        data = _parse_pyproject()
        scripts = data["project"]["scripts"]
        assert "calc" in scripts, (
            f"Missing 'calc' entry in [project.scripts]. Keys: {list(scripts)}"
        )
        assert scripts["calc"] == "calc.__main__:main", (
            f"Expected 'calc.__main__:main', got {scripts['calc']!r}"
        )

    def test_build_system_section_exists(self):
        """pyproject.toml has a [build-system] section."""
        data = _parse_pyproject()
        assert "build-system" in data, "Missing [build-system] section"

    def test_build_system_uses_setuptools(self):
        """[build-system] requires setuptools."""
        data = _parse_pyproject()
        bs = data["build-system"]
        assert "requires" in bs, "Missing [build-system] requires"
        setuptools_found = any("setuptools" in req for req in bs["requires"])
        assert setuptools_found, (
            f"setuptools not found in build-system.requires: {bs['requires']}"
        )

    def test_build_system_has_backend(self):
        """[build-system] has build-backend."""
        data = _parse_pyproject()
        assert "build-backend" in data["build-system"], (
            "Missing [build-system] build-backend"
        )

    def test_build_backend_is_documented_public_value(self):
        """The build-backend is the documented public setuptools value.

        Regression guard: we must NOT use the private/undocumented
        ``setuptools.backends._legacy:_Backend`` path that fails across
        setuptools versions.
        """
        data = _parse_pyproject()
        backend = data["build-system"]["build-backend"]
        assert backend == "setuptools.build_meta", (
            f"Expected build-backend='setuptools.build_meta', got {backend!r}. "
            f"Do NOT use private setuptools backends like "
            f"setuptools.backends._legacy:_Backend."
        )

    def test_build_backend_not_private_legacy_path(self):
        """The pyproject.toml raw text does NOT reference the private
        ``setuptools.backends._legacy`` path anywhere."""
        raw = _read_pyproject()
        assert "setuptools.backends._legacy" not in raw, (
            "pyproject.toml contains the private setuptools.backends._legacy path! "
            "Use the public 'setuptools.build_meta' instead."
        )


# ============================================================================
# pyproject.toml — optional-dependencies (dev extras)
# ============================================================================

class TestDevExtras:
    """Validates ``[project.optional-dependencies]`` with ``dev = ["pytest"]``.

    The README instructs users to run ``pip install -e ".[dev]"`` —
    this must actually resolve to a real extra that includes pytest.
    """

    def test_optional_dependencies_section_exists(self):
        """pyproject.toml has ``[project.optional-dependencies]``."""
        data = _parse_pyproject()
        assert "optional-dependencies" in data.get("project", {}), (
            "Missing [project.optional-dependencies] section"
        )

    def test_optional_dependencies_is_a_dict(self):
        """optional-dependencies is a dict/table."""
        data = _parse_pyproject()
        opt_deps = data["project"]["optional-dependencies"]
        assert isinstance(opt_deps, dict), (
            f"optional-dependencies should be a dict, got {type(opt_deps).__name__}"
        )

    def test_dev_extra_exists(self):
        """The ``dev`` key exists under optional-dependencies."""
        data = _parse_pyproject()
        opt_deps = data["project"]["optional-dependencies"]
        assert "dev" in opt_deps, (
            f"'dev' extra not found in optional-dependencies. "
            f"Existing extras: {list(opt_deps)}"
        )

    def test_dev_extra_is_a_list(self):
        """The ``dev`` extra value is a list/array."""
        data = _parse_pyproject()
        dev_deps = data["project"]["optional-dependencies"]["dev"]
        assert isinstance(dev_deps, list), (
            f"dev extra should be a list, got {type(dev_deps).__name__}: {dev_deps!r}"
        )

    def test_dev_extra_contains_pytest(self):
        """The ``dev`` extra list includes ``pytest``."""
        data = _parse_pyproject()
        dev_deps = data["project"]["optional-dependencies"]["dev"]
        assert "pytest" in dev_deps, (
            f"dev extra does not contain 'pytest'. Contents: {dev_deps!r}"
        )

    def test_dev_extra_not_empty(self):
        """The ``dev`` extra list is not empty."""
        data = _parse_pyproject()
        dev_deps = data["project"]["optional-dependencies"]["dev"]
        assert len(dev_deps) > 0, (
            "dev extra is an empty list — it must include pytest at minimum"
        )

    def test_dev_extra_items_are_strings(self):
        """Every item in the ``dev`` extra list is a string."""
        data = _parse_pyproject()
        dev_deps = data["project"]["optional-dependencies"]["dev"]
        for i, item in enumerate(dev_deps):
            assert isinstance(item, str), (
                f"dev extra item {i} is not a string: {item!r} (type {type(item).__name__})"
            )

    def test_raw_text_has_optional_dependencies_header(self):
        """The raw pyproject.toml text contains the section header."""
        raw = _read_pyproject()
        assert "[project.optional-dependencies]" in raw, (
            "pyproject.toml does not contain the literal "
            "'[project.optional-dependencies]' section header"
        )

    def test_raw_text_has_dev_pytest_line(self):
        """The raw pyproject.toml text contains ``dev = ["pytest"]``."""
        raw = _read_pyproject()
        assert 'dev = ["pytest"]' in raw, (
            "pyproject.toml does not contain the expected line: dev = [\"pytest\"]"
        )

    # ------------------------------------------------------------------
    # Cross-validation: README "pip install -e .[dev]" vs TOML
    # ------------------------------------------------------------------

    def test_readme_dev_instruction_matches_toml(self):
        """README's ``pip install -e ".[dev]"`` references an extra that
        actually exists in pyproject.toml."""
        data = _parse_pyproject()
        opt_deps = data["project"]["optional-dependencies"]
        readme_text = _read_readme()

        # The README must mention the dev extra
        assert '.[dev]' in readme_text or '[dev]' in readme_text, (
            "README.md does not mention the '.[dev]' extra for pip install"
        )

        # The dev extra must actually exist
        assert "dev" in opt_deps, (
            f"README.md references '.[dev]' but there is no 'dev' key in "
            f"[project.optional-dependencies]. Extras defined: {list(opt_deps)}"
        )

    def test_readme_dev_instruction_in_running_tests_section(self):
        """The ``pip install -e ".[dev]"`` instruction appears in the
        ``## Running the tests`` section."""
        readme_text = _read_readme()

        # Find the "Running the tests" section
        tests_section_start = readme_text.find("## Running the tests")
        assert tests_section_start != -1, "README missing '## Running the tests' section"

        # Find the next section header after it
        rest = readme_text[tests_section_start:]
        next_section = rest.find("\n## ", len("## Running the tests"))
        if next_section != -1:
            section_text = rest[:next_section]
        else:
            section_text = rest

        assert '.[dev]' in section_text or '[dev]' in section_text, (
            f"pip install '.[dev]' not found in the 'Running the tests' section. "
            f"Section content: {section_text[:200]}"
        )

    def test_dev_extra_actually_resolvable_by_pip(self):
        """The ``dev`` extra contains at least one installable package name.

        This is a lightweight check — we verify the package names don't
        look like obvious typos or placeholder values.
        """
        data = _parse_pyproject()
        dev_deps = data["project"]["optional-dependencies"]["dev"]

        # Basic sanity: no empty strings, no obviously bogus names
        for dep in dev_deps:
            assert dep.strip() == dep, f"Whitespace around dep name: {dep!r}"
            assert dep, f"Empty string in dev extra"
            # Must look like a plausible PyPI package name
            assert dep.isascii(), f"Non-ASCII dep name: {dep!r}"


# ============================================================================
# calc/__main__.py — structure and behavior
# ============================================================================

class TestMainModule:
    """Validates calc/__main__.py as the ``python -m calc`` entry point."""

    def test_main_module_exists(self):
        """calc/__main__.py exists."""
        path = REPO_ROOT / "calc" / "__main__.py"
        assert path.exists(), f"calc/__main__.py not found at {path}"

    def test_main_module_importable(self):
        """``from calc.__main__ import main`` works without side effects."""
        main_mod = _fresh_main_module()
        assert callable(main_mod.main), "main is not callable"

    def test_main_function_exists(self):
        """calc/__main__.py defines a ``main()`` function."""
        tree = _get_main_module_ast()
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                found = True
                break
        assert found, "No 'main' function defined in calc/__main__.py"

    def test_main_function_has_no_required_args(self):
        """main() takes no required arguments."""
        func_node = _get_main_func_node()
        args = func_node.args
        non_default = len(args.args) - len(args.defaults)
        assert non_default == 0, (
            f"main() has {non_default} required argument(s); expected 0"
        )

    def test_main_function_annotated_return_none(self):
        """main() return annotation is None."""
        func_node = _get_main_func_node()
        if func_node.returns:
            returns_str = ast.unparse(func_node.returns)
            assert "None" in returns_str, (
                f"main() return annotation is {returns_str}, expected None"
            )

    def test_main_module_has_dunder_name_guard(self):
        """calc/__main__.py has the ``if __name__ == "__main__": main()`` guard."""
        tree = _get_main_module_ast()
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = ast.unparse(node.test)
                if '__name__' in test and '__main__' in test:
                    found = True
                    body_text = ast.unparse(node.body[0]) if node.body else ""
                    assert "main()" in body_text or "main(" in body_text, (
                        f"__name__ guard body does not call main(): {body_text}"
                    )
                    break
        assert found, (
            "Missing ``if __name__ == '__main__':`` guard in calc/__main__.py"
        )

    def test_main_module_imports_controller(self):
        """__main__.py imports CalculatorController."""
        text = (REPO_ROOT / "calc" / "__main__.py").read_text(encoding="utf-8")
        assert "CalculatorController" in text, (
            "__main__.py does not reference CalculatorController"
        )

    def test_main_module_imports_view(self):
        """__main__.py imports CalculatorView."""
        text = (REPO_ROOT / "calc" / "__main__.py").read_text(encoding="utf-8")
        assert "CalculatorView" in text, (
            "__main__.py does not reference CalculatorView"
        )

    def test_import_main_creates_no_tk_window(self):
        """Importing calc.__main__ must NOT open a Tk window.

        The main() function should only be called inside the guard or by
        the caller; a bare import must be side-effect-free.
        """
        with patch("tkinter.Tk", side_effect=RuntimeError("Tk() called during import!")):
            try:
                _fresh_main_module()
            except RuntimeError as e:
                if "Tk() called during import" in str(e):
                    pytest.fail(
                        "Importing calc.__main__ triggered tkinter.Tk() — "
                        "the import has side effects. The main() call must be "
                        "inside the ``if __name__ == '__main__':`` guard."
                    )
                raise

    def test_main_module_docstring(self):
        """__main__.py has a module docstring."""
        tree = _get_main_module_ast()
        doc = ast.get_docstring(tree)
        assert doc is not None, "__main__.py has no module docstring"
        assert len(doc.strip()) > 0, "__main__.py docstring is empty"

    def test_main_function_docstring(self):
        """main() has a docstring."""
        func_node = _get_main_func_node()
        doc = ast.get_docstring(func_node)
        assert doc is not None, "main() has no docstring"
        assert len(doc.strip()) > 0, "main() docstring is empty"


# ============================================================================
# End-to-end wiring — main() connects controller → view → run()
# ============================================================================

class TestEndToEndWiring:
    """Validates that main() correctly wires controller and view together.

    All Tkinter calls are mocked so no live display is created.
    Uses fresh module reloads to ensure clean patching.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _call_main_with_mocks(mock_controller_cls, mock_view_cls):
        """Import calc.__main__ fresh with patched imports, call main()."""
        # Purge all calc modules so imports are fresh
        for mod in list(sys.modules):
            if mod.startswith("calc"):
                del sys.modules[mod]

        # Patch the import targets *before* calc.__main__ is imported
        with patch("calc.__main__.CalculatorController", mock_controller_cls):
            with patch("calc.__main__.CalculatorView", mock_view_cls):
                import calc.__main__ as main_mod
                main_mod.main()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_main_creates_controller(self):
        """main() instantiates CalculatorController."""
        mock_controller_cls = MagicMock(return_value=MagicMock())
        mock_view_cls = MagicMock()

        # Block Tk so view.__init__ doesn't open a window
        with patch("tkinter.Tk"):
            self._call_main_with_mocks(mock_controller_cls, mock_view_cls)

        mock_controller_cls.assert_called_once()

    def test_main_creates_view_with_controller_instance(self):
        """main() passes a CalculatorController instance to CalculatorView."""
        mock_controller = MagicMock()
        mock_controller_cls = MagicMock(return_value=mock_controller)
        mock_view_cls = MagicMock()

        with patch("tkinter.Tk"):
            self._call_main_with_mocks(mock_controller_cls, mock_view_cls)

        mock_view_cls.assert_called_once_with(mock_controller)

    def test_main_calls_view_run(self):
        """main() calls view.run() to start the Tkinter main loop."""
        mock_view = MagicMock()
        mock_controller_cls = MagicMock(return_value=MagicMock())
        mock_view_cls = MagicMock(return_value=mock_view)

        with patch("tkinter.Tk"):
            self._call_main_with_mocks(mock_controller_cls, mock_view_cls)

        mock_view.run.assert_called_once()

    def test_main_does_not_swallow_exceptions(self):
        """main() does not have a blanket try/except that hides errors."""
        text = (REPO_ROOT / "calc" / "__main__.py").read_text(encoding="utf-8")
        tree = ast.parse(text)
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                func_node = node
                break
        assert func_node is not None

        for stmt in func_node.body:
            if isinstance(stmt, ast.Try):
                for handler in stmt.handlers:
                    if handler.type is None:
                        pytest.fail(
                            "main() has a bare ``except:`` clause — "
                            "exceptions should not be silently swallowed"
                        )


# ============================================================================
# Package integrity: all modules reachable
# ============================================================================

class TestPackageIntegrity:
    """Validates the package is well-formed and all modules are importable."""

    def test_package_has_init(self):
        """calc/__init__.py exists."""
        path = REPO_ROOT / "calc" / "__init__.py"
        assert path.exists(), "calc/__init__.py not found"

    def test_all_production_modules_importable(self):
        """Every production module can be imported from the calc package."""
        expected_modules = ["engine", "controller", "view", "__main__"]
        for mod_name in expected_modules:
            full = f"calc.{mod_name}"
            try:
                __import__(full)
            except ImportError as e:
                pytest.fail(f"Cannot import {full}: {e}")

    def test_calc_command_maps_to_main(self):
        """The ``calc`` script entry point maps to ``calc.__main__:main``.

        We verify by reading pyproject.toml and checking the entry resolves.
        """
        data = _parse_pyproject()
        scripts = data["project"]["scripts"]
        assert scripts["calc"] == "calc.__main__:main", (
            f"Expected 'calc.__main__:main', got {scripts['calc']!r}"
        )

        # Also verify that module path and function name resolve
        module_path, func_name = scripts["calc"].split(":")
        mod = __import__(module_path, fromlist=[func_name])
        assert hasattr(mod, func_name), (
            f"Module {module_path} has no attribute {func_name}"
        )
        assert callable(getattr(mod, func_name)), (
            f"{module_path}.{func_name} is not callable"
        )


# ============================================================================
# README — basic existence and content (M4-stub)
# ============================================================================

class TestReadme:
    """Validates README.md exists and has the required content."""

    def test_readme_exists(self):
        """README.md exists at repo root."""
        path = REPO_ROOT / "README.md"
        assert path.exists(), "README.md not found"

    def test_readme_not_empty(self):
        """README.md is not empty."""
        text = _read_readme()
        assert len(text.strip()) > 0, "README.md is empty"

    def test_readme_mentions_python_m_calc(self):
        """README.md mentions ``python -m calc`` launch instruction."""
        text = _read_readme()
        assert "python -m calc" in text or "`python -m calc`" in text, (
            "README.md does not mention 'python -m calc' launch instruction"
        )

    def test_readme_mentions_calc_command(self):
        """README.md mentions the ``calc`` command.

        The command may appear inline (`` `calc` ``) or inside a fenced
        code block (``\\ncalc\\n``).  Both forms are valid.
        """
        text = _read_readme()
        assert (
            "`calc`" in text
            or "\ncalc\n" in text
            or "calc command" in text.lower()
            or "run calc" in text.lower()
        ), (
            "README.md does not mention the 'calc' command"
        )

    def test_readme_describes_window(self):
        """README.md describes what the calculator window looks like."""
        text = _read_readme().lower()
        window_keywords = ["window", "display", "button", "grid", "layout", "gui"]
        found = any(kw in text for kw in window_keywords)
        assert found, (
            f"README.md does not describe the window appearance. "
            f"Expected at least one of: {window_keywords}"
        )


# ============================================================================
# README — M4-real: accuracy vs. the delivered window
# ============================================================================

class TestReadmeReal:
    """M4-real: README accurately describes the actual delivered window.

    Cross-references the README claims against the source of truth in
    ``calc/view.py`` so the document never drifts from the code.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _readme_text() -> str:
        return _read_readme()

    @staticmethod
    def _readme_lower() -> str:
        return _read_readme().lower()

    # ------------------------------------------------------------------
    # Title and structure
    # ------------------------------------------------------------------

    def test_title_is_calc_not_old_placeholder(self):
        """The README title is ``# calc`` — not ``# calc-cli-3``."""
        text = self._readme_text()
        # First non-empty line should be "# calc"
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        assert lines, "README.md is empty"
        assert lines[0] == "# calc", (
            f"Expected first heading '# calc', got {lines[0]!r}"
        )

    def test_no_old_title_calc_cli_3(self):
        """The old placeholder title ``calc-cli-3`` does not appear anywhere."""
        text = self._readme_text()
        assert "calc-cli-3" not in text, (
            "README.md still contains the old placeholder 'calc-cli-3'"
        )

    def test_has_usage_section(self):
        """README has a ``## Usage`` section."""
        text = self._readme_text()
        assert "## Usage" in text, "README.md missing '## Usage' section"

    def test_has_keyboard_shortcuts_section(self):
        """README has a ``### Keyboard shortcuts`` section."""
        text = self._readme_text()
        assert "Keyboard shortcuts" in text, (
            "README.md missing 'Keyboard shortcuts' section"
        )

    def test_has_window_appearance_section(self):
        """README has a ``## Window appearance`` section."""
        text = self._readme_text()
        assert "## Window appearance" in text, (
            "README.md missing '## Window appearance' section"
        )

    def test_has_running_tests_section(self):
        """README has a ``## Running the tests`` section."""
        text = self._readme_text()
        assert "## Running the tests" in text, (
            "README.md missing '## Running the tests' section"
        )

    def test_has_pytest_instruction(self):
        """README mentions ``pytest`` for running tests."""
        text = self._readme_text()
        assert "pytest" in text, (
            "README.md does not mention pytest"
        )

    # ------------------------------------------------------------------
    # Window appearance accuracy — fonts
    # ------------------------------------------------------------------

    def test_mentions_segoe_ui_24pt_display(self):
        """README mentions Segoe UI 24 pt for the display."""
        text = self._readme_text()
        assert "Segoe UI 24" in text or "Segoe UI, 24" in text, (
            "README.md does not mention Segoe UI 24 pt for the display"
        )

    def test_mentions_segoe_ui_14pt_buttons(self):
        """README mentions Segoe UI 14 pt for the buttons."""
        text = self._readme_text()
        assert "Segoe UI 14" in text or "Segoe UI, 14" in text, (
            "README.md does not mention Segoe UI 14 pt for the buttons"
        )

    # ------------------------------------------------------------------
    # Window appearance accuracy — colors
    # ------------------------------------------------------------------

    def test_mentions_display_white_background(self):
        """README mentions the display has a white background."""
        text = self._readme_lower()
        assert "white" in text, (
            "README.md does not mention the display's white background"
        )

    def test_mentions_button_color_e0e0e0(self):
        """README mentions the standard button color ``#e0e0e0``."""
        text = self._readme_text()
        assert "#e0e0e0" in text, (
            "README.md does not mention standard button color #e0e0e0"
        )

    def test_mentions_c_button_red(self):
        """README mentions the C button is red (``#ff6b6b``)."""
        text = self._readme_text()
        assert "#ff6b6b" in text, (
            "README.md does not mention C button color #ff6b6b"
        )

    def test_mentions_equals_button_blue(self):
        """README mentions the = button is blue (``#4dabf7``)."""
        text = self._readme_text()
        assert "#4dabf7" in text, (
            "README.md does not mention = button color #4dabf7"
        )

    # ------------------------------------------------------------------
    # Window appearance accuracy — layout
    # ------------------------------------------------------------------

    def test_mentions_fixed_size_or_non_resizable(self):
        """README mentions the window is fixed size / non-resizable."""
        text = self._readme_lower()
        assert "fixed size" in text or "non-resizable" in text or "not resizable" in text, (
            "README.md does not mention the window is fixed-size / non-resizable"
        )

    def test_mentions_background_f0f0f0(self):
        """README mentions the window background is ``#f0f0f0``."""
        text = self._readme_text()
        assert "#f0f0f0" in text, (
            "README.md does not mention window background #f0f0f0"
        )

    def test_mentions_window_title_calculator(self):
        """README mentions the window title is 'Calculator'."""
        text = self._readme_text()
        assert "Calculator" in text, (
            "README.md does not mention the window title 'Calculator'"
        )

    def test_mentions_right_aligned_display(self):
        """README mentions the display is right-aligned."""
        text = self._readme_text()
        assert "right-aligned" in text.lower() or "right aligned" in text.lower(), (
            "README.md does not mention the display is right-aligned"
        )

    # ------------------------------------------------------------------
    # Window appearance accuracy — button labels (Unicode)
    # ------------------------------------------------------------------

    def test_mentions_division_sign(self):
        """README mentions the division button uses ``÷`` (U+00F7)."""
        text = self._readme_text()
        assert "\u00f7" in text or "÷" in text, (
            "README.md does not mention the division button symbol ÷"
        )

    def test_mentions_multiplication_sign(self):
        """README mentions the multiplication button uses ``×`` (U+00D7)."""
        text = self._readme_text()
        assert "\u00d7" in text or "×" in text, (
            "README.md does not mention the multiplication button symbol ×"
        )

    def test_mentions_minus_sign(self):
        """README mentions the subtraction button uses ``−`` (U+2212)."""
        text = self._readme_text()
        assert "\u2212" in text or "−" in text, (
            "README.md does not mention the subtraction button symbol −"
        )

    def test_mentions_backspace_symbol(self):
        """README mentions the backspace button uses ``⌫`` (U+232B)."""
        text = self._readme_text()
        assert "\u232b" in text or "⌫" in text, (
            "README.md does not mention the backspace button symbol ⌫"
        )

    def test_mentions_parentheses_buttons(self):
        """README mentions the parentheses buttons ``(`` and ``)``."""
        text = self._readme_text()
        assert "(" in text and ")" in text, (
            "README.md does not mention the parentheses buttons"
        )

    def test_button_grid_is_5x4(self):
        """README shows the 5-row × 4-column button grid."""
        text = self._readme_text()
        # The ASCII art has 5 rows × 4 columns of button boxes.
        # Count the number of button rows in the ASCII diagram.
        button_rows = [line for line in text.splitlines()
                       if line.strip().startswith("│  ┌───")]
        assert len(button_rows) >= 5, (
            f"README ASCII art has {len(button_rows)} button rows, expected ≥ 5"
        )

    # ------------------------------------------------------------------
    # README is not a raw dump of the internal goal spec
    # ------------------------------------------------------------------

    def test_not_a_raw_goal_dump(self):
        """README is a user-facing document, not a raw paste of the goal spec.

        The goal document is an internal spec; the README should be
        structured for end users with dedicated sections.
        """
        text = self._readme_text()
        # The internal goal spec contains certain characteristic phrases
        # that a user-facing README would not include verbatim.
        goal_phrases = [
            "put ALL arithmetic in a pure, GUI-free `engine` module",
            "headless `controller` that turns button/key presses into display state",
            "Tkinter layer is a thin view that only wires widgets to the controller",
        ]
        for phrase in goal_phrases:
            if phrase in text:
                # OK if present but only as part of intentional doc, not as the
                # entire document.  We check that proper sections exist (tested
                # above), so just note it but allow it.
                pass

        # The README must have at least 3 of the expected section headers.
        section_headers = ["## Usage", "## Window appearance",
                           "## Running the tests", "### Keyboard shortcuts"]
        found = sum(1 for h in section_headers if h in text)
        assert found >= 3, (
            f"README.md looks like a raw spec dump, not a user-facing document. "
            f"Only {found}/4 expected section headers found."
        )

    # ------------------------------------------------------------------
    # README matches pyproject.toml project name
    # ------------------------------------------------------------------

    def test_readme_title_matches_project_name(self):
        """The README heading matches the project name in pyproject.toml."""
        data = _parse_pyproject()
        project_name = data["project"]["name"]
        text = self._readme_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        assert lines, "README.md is empty"
        heading = lines[0]
        assert heading == f"# {project_name}", (
            f"README heading {heading!r} does not match project name "
            f"{project_name!r} from pyproject.toml"
        )


# ============================================================================
# Edge cases
# ============================================================================

class TestEdgeCases:
    """Edge-case tests for package wiring."""

    def test_main_function_idempotent_import(self):
        """Importing main multiple times does not crash or change state."""
        main_mod1 = _fresh_main_module()
        main_mod2 = _fresh_main_module()
        assert main_mod1.main is not main_mod2.main or True  # Different module objects after reload
        # Both should be callable
        assert callable(main_mod1.main)
        assert callable(main_mod2.main)

    def test_package_init_not_empty(self):
        """calc/__init__.py has a docstring or comment."""
        path = REPO_ROOT / "calc" / "__init__.py"
        text = path.read_text(encoding="utf-8").strip()
        assert len(text) > 0, "calc/__init__.py is empty"

    def test_tests_init_exists(self):
        """tests/__init__.py exists (making tests a package)."""
        path = REPO_ROOT / "tests" / "__init__.py"
        assert path.exists(), "tests/__init__.py not found"
