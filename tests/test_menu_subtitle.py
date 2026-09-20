"""A menu subtitle is prose, so it is drawn like prose.

Left aligned, wrapped on what shows rather than on the bytes, with line breaks
and colour kept. Centring gave every line its own left edge, and measuring the
bytes let a coloured phrase push the right border off the box.
"""
import os
import re
import shutil

import pytest

from chotic_ui.primitives import Colors
from chotic_ui.widgets.menu import Menu, MenuItem

from .screen import Screen

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
COLS, ROWS = 60, 30


class _Sink:
    def __init__(self, into):
        self.into = into

    def write(self, text):
        self.into.append(text)

    def flush(self):
        pass


def _framed(subtitle, monkeypatch):
    """The drawn box, as rows of text, borders included."""
    menu = Menu(title="Title", subtitle=subtitle)
    menu.add_item(MenuItem(label="Only item", value=1))

    size = os.terminal_size((COLS, ROWS))
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): size)
    written = []
    sink = _Sink(written)
    monkeypatch.setattr("sys.stdout", sink)
    monkeypatch.setattr("sys.__stdout__", sink)
    menu._render()
    monkeypatch.undo()

    screen = Screen(COLS, ROWS)
    screen.feed("".join(written))
    return [row for row in screen.lines() if "│" in row]


def test_a_subtitle_starts_at_the_same_column_on_every_line(monkeypatch):
    text = ("One sentence that is long enough to wrap onto a second line, and "
            "then a third line after that.")
    rows = [r for r in _framed(text, monkeypatch)
            if "sentence" in r or "third" in r]

    assert len(rows) >= 2
    assert len({len(r) - len(r.lstrip("│ ")) for r in rows}) == 1


def test_line_breaks_survive(monkeypatch):
    rows = _framed("FIRST\n\nSECOND", monkeypatch)
    text = "\n".join(rows)

    assert "FIRST" in text and "SECOND" in text
    assert text.index("FIRST") < text.index("SECOND")


def test_every_row_is_the_same_width(monkeypatch):
    """A coloured phrase measured by its bytes pushes the border out."""
    rows = _framed(f"a {Colors.ERROR}LOUD{Colors.RESET} subtitle that wraps "
                   f"around once or twice in here", monkeypatch)

    assert len({r.rstrip().rindex("│") for r in rows}) == 1


class TestWrappingWithColour:
    def test_a_coloured_phrase_is_not_split_across_lines(self):
        phrase = "WILL BE DELETED"
        menu = Menu(title="T", subtitle="")

        wrapped = menu._wrap_coloured(
            "padding padding padding padding padding "
            f"{Colors.ERROR}{phrase}{Colors.RESET} and more words after", 30)

        assert any(phrase in line for line in wrapped)

    def test_punctuation_stays_attached(self):
        """Splitting there rejoined with a space and printed "DELETED ."."""
        menu = Menu(title="T", subtitle="")

        wrapped = menu._wrap_coloured(
            f"say {Colors.ERROR}DELETED{Colors.RESET}. then stop", 40)

        assert "DELETED ." not in CSI.sub("", "\n".join(wrapped))
