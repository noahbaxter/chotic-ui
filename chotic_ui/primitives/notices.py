"""Plain lines printed since the last screen, so the next screen can show them.

Every screen repaints from the top, so whatever was printed before it opened is
drawn over before anyone reads it. Rather than trusting each caller to know
what comes next, `install()` wraps sys.stdout and keeps the plain lines written
through it; the next screen draws them under the banner.

Only plain lines count. A write carrying a carriage return, a backspace or a
cursor control is an animation, a frame or typed echo, so it passes straight
through and is never kept: progress lines, spinners and repainting frames stay
exactly as they are. Colour codes are allowed.

A pause (wait_with_skip, wait_for_key, the input prompts) means the text sat
on screen long enough to read, so it clears what was kept.
"""

import re
import sys
import threading

# Anything but SGR colour: CSI with a final byte other than "m", OSC (window
# titles), carriage return and backspace.
_CONTROL = re.compile(r"\r|\x08|\x1b\[[0-9;?]*[A-Za-ln-z]|\x1b\]")

# More than this and the notice starts costing the screen its own rows.
MAX_LINES = 6

_lock = threading.Lock()
_lines: list = []
_partial = ""


def record(text: str) -> None:
    """Keep the plain lines in `text`. Anything with control codes is dropped,
    along with the unfinished line it was writing over."""
    global _partial
    with _lock:
        if _CONTROL.search(text):
            _partial = ""
            return
        text = _partial + text
        *done, _partial = text.split("\n")
        _lines.extend(done)


def mark_read() -> None:
    """The user has had time to read what is on screen."""
    global _partial
    with _lock:
        _lines.clear()
        _partial = ""


def pending() -> bool:
    """Whether there is anything unread, for a live screen deciding to repaint."""
    with _lock:
        return any(line.strip() for line in _lines)


def take() -> list:
    """The unread lines, blank edges trimmed, capped at MAX_LINES. Clears them."""
    with _lock:
        lines = [line.rstrip() for line in _lines]
        _lines.clear()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES - 1] + ["…"]
    return lines


class Capture:
    """sys.stdout, with the plain lines written through it kept for the next
    screen. Everything else, including attributes a wrapper underneath adds,
    passes through untouched."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, text):
        record(text)
        return self._stream.write(text)

    def __getattr__(self, name):
        return getattr(self._stream, name)


def install() -> None:
    """Wrap sys.stdout, once. Install it last, outside any other wrapper, so it
    sees what the program prints and nothing a wrapper adds."""
    if not isinstance(sys.stdout, Capture):
        sys.stdout = Capture(sys.stdout)
