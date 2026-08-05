"""Headless controller — state machine for the calculator (stub).

In the stub pass, press() echoes keys to the display, "=" shows "STUB",
and C/backspace work trivially.  In the real pass this becomes a full
state machine with the behaviors described in ARCHITECTURE.md.
"""


class CalculatorController:
    """Manages expression state and display, delegating to the engine.

    Attributes:
        expression: The internal ASCII expression (e.g. "1+2*3").
        display: What the view should show (Unicode operators, or result).
    """

    def __init__(self) -> None:
        self._expression: str = ""
        self._display: str = ""

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

    # ------------------------------------------------------------------
    # press()
    # ------------------------------------------------------------------

    def press(self, key: str) -> None:
        """Process a key/button press.

        Args:
            key: One of "0"–"9", ".", "+", "-", "*", "/", "(", ")",
                 "=", "C", "backspace".
        """
        if key == "C":
            self._expression = ""
            self._display = ""
        elif key == "backspace":
            self._expression = self._expression[:-1]
            self._display = self._display[:-1]
        elif key == "=":
            # Stub: always show "STUB" — real pass delegates to engine
            self._display = "STUB"
        else:
            self._expression += key
            self._display += self._to_display(key)
