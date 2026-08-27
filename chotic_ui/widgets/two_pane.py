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
the cursor. The widget OWNS the cursor/focus indicator (a marker, row highlight,
bold, or accent colour, chosen via ``cursor_style``); the caller draws only its
own data marks (e.g. a selection dot). Non-selectable rows (``selectable=False``,
e.g. section headers) are skipped by the cursor.
"""

import sys
import shutil

from ..primitives import (
    Colors, getch, getch_with_timeout, cbreak_noecho,
    KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_TAB, KEY_BACKSPACE, KEY_SPACE,
)
from ..primitives.terminal import strip_ansi, visible_len, pad_to, truncate_ansi
from ..components import (
    print_header, header_height, box_row,
    BOX_TL, BOX_TR, BOX_BL, BOX_BR, BOX_H, BOX_V, BOX_TL_DIV, BOX_TR_DIV,
)


# Cursor-state for a visible row.
FOCUS_CURSOR = "focus"   # cursor row in the currently focused pane
FAINT_CURSOR = "faint"   # left pane's active row while focus is on the right
NONE = "none"


def _restyle(text, code):
    """Re-apply an ANSI `code` across a string that contains full resets, so the
    style spans the whole row (and its padding) despite embedded Colors.RESET.

    >>> _restyle("a" + Colors.RESET + "b", "<C>") == "<C>a" + Colors.RESET + "<C>b" + Colors.RESET
    True
    """
    return code + text.replace(Colors.RESET, Colors.RESET + code) + Colors.RESET


# Rows the frame spends on the box itself: top edge, title band, the rule under
# it, the pane-header band, the rule under that, and the bottom edge.
BOX_LINES = 6
# Fallback when no banner is configured: box + one footer line.
CHROME_LINES = BOX_LINES + 1
MIN_BODY = 3


def body_height(term_lines, n_rows, min_rows=0, chrome=CHROME_LINES):
    """Visible body rows: as tall as the tallest pane, never taller than the
    window can show.

    ``min_rows`` is a floor, not an override -- applying it with an outer max()
    grew the box past the window and pushed the banner off the top. ``chrome``
    is every row the frame spends on something other than body, banner included;
    guessing it low scrolls the terminal, which reads as flicker.

    >>> body_height(40, 30, 5, chrome=17)
    23
    >>> body_height(24, 30, 5, chrome=17)      # clamped to the window, not 30
    7
    >>> body_height(24, 1, 5, chrome=17)
    5
    >>> body_height(24, 40, 20, chrome=17)     # floor never beats the window
    7
    >>> body_height(12, 40, 0, chrome=17)      # never below the floor
    3
    """
    available = max(MIN_BODY, term_lines - chrome)
    return max(MIN_BODY, min(available, max(n_rows, min_rows, 1)))


class TwoPane:
    """Two-column picker built from caller-supplied rows and callbacks.

    Args:
        title: bold heading drawn in the top band.
        subtitle: muted text shown beside the title.
        left_rows: ``() -> list[Row]`` rows for the left pane.
        right_rows: ``(active_left_value, query) -> list[Row]`` rows for the right pane,
            rebuilt whenever the active left row changes. ``active_left_value`` is
            the value of the left row under the left cursor (or None if empty).
        on_left_enter: ``(value) -> None`` Enter on a focused left row (after the
            first Enter, which just moves focus to the right pane). Returning
            anything other than None ends ``run()`` and becomes its return value,
            so a row can hand an action back to the caller.
        on_right_enter: ``(value) -> None`` Enter on a focused right row. Returning
            anything other than None ends ``run()`` and becomes its return value.
        right_filterable: when True, typing (with the right pane focused) builds a
            filter query applied to the right rows via ``search_key``.
        search_key: ``(value) -> str`` the text a right row is filtered on. Default
            strips ANSI from the row's rendered (unfocused) label.
        keys: ``{char: callback() -> "return"|None}`` extra hotkeys; if a callback
            returns ``"return"`` ``run()`` returns that char.
        footer: hint line drawn under the box (caller-styled), or a ``() -> str``
            callable recomputed each frame (e.g. a live plan line). A default is
            used when empty.
        right_header: bold label for the right pane's header band; when set it
            replaces the filter/count line (use for a fixed-purpose right pane
            like settings).
        show_count: when False, hide the right-row count in the header band
            (meaningless for fixed lists like settings).
        left_width: width of the left column in characters.
        left_enter_focuses_right: when True (default), Enter/Space on a left row
            moves focus to the right pane (drill-down, as the model picker wants).
            When False, focus stays on the left pane (multi-select toggling).
        cursor_style: how the focused row is indicated. One of "marker" (a ``▸``/
            ``•`` glyph, the default), "highlight" (slate row background), "bold",
            or "color" (accent the whole row). All reserve the same 2-col gutter.
        header_style: how the active pane header is emphasised. One of "chip" (an
            inverted reverse-video chip, the default), "bold", or "color".
        detail: ``(focused_right_value) -> str`` optional; its result is drawn as
            a full-width line under the box (above the footer), so the focused
            right row's full text stays visible without being cramped in-column.

    A Row is ``(render(focused, cursor) -> str, value, selectable)``.
    """

    def __init__(self, *, title="", subtitle="", left_rows, right_rows,
                 on_left_enter=None, on_right_enter=None, right_filterable=True,
                 search_key=None, keys=None, footer="", left_width=22,
                 left_header="", right_header="", show_count=True,
                 left_enter_focuses_right=True,
                 cursor_style="marker", header_style="chip", detail=None,
                 update_callback=None, refresh_interval_ms=250,
                 on_left_space=None, space_activates=False, footer_lines=1,
                 fill_height=False):
        self.title = title
        self.subtitle = subtitle
        self.left_header = left_header
        self.right_header = right_header
        self.show_count = show_count
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
        self.cursor_style = cursor_style
        self.header_style = header_style
        self._detail = detail
        # Called on each idle poll; return True to repaint. Rows are rebuilt
        # every frame, so a repaint is all a live-data screen needs.
        self.update_callback = update_callback
        self.refresh_interval_ms = refresh_interval_ms
        # Space on a left row, when it means something different from Enter
        # (toggle vs drill in). Falls back to on_left_enter when unset.
        self._on_left_space = on_left_space
        # Give Space to the focused row even on a filterable pane. A list whose
        # primary verb is "toggle" needs it more than the filter needs spaces.
        self.space_activates = space_activates
        # How many lines the caller's footer occupies, so the body can give them
        # back to the window instead of shoving the banner off the top.
        self.footer_lines = footer_lines
        # Tallest content seen so far. The box sizes to this rather than to the
        # current right pane, so switching to a drive with three setlists does
        # not collapse the frame and switching back does not grow it again.
        # Size the body to the window rather than to the rows. A screen that is
        # returned to repeatedly wants a frame that stays put; sizing to content
        # means it comes back smaller than the window that holds it.
        self.fill_height = fill_height
        # First frame of a run clears the screen; later ones overwrite in place.
        # Clearing every time flickers, never clearing leaves whatever the
        # screen we just came back from left behind.
        self._painted = False

        self.focus = "left"
        self._left_cursor = 0
        self._cursor = 0   # right pane cursor
        self._scroll = 0   # right pane scroll
        self._query = ""

    # --- row helpers ---

    @staticmethod
    def _selectable_indices(rows):
        return [i for i, r in enumerate(rows) if r[2]]

    def _clamp_left(self, left):
        """Keep the left cursor on a row that can actually be chosen.

        The cursor is set from a caller's remembered position and from plain
        arithmetic on the row count, neither of which knows that section headers
        are not selectable -- so without this a fresh screen opens with the
        highlight sitting on a header nobody can act on."""
        if not left:
            self._left_cursor = 0
            return
        self._left_cursor = max(0, min(self._left_cursor, len(left) - 1))
        if left[self._left_cursor][2]:
            return
        sel = self._selectable_indices(left)
        if sel:
            # Prefer the next selectable row below, so opening on a header lands
            # on the first thing under it rather than jumping backwards.
            below = [i for i in sel if i > self._left_cursor]
            self._left_cursor = below[0] if below else sel[-1]

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

    def _chrome_lines(self) -> int:
        """Everything the frame draws that is not a body row."""
        return (header_height() + BOX_LINES + self.footer_lines
                + (1 if self._detail else 0))

    def _body_rows(self, left, right, term):
        chrome = self._chrome_lines()
        if self.fill_height:
            return max(MIN_BODY, term[1] - chrome)
        return body_height(term[1], max(len(left), len(right)), len(left),
                           chrome=chrome)

    def _frame(self, left, right, term):
        w = max(72, min(term[0] - 2, 110))
        rows_h = self._body_rows(left, right, term)
        inner = w - 4
        left_w = self.left_width
        right_w = inner - left_w - 3            # " │ " between columns
        c = Colors.PRIMARY
        lines = [box_row(BOX_TL, BOX_H, BOX_TR, w, c)]

        def row(content):
            pad = inner - visible_len(content)
            lines.append(f"{c}{BOX_V}{Colors.RESET} {content}{' ' * max(0, pad)} {c}{BOX_V}{Colors.RESET}")

        def cell(text, cstate, width):
            """Pad `text` to `width`, then apply the cursor indicator/emphasis for
            `cstate`, always reserving a 2-col indicator gutter so every row keeps
            the same width and left inset."""
            style = self.cursor_style
            if style == "marker":
                if cstate == FOCUS_CURSOR:
                    lead = f"{Colors.PRIMARY}▸{Colors.RESET} "   # "▸ "
                elif cstate == FAINT_CURSOR:
                    lead = f"{Colors.PRIMARY}•{Colors.RESET} "   # "• "
                else:
                    lead = "  "
                return lead + pad_to(text, width - 2)
            # non-marker styles: reserve the same 2-col gutter
            lead = f"{Colors.PRIMARY}•{Colors.RESET} " if cstate == FAINT_CURSOR else "  "
            padded = pad_to(text, width - 2)
            if cstate == FOCUS_CURSOR:
                if style == "highlight":
                    return _restyle(lead + padded, Colors.HIGHLIGHT_BG)
                if style == "bold":
                    return _restyle(lead + padded, Colors.BOLD)
                if style == "color":
                    return _restyle(lead + padded, Colors.PRIMARY)
            return lead + padded

        def two(lt, rt, lt_state=NONE, rt_state=NONE):
            row(f"{cell(lt, lt_state, left_w)} {Colors.DIM}{BOX_V}{Colors.RESET} "
                f"{cell(rt, rt_state, right_w)}")

        if self.subtitle:
            row(f"{Colors.BOLD}{self.title}{Colors.RESET}  {Colors.MUTED}{self.subtitle}{Colors.RESET}")
        else:
            row(f"{Colors.BOLD}{self.title}{Colors.RESET}")
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        def hdr(label, active):
            # Active pane header emphasis is switchable via header_style.
            if self.header_style == "bold":
                if active:
                    return f"{Colors.BOLD}{Colors.PRIMARY}{label}{Colors.RESET}"
                return f"{Colors.BOLD}{Colors.MUTED}{label}{Colors.RESET}"
            if self.header_style == "color":
                if active:
                    return f"{Colors.PRIMARY}{label}{Colors.RESET}"
                return f"{Colors.MUTED}{label}{Colors.RESET}"
            # "chip": inverted reverse-video chip on the active pane.
            if active:
                return f"{Colors.REVERSE}{Colors.BOLD} {label} {Colors.RESET}"
            return f"{Colors.BOLD}{Colors.MUTED}{label}{Colors.RESET}"

        n = len(right)
        if self.right_header:
            left_part = hdr(self.right_header, self.focus == "right")
        elif self.right_filterable:
            left_part = (f"{Colors.PRIMARY}Filter:{Colors.RESET} {self._query}{Colors.PRIMARY}▌{Colors.RESET}"
                         if self.focus == "right"
                         else f"{Colors.MUTED}(type to filter){Colors.RESET}")
        else:
            left_part = ""
        count = f"{Colors.MUTED}{n}{Colors.RESET}" if self.show_count else ""
        # cell() reserves a 2-col indicator gutter, so the usable width here is right_w - 2.
        if count:
            pad = right_w - 2 - visible_len(left_part) - visible_len(count)
            header_right = f"{left_part}{' ' * max(1, pad)}{count}"
        else:
            # Nothing to push right, so add nothing: a trailing space here shunts
            # the header one column off the rows it labels.
            header_right = left_part
        two(hdr(self.left_header, self.focus == "left"), header_right)
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        end = min(n, self._scroll + rows_h)
        for r in range(rows_h):
            # left column
            lt_state = NONE
            if r < len(left):
                render, _, _ = left[r]
                is_cur = r == self._left_cursor
                lt = render(self.focus == "left", is_cur)
                if is_cur:
                    lt_state = FOCUS_CURSOR if self.focus == "left" else FAINT_CURSOR
            else:
                lt = ""
            # right column: scrolled window
            idx = self._scroll + r
            rt_state = NONE
            if r == 0 and self._scroll > 0:
                rt = f"{Colors.MUTED}▲ {self._scroll} above{Colors.RESET}"
            elif r == rows_h - 1 and end < n:
                rt = f"{Colors.MUTED}▼ {n - end} below{Colors.RESET}"
            elif idx < n:
                render, _, sel = right[idx]
                is_cur = idx == self._cursor and sel
                rt = render(self.focus == "right", is_cur)
                if is_cur and self.focus == "right":
                    rt_state = FOCUS_CURSOR
            else:
                rt = ""
            two(lt, rt, lt_state, rt_state)

        lines.append(box_row(BOX_BL, BOX_H, BOX_BR, w, c))
        if self._detail:
            fv = right[self._cursor][1] if 0 <= self._cursor < n and right[self._cursor][2] else None
            dtext = self._detail(fv) if fv is not None else ""
            lines.append("  " + truncate_ansi(dtext, w - 2) if dtext else "")
        footer = self.footer() if callable(self.footer) else self.footer
        if footer:
            lines.append(footer)
        else:
            lines.append(f"  {Colors.PRIMARY}Tab{Colors.MUTED} switch pane  {Colors.PRIMARY}↑/↓{Colors.MUTED} move  "
                         f"{Colors.PRIMARY}Enter{Colors.MUTED} set  {Colors.PRIMARY}Esc{Colors.MUTED} done  "
                         f"{Colors.DIM}(type to filter the right){Colors.RESET}")

        out = sys.__stdout__ if sys.__stdout__ else sys.stdout
        # Home the cursor and overwrite in place. Erasing the whole screen first
        # blanks it for one frame, which reads as a flicker on every repaint --
        # and a live screen repaints a lot. Each line below carries its own
        # erase-to-end-of-line, and the trailing erase clears anything left over.
        out.write("\033[H\033[J" if not self._painted else "\033[H")
        self._painted = True
        print_header()
        out.write("\n".join(lines).replace("\n", "\033[K\n") + "\033[J\033[3J")
        out.flush()

    def render_once(self):
        """Build the current rows and draw one frame (no input). Returns the
        (left, right) row lists used, for headless inspection."""
        left = self._left_rows()
        self._clamp_left(left)
        right = self._filtered_right(self._right_rows(self._active_left_value(left), self._query))
        term = shutil.get_terminal_size((80, 24))
        self._clamp(right, self._body_rows(left, right, term))
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

    def _next_key(self):
        """Block for a keypress, or poll so `update_callback` still runs while
        nothing is typed. Returns None when the callback asked for a repaint;
        a screen backed by live data would otherwise sit frozen on a blocking
        read until the user happened to press something."""
        if not self.update_callback:
            return getch(return_special_keys=True)
        while True:
            key = getch_with_timeout(self.refresh_interval_ms, return_special_keys=True)
            if key is not None:
                return key
            if self.update_callback(self):
                return None

    def run(self):
        """Show the picker. Loops until Esc (returns None) or a hotkey callback
        returns ``"return"`` (returns that hotkey char)."""
        with cbreak_noecho():
            while True:
                left = self._left_rows()
                self._clamp_left(left)
                right = self._filtered_right(self._right_rows(self._active_left_value(left), self._query))
                term = shutil.get_terminal_size((80, 24))
                self._clamp(right, self._body_rows(left, right, term))
                self._frame(left, right, term)

                key = self._next_key()
                if key is None:
                    continue
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
                            out = self._on_left_enter(self._active_left_value(left))
                            if out is not None:
                                return out
                        if self.left_enter_focuses_right:
                            self.focus = "right"
                    elif self._cursor < len(right) and right[self._cursor][2]:
                        if self._on_right_enter:
                            out = self._on_right_enter(right[self._cursor][1])
                            if out is not None:
                                return out
                elif key == KEY_BACKSPACE:
                    if self.focus == "right" and self.right_filterable:
                        self._query = self._query[:-1]
                        self._cursor = self._scroll = 0
                elif key == KEY_SPACE:
                    if self.focus == "right" and self.right_filterable and not self.space_activates:
                        self._query += " "
                        self._cursor = self._scroll = 0
                    elif self.focus == "right":
                        if self._cursor < len(right) and right[self._cursor][2] and self._on_right_enter:
                            out = self._on_right_enter(right[self._cursor][1])
                            if out is not None:
                                return out
                    elif self.focus == "left":
                        cb = self._on_left_space or self._on_left_enter
                        if cb:
                            out = cb(self._active_left_value(left))
                            if out is not None:
                                return out
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
