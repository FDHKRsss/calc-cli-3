"""Quick AST check of view.py M3-real features."""
import ast

source = open("calc/view.py", "r", encoding="utf-8").read()
tree = ast.parse(source)

# Find CalculatorView class
cv = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "CalculatorView"][0]

# Find __init__ and _create_buttons
init = [item for item in cv.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"][0]
create_btns = [item for item in cv.body if isinstance(item, ast.FunctionDef) and item.name == "_create_buttons"][0]

# Check for focus_set in __init__
found_focus = False
for sub in ast.walk(init):
    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
        if sub.func.attr == "focus_set":
            found_focus = True
            val = sub.func.value
            if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Attribute):
                print(f"focus_set: self.{val.value.attr}.{val.attr} at line {sub.lineno}")
            break
print(f"focus_set found: {found_focus}")

# Check for grid ipady in _create_buttons (button grid)
found_btn_ipady = False
for sub in ast.walk(create_btns):
    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
        if sub.func.attr == "grid":
            for kw in sub.keywords:
                if kw.arg == "ipady":
                    found_btn_ipady = True
                    if isinstance(kw.value, ast.Constant):
                        print(f"button grid ipady={kw.value.value} at line {sub.lineno}")
print(f"button ipady found: {found_btn_ipady}")

# Check module docstring
mod_doc = ast.get_docstring(tree)
has_stub = "(stub)" in (mod_doc or "")
print(f"module docstring has '(stub)': {has_stub}")

# Check class docstring
cls_doc = ast.get_docstring(cv)
has_keyboard = "keyboard" in (cls_doc or "").lower() and "immediately" in (cls_doc or "").lower()
print(f"class docstring mentions keyboard immediately: {has_keyboard}")
