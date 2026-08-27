"""A terminal screen just real enough to catch repaint bugs.

Widgets here repaint in place from the home position rather than clearing
first, so whether a frame is correct depends on what was on the screen before
it. Asserting on the escape sequence a widget emits cannot see that; only
replaying it onto a grid can.

Understands the subset the widgets actually emit: cursor home, erase to end of
line, erase to end of screen, and printable text. Colour codes are dropped.
"""

import re

CSI = re.compile(r"\x1b\[([0-9;?]*)([A-Za-z])")


class Screen:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.grid = [[" "] * cols for _ in range(rows)]
        self.scrollback = []
        self.row = self.col = 0

    def grow(self, cols, rows):
        """Grow the window the way a terminal with scrollback does: the extra
        height is filled from above, pulling what scrolled off back into view,
        so everything already on screen moves down. This is the case that broke
        in the wild, and the reason a resize cannot just repaint in place."""
        assert rows >= self.rows and cols >= self.cols
        for line in self.grid:
            line += [" "] * (cols - self.cols)
        revealed = rows - self.rows
        if revealed:
            older = [list(line) + [" "] * (cols - self.cols)
                     for line in self.scrollback[-revealed:]]
            older += [[" "] * cols] * (revealed - len(older))
            self.grid = older + self.grid
        self.cols, self.rows = cols, rows

    def snapshot(self):
        """Remember the current screen as what a later grow() reveals."""
        self.scrollback = [list(line) for line in self.grid]

    def feed(self, stream):
        i = 0
        while i < len(stream):
            match = CSI.match(stream, i)
            if match:
                self._escape(*match.groups())
                i = match.end()
                continue
            char = stream[i]
            i += 1
            if char == "\n":
                self.row += 1
                self.col = 0
                if self.row >= self.rows:
                    self.grid.pop(0)
                    self.grid.append([" "] * self.cols)
                    self.row = self.rows - 1
            elif char == "\r":
                self.col = 0
            else:
                if self.col < self.cols:
                    self.grid[self.row][self.col] = char
                self.col += 1

    def _escape(self, arg, cmd):
        if cmd == "H":
            self.row = self.col = 0
        elif cmd == "K":
            self._blank_rest_of_line()
        elif cmd == "J" and arg != "3":       # 3 is scrollback, nothing on screen
            self._blank_rest_of_line()
            for r in range(self.row + 1, self.rows):
                self.grid[r] = [" "] * self.cols

    def _blank_rest_of_line(self):
        for c in range(self.col, self.cols):
            self.grid[self.row][c] = " "

    def lines(self):
        return [("".join(line)).rstrip() for line in self.grid]

    def text(self):
        return "\n".join(self.lines())
