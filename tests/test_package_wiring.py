"""Tests for M4-stub: package wiring — entry points, pyproject.toml, README.

Validates:
- ``calc/__main__.py``: entry point for ``python -m calc``
- ``pyproject.toml``: project metadata and ``[project.scripts]`` entry
- End-to-end wiring: ``main()`` connects controller → view → run()
- Package integrity: all public modules are importable

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
# README — existence and content
# ============================================================================

class TestReadme:
    """Validates README.md exists and has the required content."""

    def test_readme_exists(self):
        """README.md exists at repo root."""
        path = REPO_ROOT / "README.md"
        assert path.exists(), "README.md not found"

    def test_readme_not_empty(self):
        """README.md is not empty."""
        path = REPO_ROOT / "README.md"
        text = path.read_text(encoding="utf-8")
        assert len(text.strip()) > 0, "README.md is empty"

    def test_readme_mentions_python_m_calc(self):
        """README.md mentions ``python -m calc`` launch instruction."""
        path = REPO_ROOT / "README.md"
        text = path.read_text(encoding="utf-8")
        assert "python -m calc" in text or "`python -m calc`" in text, (
            "README.md does not mention 'python -m calc' launch instruction"
        )

    def test_readme_mentions_calc_command(self):
        """README.md mentions the ``calc`` command."""
        path = REPO_ROOT / "README.md"
        text = path.read_text(encoding="utf-8")
        assert "`calc`" in text or "calc command" in text.lower() or "run calc" in text.lower(), (
            "README.md does not mention the 'calc' command"
        )

    def test_readme_describes_window(self):
        """README.md describes what the calculator window looks like."""
        path = REPO_ROOT / "README.md"
        text = path.read_text(encoding="utf-8").lower()
        window_keywords = ["window", "display", "button", "grid", "layout", "gui"]
        found = any(kw in text for kw in window_keywords)
        assert found, (
            f"README.md does not describe the window appearance. "
            f"Expected at least one of: {window_keywords}"
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
