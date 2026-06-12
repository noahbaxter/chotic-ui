"""
FilterList - a generic, real-time filterable list.

Type to filter as-you-go, arrow keys to move, Enter to pick, Esc to cancel. A
reusable building block: hand it `(label, value)` pairs and it returns the chosen
value. Labels may contain ANSI colour codes; matching is done on the visible text
(or a custom `search_key`).
"""

import sys
import shutil

from ..primitives import (
    Colors, getch, cbreak_noecho,
    KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_BACKSPACE, KEY_SPACE,
)
from ..primitives.terminal import strip_ansi, get_terminal_width, visible_len, truncate_ansi
from ..components import (
    print_header, box_row,
    BOX_TL, BOX_TR, BOX_BL, BOX_BR, BOX_H, BOX_V, BOX_TL_DIV, BOX_TR_DIV,
)


class FilterList:
    """A real-time filterable, scrollable picker.

    Items are (label, value) pairs. Use `(label, FilterList.SECTION)` for a
    non-selectable section header; the cursor skips it and it's hidden while
    filtering."""

    SECTION = object()  # sentinel value marking a section-header row

    def __init__(self, items, *, title="", subtitle="", esc_label="Back",
                 prompt="Filter", page_size=None, search_key=None):
        # items: list of (label, value). label may contain ANSI.
        # page_size None => size to the terminal height (avoids scrolling by 1).
        self.items = list(items)
        self.title = title
        self.subtitle = subtitle
        self.esc_label = esc_label
        self.prompt = prompt
        self.page_size = page_size
        self._search_key = search_key or (lambda label, value: strip_ansi(label))
        self._query = ""
        self._cursor = 0
        self._scroll = 0

    def _matches(self):
        q = self._query.lower().strip()
        if not q:
            return self.items
        terms = q.split()
        out = []
        for label, value in self.items:
            if value is self.SECTION:
                continue  # headers hidden while filtering (flat results)
            hay = self._search_key(label, value).lower()
            if all(t in hay for t in terms):
                out.append((label, value))
        return out

    def _selectable(self, matches):
        return [i for i, (_, v) in enumerate(matches) if v is not self.SECTION]

    def _width(self):
        return max(40, min(get_terminal_width() - 2, 100))

    def _page(self):
        """Visible row capacity: fixed if the caller set page_size, else derived
        from terminal height (header + box chrome + hint ~= 16 lines)."""
        if self.page_size is not None:
            return self.page_size
        rows = shutil.get_terminal_size((80, 24)).lines
        return max(6, rows - 16)

    def _render(self, matches):
        w = self._width()
        c = Colors.PRIMARY
        inner = w - 4
        lines = []

        def row(content):
            content = truncate_ansi(content, inner)
            pad = inner - visible_len(content)
            lines.append(f"{c}{BOX_V}{Colors.RESET} {content}{' ' * pad} {c}{BOX_V}{Colors.RESET}")

        lines.append(box_row(BOX_TL, BOX_H, BOX_TR, w, c))
        if self.title:
            row(f"{Colors.BOLD}{self.title}{Colors.RESET}")
        if self.subtitle:
            row(f"{Colors.MUTED}{self.subtitle}{Colors.RESET}")
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        # Query line
        count = f"{Colors.MUTED}{len(matches)} match{'es' if len(matches) != 1 else ''}{Colors.RESET}"
        query_disp = f"{Colors.PRIMARY}{self.prompt}:{Colors.RESET} {self._query}{Colors.PRIMARY}▌{Colors.RESET}"
        gap = inner - visible_len(query_disp) - visible_len(count)
        row(f"{query_disp}{' ' * max(1, gap)}{count}")
        lines.append(box_row(BOX_TL_DIV, BOX_H, BOX_TR_DIV, w, c))

        # Visible window
        if not matches:
            row(f"{Colors.MUTED}(no matches){Colors.RESET}")
        else:
            start = self._scroll
            end = min(len(matches), start + self._page())
            if start > 0:
                row(f"{Colors.MUTED}  ▲ {start} above{Colors.RESET}")
            for i in range(start, end):
                label, value = matches[i]
                if value is self.SECTION:
                    row(f"{Colors.DIM}{label}{Colors.RESET}")
                elif i == self._cursor:
                    row(f"{Colors.PRIMARY}▸ {Colors.RESET}{label}")
                else:
                    row(f"  {label}")
            if end < len(matches):
                row(f"{Colors.MUTED}  ▼ {len(matches) - end} below{Colors.RESET}")

        lines.append(box_row(BOX_BL, BOX_H, BOX_BR, w, c))
        hint = (f"  {Colors.MUTED}↑/↓ Navigate  {Colors.PRIMARY}Enter{Colors.MUTED} Select  "
                f"{Colors.PRIMARY}⌫{Colors.MUTED} Delete  {Colors.PRIMARY}Esc{Colors.MUTED} {self.esc_label}  "
                f"{Colors.DIM}(type to filter){Colors.RESET}")
        lines.append(hint)

        out = sys.__stdout__ if sys.__stdout__ else sys.stdout
        # header rendered separately (it manages its own caching/print)
        out.write("\033[H\033[J")
        print_header()
        content = "\n".join(lines).replace("\n", "\033[K\n")
        out.write(content + "\033[J\033[3J")
        out.flush()

    def _clamp_scroll(self, matches):
        if self._cursor < self._scroll:
            self._scroll = self._cursor
        elif self._cursor >= self._scroll + self._page():
            self._scroll = self._cursor - self._page() + 1
        self._scroll = max(0, min(self._scroll, max(0, len(matches) - self._page())))

    def run(self):
        """Show the list. Returns the chosen value, or None if cancelled."""
        with cbreak_noecho():
            while True:
                matches = self._matches()
                sel = self._selectable(matches)
                # Keep the cursor on a selectable (non-header) row.
                if not sel:
                    self._cursor = 0
                elif self._cursor not in sel:
                    self._cursor = min(sel, key=lambda i: abs(i - self._cursor))
                self._clamp_scroll(matches)
                self._render(matches)

                key = getch(return_special_keys=True)
                if key == KEY_ESC:
                    return None
                if key == KEY_ENTER:
                    if sel and matches[self._cursor][1] is not self.SECTION:
                        return matches[self._cursor][1]
                    continue
                if key == KEY_UP:
                    above = [i for i in sel if i < self._cursor]
                    self._cursor = above[-1] if above else self._cursor
                elif key == KEY_DOWN:
                    below = [i for i in sel if i > self._cursor]
                    self._cursor = below[0] if below else self._cursor
                elif key == KEY_BACKSPACE:
                    self._query = self._query[:-1]
                    self._cursor = 0
                elif key == KEY_SPACE:
                    self._query += " "
                    self._cursor = 0
                elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                    self._query += key
                    self._cursor = 0
