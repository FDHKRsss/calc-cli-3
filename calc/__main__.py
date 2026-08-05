"""Entry point for ``python -m calc``.

Creates the controller and view, then starts the Tkinter main loop.
"""

from calc.controller import CalculatorController
from calc.view import CalculatorView


def main() -> None:
    """Build and run the calculator application."""
    controller = CalculatorController()
    view = CalculatorView(controller)
    view.run()


if __name__ == "__main__":
    main()
