# Known issues

_Recurring walls/gotchas and how to get past them. One bullet each._

- **Button focus steals keyboard input** (M3-real check): Clicking any Tkinter `Button` widget gives it keyboard focus, after which pressing Enter/Space can double-fire (once from the root `<Return>` binding, once from the Button's built-in activation) and typed digits may not route cleanly to root bindings. **Fix** (already applied in stub): set `takefocus=False` on every button. M3-real must preserve this and ensure root-level keyboard bindings work immediately on launch without requiring a click on the display area.
