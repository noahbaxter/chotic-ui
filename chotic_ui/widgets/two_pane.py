"""
TwoPane - a generic two-column picker.

Left pane drives the right pane: the active left row selects what the right
pane lists. Tab switches the focused pane, the cursor moves within the focused
pane, typing filters the right pane (when enabled), Enter activates the focused
row. The caller supplies rows + callbacks; the widget owns the box layout,
focus, per-pane cursor/scroll, and the right-pane filter query.

The widget knows nothing about what the rows mean. Each row is a tuple:

    (render(focused: bool, cursor: bool) -> str, value, selectable: bool)

`render` is called per visible row and returns the (possibly ANSI-coloured)
label for that row, told whether its pane has focus and whether it sits under
the cursor, so the caller draws its own markers. Non-selectable rows
(``selectable=False``, e.g. section headers) are skipped by the cursor.
"""

import sys
import shutil

from ..primitives import (
    Colors, getch, cbreak_noecho,
    KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_TAB, KEY_BACKSPACE, KEY_SPACE,
)
from ..primitives.terminal import strip_ansi, visible_len, pad_to
from ..components import (
    print_header, box_row,
    BOX_TL, BOX_TR, BOX_BL, BOX_BR, BOX_H, BOX_V, BOX_TL_DIV, BOX_TR_DIV,
)


def body_height(term_lines, n_rows, min_rows):
    """Visible body rows: enough for the widest pane and the rows on screen,
    capped to terminal height and floored at ``min_rows``.

    >>> body_height(40, 30, 5)
    26
    >>> body_height(24, 30, 5)
    10
    >>> body_height(24, 1, 5)
    5
    >>> body_height(40, 3, 8)
    8
    """
    return max(min_rows, min(term_lines - 14, max(n_rows, 1)))


class TwoPane:
    """Two-column picker built from caller-supplied rows and callbacks.

    Args:
        title: bold heading drawn in the top band.
        subtitle: muted text shown beside the title.
        left_rows: ``() -> list[Row]`` rows for the left pane.
        right_rows: ``(active_left_value) -> list[Row]`` rows for the right pane,
            rebuilt whenever the active left row changes. ``active_left_value`` is
            the value of the left row under the left cursor (or None if empty).
        on_left_enter: ``(value) -> None`` Enter on a focused left row (after the
            first Enter, which just moves focus to the right pane).
        on_right_enter: ``(value) -> None`` Enter on a focused right row.
        right_filterable: when True, typing (with the right pane focused) builds a
            filter query applied to the right rows via ``search_key``.
        search_key: ``(value) -> str`` the text a right row is filtered on. Default
            strips ANSI from the row's rendered (unfocused) label.
        keys: ``{char: callback() -> "return"|None}`` extra hotkeys; if a callback
            returns ``"return"`` ``run()`` returns that char.
        footer: hint line drawn under the box (caller-styled). A default is used
            when empty.
        left_width: width of the left column in characters.
        left_enter_focuses_right: when True (default), Enter/Space on a left row
            moves focus to the right pane (drill-down, as the model picker wants).
            When False, focus stays on the left pane (multi-select toggling).

    A Row is ``(render(focused, cursor) -> str, value, selectable)``.
    """

    def __init__(self, *, title="", subtitle="", left_rows, right_rows,
                 on_left_enter=None, on_right_enter=None, right_filterable=True,
                 search_key=None, keys=None, footer="", left_width=22,
                 left_header="", left_enter_focuses_right=True):
        self.title = title
        self.subtitle = subtitle
        self.left_header = left_header
        self._left_rows = left_rows
        self._right_rows = right_rows
        self._on_left_enter = on_left_enter
        self._on_right_enter = on_right_enter
        self.right_filterable = right_filterable
        self._search_key = search_key
        self.keys = keys or {}
        self.footer = footer
        self.left_width = left_width
        self.left_enter_focuses_right = left_enter_focuses_right

        self.focus = "left"
        self._left_cursor = 0
        self._cursor = 0   # right pane cursor
        self._scroll = 0   # right pane scroll
        self._query = ""

    # --- row helpers ---

    @staticmethod
    def _selectable_indices(rows):
        return [i for i, r in enumerate(rows) if r[2]]

    def _active_left_value(self, left):
        if not left:
            return None
        i = max(0, min(self._left_cursor, len(left) - 1))
        if not left[i][2]:                       # snap off a non-selectable row
            sel = self._selectable_indices(left)
            if sel:
                i = min(sel, key=lambda j: abs(j - i))
        return left[i][1]

    def _filtered_right(self, right):
        if not (self.right_filterable and self._query):
            return right
        q = self._query.lower().strip()
        terms = q.split()
        out = []
        for render, value, selectable in right:
            if not selectable:
                continue   # headers hidden while filtering
            if self._search_key:
                hay = self._search_key(value).lower()
            else:
                hay = strip_ansi(render(False, False)).lower()
            if all(t in hay for t in terms):
                out.append((render, value, selectable))
        return out

    # --- rendering ---

    def _frame(self, left, right, term):
        w = max(72, min(term[0] - 2, 110))
        rows_h = body_height(term[1], max(len(left), len(right)), len(left))
        inner = w - 4
        left_w = self.left_width
        right_w = inner - left_w - 3            # " │ " between columns
        c = Colors.PRIMARY
        lines = [box_row(BOX_TL, BOX_H, BOX_TR, w, c)]

        def row(content):
            pad = inner - visible_len(content)
            lines.append(f"{c}{BOX_V}{Colors.RESET} {content}{' ' * max(0, pad)} {c}{BOX_V}{Colors.RESET}")

        def two(lt, rt):
            row(f"{pad_to(lt, left_w)} {Colors.DIM}{BOX_V}{Colors.RESET} {pad_to(rt, right_w)}")

        if self.subtitle:
            row(f"{Colors.BOLD}{self.title}{Colors.RESET}  {Colors.MUTED}{self.subtitle}{Colors.RESET}")
        else:
            row(f"{Colors.BOLD}{self.title}{Colors.RESET}")
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        n = len(right)
        if self.right_filterable:
            filt = (f"{Colors.PRIMARY}Filter:{Colors.RESET} {self._query}{Colors.PRIMARY}▌{Colors.RESET}"
                    if self.focus == "right"
                    else f"{Colors.MUTED}(type to filter){Colors.RESET}")
        else:
            filt = ""
        count = f"{Colors.MUTED}{n}{Colors.RESET}"
        pad = right_w - visible_len(filt) - visible_len(count)
        two(f"{Colors.BOLD}{self.left_header}{Colors.RESET}", f"{filt}{' ' * max(1, pad)}{count}")
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        end = min(n, self._scroll + rows_h)
        for r in range(rows_h):
            # left column
            if r < len(left):
                render, _, _ = left[r]
                lt = render(self.focus == "left", r == self._left_cursor)
            else:
                lt = ""
            # right column: scrolled window
            idx = self._scroll + r
            if r == 0 and self._scroll > 0:
                rt = f"{Colors.MUTED}  ▲ {self._scroll} above{Colors.RESET}"
            elif r == rows_h - 1 and end < n:
                rt = f"{Colors.MUTED}  ▼ {n - end} below{Colors.RESET}"
            elif idx < n:
                render, _, sel = right[idx]
                rt = pad_to(render(self.focus == "right", idx == self._cursor and sel), right_w)
            else:
                rt = ""
            two(lt, rt)

        lines.append(box_row(BOX_BL, BOX_H, BOX_BR, w, c))
        if self.footer:
            lines.append(self.footer)
        else:
            lines.append(f"  {Colors.PRIMARY}Tab{Colors.MUTED} switch pane  {Colors.PRIMARY}↑/↓{Colors.MUTED} move  "
                         f"{Colors.PRIMARY}Enter{Colors.MUTED} set  {Colors.PRIMARY}Esc{Colors.MUTED} done  "
                         f"{Colors.DIM}(type to filter the right){Colors.RESET}")

        out = sys.__stdout__ if sys.__stdout__ else sys.stdout
        out.write("\033[H\033[J")
        print_header()
        out.write("\n".join(lines).replace("\n", "\033[K\n") + "\033[J\033[3J")
        out.flush()

    def render_once(self):
        """Build the current rows and draw one frame (no input). Returns the
        (left, right) row lists used, for headless inspection."""
        left = self._left_rows()
        self._left_cursor = max(0, min(self._left_cursor, len(left) - 1)) if left else 0
        right = self._filtered_right(self._right_rows(self._active_left_value(left)))
        term = shutil.get_terminal_size((80, 24))
        rows_h = body_height(term[1], max(len(left), len(right)), len(left))
        self._clamp(right, rows_h)
        self._frame(left, right, term)
        return left, right

    def _clamp(self, right, rows_h):
        sel = self._selectable_indices(right)
        if not sel:
            self._cursor = 0
        elif self._cursor not in sel:
            self._cursor = min(sel, key=lambda i: abs(i - self._cursor))
        if self._cursor < self._scroll:
            self._scroll = self._cursor
        elif self._cursor >= self._scroll + rows_h:
            self._scroll = self._cursor - rows_h + 1
        self._scroll = max(0, min(self._scroll, max(0, len(right) - rows_h)))

    # --- loop ---

    def run(self):
        """Show the picker. Loops until Esc (returns None) or a hotkey callback
        returns ``"return"`` (returns that hotkey char)."""
        with cbreak_noecho():
            while True:
                left = self._left_rows()
                self._left_cursor = max(0, min(self._left_cursor, len(left) - 1)) if left else 0
                right = self._filtered_right(self._right_rows(self._active_left_value(left)))
                term = shutil.get_terminal_size((80, 24))
                rows_h = body_height(term[1], max(len(left), len(right)), len(left))
                self._clamp(right, rows_h)
                self._frame(left, right, term)

                key = getch(return_special_keys=True)
                if key == KEY_ESC:
                    return None
                if key == KEY_TAB:
                    self.focus = "right" if self.focus == "left" else "left"
                elif key == KEY_UP:
                    if self.focus == "left":
                        self._move_left(left, -1)
                    else:
                        self._move_right(right, -1)
                elif key == KEY_DOWN:
                    if self.focus == "left":
                        self._move_left(left, +1)
                    else:
                        self._move_right(right, +1)
                elif key == KEY_ENTER:
                    if self.focus == "left":
                        if self._on_left_enter:
                            self._on_left_enter(self._active_left_value(left))
                        if self.left_enter_focuses_right:
                            self.focus = "right"
                    elif self._cursor < len(right) and right[self._cursor][2]:
                        if self._on_right_enter:
                            self._on_right_enter(right[self._cursor][1])
                elif key == KEY_BACKSPACE:
                    if self.focus == "right" and self.right_filterable:
                        self._query = self._query[:-1]
                        self._cursor = self._scroll = 0
                elif key == KEY_SPACE:
                    if self.focus == "right" and self.right_filterable:
                        self._query += " "
                        self._cursor = self._scroll = 0
                    elif self.focus == "right" and not self.right_filterable:
                        if self._cursor < len(right) and right[self._cursor][2] and self._on_right_enter:
                            self._on_right_enter(right[self._cursor][1])
                    elif self.focus == "left" and self._on_left_enter:
                        self._on_left_enter(self._active_left_value(left))
                elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                    if key in self.keys:
                        if self.keys[key]() == "return":
                            return key
                    elif self.right_filterable:
                        self.focus = "right"
                        self._query += key
                        self._cursor = self._scroll = 0

    def _move_left(self, left, delta):
        sel = self._selectable_indices(left)
        if not sel:
            return
        cur = self._left_cursor
        if delta < 0:
            above = [i for i in sel if i < cur]
            self._left_cursor = above[-1] if above else cur
        else:
            below = [i for i in sel if i > cur]
            self._left_cursor = below[0] if below else cur
        self._cursor = self._scroll = 0
        self._query = ""

    def _move_right(self, right, delta):
        sel = self._selectable_indices(right)
        if not sel:
            return
        cur = self._cursor
        if delta < 0:
            above = [i for i in sel if i < cur]
            self._cursor = above[-1] if above else cur
        else:
            below = [i for i in sel if i > cur]
            self._cursor = below[0] if below else cur
