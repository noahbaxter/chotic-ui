"""A one-line text editor for the terminal: a cursor you can move, text that
wraps onto further rows and can be edited back across them, and paste.

The whole prompt-plus-text is redrawn on every change from the row the cursor
is on, so a line that wrapped is edited like any other. `input_with_esc` drives
it; this module holds the editing and the drawing, which need no real terminal
to test.
"""

from . import clipboard
from .terminal import visible_len

LEFT = "LEFT"
RIGHT = "RIGHT"
HOME = "HOME"
END = "END"
DELETE = "DELETE"
BACKSPACE = "BACKSPACE"
PASTE = "PASTE"
ENTER = "ENTER"
ESC = "ESC"

# Escape sequences after the ESC byte (xterm, VT220 and SS3 spellings).
_SEQUENCES = {
    "[D": LEFT, "[C": RIGHT,
    "[H": HOME, "[1~": HOME, "[7~": HOME, "OH": HOME,
    "[F": END, "[4~": END, "[8~": END, "OF": END,
    "[3~": DELETE,
}


def parse_chunk(chunk: str) -> list[str]:
    """Split bytes read off a Unix terminal into characters and key names.
    A lone ESC is the Esc key; any other sequence not listed is dropped."""
    keys = []
    i = 0
    while i < len(chunk):
        ch = chunk[i]
        if ch == "\x1b":
            if len(chunk) == 1:
                keys.append(ESC)
                break
            i += 1
            if i == len(chunk):
                break
            lead = chunk[i]
            if lead == "O":
                end = i + 1
            elif lead == "[":
                end = i + 1
                while end < len(chunk) and not (chunk[end].isalpha() or chunk[end] == "~"):
                    end += 1
            else:
                continue  # ESC before an ordinary key: drop the ESC
            key = _SEQUENCES.get(chunk[i:end + 1])
            if key:
                keys.append(key)
            i = end + 1
            continue
        keys.append(ch)
        i += 1
    return keys


class LineEditor:
    """Editing state plus the drawing of it. `feed` takes keys; `render`
    returns the escape text that brings the terminal up to date."""

    def __init__(self, prompt: str = ""):
        self.prompt = prompt
        self.text = ""
        self.pos = 0
        self.done = False
        self.cancelled = False
        self._row = 0  # rows the cursor sits below the prompt's first row

    def feed(self, keys) -> None:
        for key in keys:
            if self.done:
                return
            self._apply(key)

    def _apply(self, key: str) -> None:
        if key == ENTER or key in ("\r", "\n"):
            self.pos = len(self.text)
            self.done = True
        elif key == ESC:
            self.pos = len(self.text)  # so the newline lands below all of it
            self.cancelled = self.done = True
        elif key == LEFT:
            self.pos = max(0, self.pos - 1)
        elif key == RIGHT:
            self.pos = min(len(self.text), self.pos + 1)
        elif key == HOME:
            self.pos = 0
        elif key == END:
            self.pos = len(self.text)
        elif key in (BACKSPACE, "\x7f", "\x08"):
            if self.pos:
                self.text = self.text[:self.pos - 1] + self.text[self.pos:]
                self.pos -= 1
        elif key == DELETE:
            self.text = self.text[:self.pos] + self.text[self.pos + 1:]
        elif key in (PASTE, "\x16"):  # Ctrl+V reaches the app as a keypress
            self._insert(clipboard.read_text())
        elif len(key) == 1 and key >= " " and key != "\x7f":
            self._insert(key)

    def _insert(self, text: str) -> None:
        text = "".join(c for c in text if c >= " " and c != "\x7f")  # one line
        self.text = self.text[:self.pos] + text + self.text[self.pos:]
        self.pos += len(text)

    def render(self, cols: int) -> str:
        """Redraw prompt and text from where the last render began, and leave
        the cursor on `pos`."""
        cols = max(cols, 1)
        start = visible_len(self.prompt)
        out = []
        if self._row:
            out.append(f"\x1b[{self._row}A")
        out.append("\r\x1b[J" + self.prompt + self.text)
        total = start + len(self.text)
        if total and total % cols == 0:
            # Text that ends exactly on the last column leaves the cursor
            # waiting to wrap; write the wrap so the cursor row is certain.
            out.append(" \b")
        end_row = total // cols
        row, col = divmod(start + self.pos, cols)
        if end_row > row:
            out.append(f"\x1b[{end_row - row}A")
        out.append(f"\x1b[{col + 1}G")
        self._row = row
        return "".join(out)
