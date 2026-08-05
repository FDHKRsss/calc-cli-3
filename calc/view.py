"""Tkinter GUI — thin view layer.

Creates the calculator window with display and button grid.  Wires
mouse clicks and keyboard events to the headless controller.  The
view is a pure Tkinter shell — all logic lives in the controller
and engine modules.
"""

import tkinter as tk

from calc.controller import CalculatorController

# Button layout: each row is a list of (label, controller_key) tuples.
BUTTONS: list[list[tuple[str, str]]] = [
    [("(", "("), (")", ")"), ("C", "C"), ("\u232b", "backspace")],
    [("7", "7"), ("8", "8"), ("9", "9"), ("\u00f7", "/")],
    [("4", "4"), ("5", "5"), ("6", "6"), ("\u00d7", "*")],
    [("1", "1"), ("2", "2"), ("3", "3"), ("\u2212", "-")],
    [(".", "."), ("0", "0"), ("=", "="), ("+", "+")],
]

# Keyboard mapping: tkinter keysym → controller key.
KEYBOARD_MAP: dict[str, str] = {
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "period": ".",
    "plus": "+",
    "minus": "-",
    "asterisk": "*",
    "slash": "/",
    "parenleft": "(",
    "parenright": ")",
    "Return": "=",
    "KP_Enter": "=",
    "BackSpace": "backspace",
    "Escape": "C",
    "Delete": "C",
}

# Also support numpad keys — same keysym prefix "KP_".
NUMPAD_MAP: dict[str, str] = {
    "KP_0": "0",
    "KP_1": "1",
    "KP_2": "2",
    "KP_3": "3",
    "KP_4": "4",
    "KP_5": "5",
    "KP_6": "6",
    "KP_7": "7",
    "KP_8": "8",
    "KP_9": "9",
    "KP_Decimal": ".",
    "KP_Add": "+",
    "KP_Subtract": "-",
    "KP_Multiply": "*",
    "KP_Divide": "/",
}


class CalculatorView:
    """Tkinter GUI window for the calculator.

    Creates the window, display, and button grid.  Wires mouse clicks
    and keyboard events to the headless controller.  Keyboard input
    works immediately on launch — no click required.
    """

    def __init__(self, controller: CalculatorController) -> None:
        self._controller = controller

        # ---- window ----
        self._root = tk.Tk()
        self._root.title("Calculator")
        self._root.resizable(False, False)
        self._root.configure(bg="#f0f0f0")

        # ---- display ----
        self._display_var = tk.StringVar(value="")
        self._display_label = tk.Label(
            self._root,
            textvariable=self._display_var,
            anchor="e",
            font=("Segoe UI", 24),
            bg="white",
            fg="black",
            relief="sunken",
            borderwidth=2,
        )
        self._display_label.grid(
            row=0, column=0, columnspan=4,
            sticky="ew", padx=4, pady=(8, 4), ipady=6,
        )

        # ---- buttons ----
        self._create_buttons()

        # ---- keyboard bindings ----
        self._bind_keys()

        # Make the first row (display) and button columns expand
        self._root.grid_rowconfigure(0, weight=0)
        for r in range(1, len(BUTTONS) + 1):
            self._root.grid_rowconfigure(r, weight=1)
        for c in range(4):
            self._root.grid_columnconfigure(c, weight=1)

        # Initial refresh
        self.refresh()

        # Ensure keyboard input works immediately on launch.
        self._root.focus_set()

    # ------------------------------------------------------------------
    # Button creation
    # ------------------------------------------------------------------

    def _create_buttons(self) -> None:
        """Create all calculator buttons from the BUTTONS layout."""
        for row_idx, row in enumerate(BUTTONS, start=1):
            for col_idx, (label, key) in enumerate(row):
                btn = tk.Button(
                    self._root,
                    text=label,
                    font=("Segoe UI", 14),
                    command=lambda k=key: self._on_press(k),
                    bg="#e0e0e0" if label not in ("C", "=") else (
                        "#ff6b6b" if label == "C" else "#4dabf7"
                    ),
                    fg="black",
                    relief="raised",
                    borderwidth=2,
                    takefocus=False,
                )
                btn.grid(
                    row=row_idx, column=col_idx,
                    sticky="nsew", padx=2, pady=2, ipady=4,
                )

    # ------------------------------------------------------------------
    # Keyboard bindings
    # ------------------------------------------------------------------

    def _bind_keys(self) -> None:
        """Bind keyboard events to controller presses."""
        # Main keyboard keys
        for keysym, action in KEYBOARD_MAP.items():
            self._root.bind(f"<{keysym}>", lambda e, k=action: self._on_press(k))
        # Numpad keys
        for keysym, action in NUMPAD_MAP.items():
            self._root.bind(f"<{keysym}>", lambda e, k=action: self._on_press(k))

    # ------------------------------------------------------------------
    # Press handling
    # ------------------------------------------------------------------

    def _on_press(self, key: str) -> None:
        """Process a button click or keypress, refresh the display."""
        self._controller.press(key)
        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Read controller.display and update the display widget."""
        self._display_var.set(self._controller.display)

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self._root.mainloop()
