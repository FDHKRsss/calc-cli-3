"""Pure arithmetic engine — shunting-yard algorithm (stub).

In the stub pass, evaluate() returns canned results based on trivial
input matching.  In the real pass this will be replaced with a full
tokenizer → RPN → evaluator pipeline.
"""


def evaluate(expression: str) -> str:
    """Evaluate an arithmetic expression string.

    Args:
        expression: ASCII operators (+, -, *, /), parentheses, decimals.

    Returns:
        Result string (e.g. "14", "3.5") or "Error".  Never raises.
    """
    canned: dict[str, str] = {
        "1+1": "2",
        "2*3": "6",
        "1/0": "Error",
    }
    return canned.get(expression, "STUB")
