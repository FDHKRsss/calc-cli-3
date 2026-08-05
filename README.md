# calc

A desktop calculator app in the style of the Windows Calculator, built with
Python and Tkinter (standard library — no extra dependencies).

## Usage

Launch the calculator from the command line:

```bash
calc
```

Or equivalently:

```bash
python -m calc
```

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| 0–9, numpad 0–9 | Digits |
| `.`, Numpad `.` | Decimal point |
| `+`, `-`, `*`, `/` | Operators (numpad versions also work) |
| `(`, `)` | Parentheses |
| Enter, Numpad Enter | Equals (`=`) |
| Backspace | Backspace (`⌫`) |
| Escape, Delete | Clear (`C`) |

## Window appearance

```
┌─────────────────────────────────────┐
│ Calculator                    _ □ X │
├─────────────────────────────────────┤
│                                     │
│                           (display) │
│                                     │
│  ┌───┐  ┌───┐  ┌─────┐  ┌─────┐    │
│  │ ( │  │ ) │  │  C  │  │  ⌫  │    │
│  └───┘  └───┘  └─────┘  └─────┘    │
│  ┌───┐  ┌───┐  ┌───┐  ┌─────┐      │
│  │ 7 │  │ 8 │  │ 9 │  │  ÷  │      │
│  └───┘  └───┘  └───┘  └─────┘      │
│  ┌───┐  ┌───┐  ┌───┐  ┌─────┐      │
│  │ 4 │  │ 5 │  │ 6 │  │  ×  │      │
│  └───┘  └───┘  └───┘  └─────┘      │
│  ┌───┐  ┌───┐  ┌───┐  ┌─────┐      │
│  │ 1 │  │ 2 │  │ 3 │  │  −  │      │
│  └───┘  └───┘  └───┘  └─────┘      │
│  ┌───┐  ┌───┐  ┌─────┐  ┌─────┐    │
│  │ . │  │ 0 │  │  =  │  │  +  │    │
│  └───┘  └───┘  └─────┘  └─────┘    │
│                                     │
└─────────────────────────────────────┘
```

- **Display** — right-aligned, Segoe UI 24 pt, white background.
- **Buttons** — Segoe UI 14 pt, light gray background (`#e0e0e0`).
  - `C` (clear) — red (`#ff6b6b`).
  - `=` (equals) — blue (`#4dabf7`).
- **Window** — fixed size, title "Calculator", background `#f0f0f0`.

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

All tests are headless — no display is required.
