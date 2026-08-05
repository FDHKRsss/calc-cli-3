"""Headless controller — state machine for the calculator.

Manages expression state and display, delegating evaluation to the engine.
"""

from calc.engine import evaluate


class CalculatorController:
    """Manages expression state and display, delegating to the engine.

    Attributes:
        expression: The internal ASCII expression (e.g. "1+2*3").
        display: What the view should show (Unicode operators, or result).
    """

    def __init__(self) -> None:
        self._expression: str = ""
        self._display: str = ""
        self._result_shown: bool = False

    @property
    def expression(self) -> str:
        """Internal ASCII expression, read-only."""
        return self._expression

    @property
    def display(self) -> str:
        """What the view should render, read-only."""
        return self._display

    # ------------------------------------------------------------------
    # Key mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_display(key: str) -> str:
        """Convert an ASCII operator key to its Unicode display form."""
        if key == "*":
            return "\u00d7"  # ×
        if key == "/":
            return "\u00f7"  # ÷
        return key

    @staticmethod
    def _current_number_has_dot(expr: str) -> bool:
        """Check if the rightmost number in *expr* already has a decimal point."""
        for ch in reversed(expr):
            if ch == ".":
                return True
            if ch in "+-*/()":
                return False
        return False

    # ------------------------------------------------------------------
    # press()
    # ------------------------------------------------------------------

    def press(self, key: str) -> None:
        """Process a key/button press.

        Args:
            key: One of "0"–"9", ".", "+", "-", "*", "/", "(", ")",
                 "=", "C", "backspace".
        """
        # --- C (clear) ---
        if key == "C":
            self._expression = ""
            self._display = ""
            self._result_shown = False
            return

        # --- backspace ---
        if key == "backspace":
            if self._result_shown or self._display == "Error":
                # After a result or error, backspace clears everything.
                self._expression = ""
                self._display = ""
                self._result_shown = False
            else:
                self._expression = self._expression[:-1]
                self._display = self._display[:-1]
            return

        # --- equals ---
        if key == "=":
            result = evaluate(self._expression)
            self._display = result
            self._result_shown = True
            return

        # === Handle result_shown / error state BEFORE processing other keys ===

        if self._result_shown:
            if key == ")":
                # ')' after any result (success or error): clear and ignore.
                # Can't begin an expression with ')'.
                self._expression = ""
                self._display = ""
                self._result_shown = False
                return
            if self._display == "Error":
                # Error shown: clear everything, then process the key normally
                # (operators will be ignored because expression is now empty).
                self._expression = ""
                self._display = ""
                self._result_shown = False
            elif key in "0123456789.(":
                # Digit, decimal, or '(' after a successful result:
                # start a fresh expression.
                self._expression = ""
                self._display = ""
                self._result_shown = False
            elif key in "+-*/":
                # Operator after a successful result: continue from result.
                # The display holds the result as a plain number string (ASCII-safe).
                self._expression = self._display
                self._display = self._expression
                self._result_shown = False

        # === Now process the key against the current expression state ===

        # --- digits ---
        if key in "0123456789":
            self._expression += key
            self._display += key
            return

        # --- decimal point ---
        if key == ".":
            if self._current_number_has_dot(self._expression):
                return  # already a decimal point in the current number
            self._expression += "."
            self._display += "."
            return

        # --- operators ---
        if key in "+-*/":
            if not self._expression:
                return  # can't start expression with an operator
            if self._expression[-1] in "+-*/":
                # Replace the last operator.
                self._expression = self._expression[:-1] + key
                self._display = self._display[:-1] + self._to_display(key)
            elif self._expression[-1] == "(":
                return  # can't put operator right after '('
            else:
                self._expression += key
                self._display += self._to_display(key)
            return

        # --- parentheses ---
        if key == "(":
            self._expression += "("
            self._display += "("
            return

        if key == ")":
            self._expression += ")"
            self._display += ")"
            return
