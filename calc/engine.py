"""Pure arithmetic engine — shunting-yard algorithm.

Implements a full tokenizer → RPN → evaluator pipeline.
"""

import operator
from typing import Union

# ---------------------------------------------------------------------------
# Operator tables
# ---------------------------------------------------------------------------

_PRECEDENCE: dict[str, int] = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
}

_OPS: dict[str, callable] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(expression: str) -> str:
    """Evaluate an arithmetic expression string.

    Args:
        expression: ASCII operators (+, -, *, /), parentheses, decimals.

    Returns:
        Result string (e.g. "14", "3.5") or "Error".  Never raises.
    """
    try:
        tokens = _tokenize(expression)
        if not tokens:
            return "Error"
        rpn = _shunting_yard(tokens)
        if rpn is None:
            return "Error"
        result = _eval_rpn(rpn)
        if result is None:
            return "Error"
        return _format_result(result)
    except Exception:
        return "Error"


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def _tokenize(expr: str) -> list[str]:
    """Convert an expression string into a flat list of tokens.

    Returns an empty list for any invalid input (bad characters,
    multiple adjacent decimal points in a single number, etc.).
    """
    tokens: list[str] = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        # whitespace is silently skipped
        if ch.isspace():
            i += 1
            continue

        # digits: accumulate a whole number (digits + at most one dot)
        if ch.isdigit():
            start = i
            has_dot = False
            while i < n and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    if has_dot:
                        return []              # multiple dots in one number
                    has_dot = True
                i += 1
            num_str = expr[start:i]
            if num_str == ".":
                return []                      # isolated dot left over
            tokens.append(num_str)
            continue

        # leading dot: ".5" style decimal
        if ch == ".":
            start = i
            i += 1
            while i < n and expr[i].isdigit():
                i += 1
            num_str = expr[start:i]
            tokens.append(num_str)
            continue

        # operators and parentheses
        if ch in "+-*/()":
            tokens.append(ch)
            i += 1
            continue

        # anything else is invalid
        return []

    return tokens


# ---------------------------------------------------------------------------
# Shunting-yard (infix → RPN)
# ---------------------------------------------------------------------------

def _shunting_yard(tokens: list[str]) -> Union[list[str], None]:
    """Convert infix token list to RPN.

    Returns None when the token sequence is structurally invalid
    (mismatched parentheses, consecutive operators, empty parens,
    trailing operator, etc.).
    """
    output: list[str] = []
    op_stack: list[str] = []
    expect_number = True          # next token must be a number or '('

    for token in tokens:
        if _is_number(token):
            if not expect_number:
                return None       # two numbers in a row, or number after ')'
            output.append(token)
            expect_number = False

        elif token == "(":
            if not expect_number:
                return None       # e.g. "2(3" — missing operator
            op_stack.append(token)
            # expect_number stays True (after '(' we expect a number or '(')

        elif token == ")":
            if expect_number:
                return None       # "()" or "+)"
            while op_stack and op_stack[-1] != "(":
                output.append(op_stack.pop())
            if not op_stack:
                return None       # unmatched ')'
            op_stack.pop()        # discard '('
            expect_number = False

        elif token in _PRECEDENCE:
            if expect_number:
                return None       # leading / consecutive operator, or "(" then operator
            while (op_stack and op_stack[-1] != "(" and
                   _PRECEDENCE[op_stack[-1]] >= _PRECEDENCE[token]):
                output.append(op_stack.pop())
            op_stack.append(token)
            expect_number = True

    # After consuming all tokens we must NOT be waiting for a number
    if expect_number and tokens:
        return None               # trailing operator or empty expression

    # Pop remaining operators — any leftover '(' means mismatch
    while op_stack:
        if op_stack[-1] == "(":
            return None
        output.append(op_stack.pop())

    return output


# ---------------------------------------------------------------------------
# RPN evaluator
# ---------------------------------------------------------------------------

def _eval_rpn(rpn: list[str]) -> Union[float, None]:
    """Evaluate an RPN token list.

    Returns the float result, or None for any error condition
    (most notably division by zero).
    """
    stack: list[float] = []

    for token in rpn:
        if _is_number(token):
            stack.append(float(token))
        else:
            if len(stack) < 2:
                return None          # malformed RPN
            b = stack.pop()
            a = stack.pop()
            if token == "/" and b == 0:
                return None          # division by zero
            try:
                result = _OPS[token](a, b)
            except (ArithmeticError, ValueError):
                return None
            stack.append(result)

    if len(stack) != 1:
        return None
    return stack[0]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_number(token: str) -> bool:
    """Return True when *token* can be parsed as a float."""
    try:
        float(token)
        return True
    except ValueError:
        return False


def _format_result(value: float) -> str:
    """Format a float as a display-friendly string.

    Whole numbers lose the decimal point; fractional numbers are
    rendered with up to 15 digits, trailing zeros stripped.
    """
    if value == int(value):
        return str(int(value))
    # Use fixed-point formatting so we don't get scientific notation.
    s = f"{value:.15f}".rstrip("0").rstrip(".")
    if not s:
        s = "0"
    return s
