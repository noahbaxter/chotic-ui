"""Repainting a frame must leave nothing of the frame before it behind.

The bug these cover: the banner printed plain lines while every other line
carried an erase, so old rows survived to the right of the art and beside the
version line. A window resize made it visible, because growing the window
pulls the previous frame back into view underneath the new one.
"""

import os
import shutil

import pytest

from chotic_ui.components import configure_header, header_height
from chotic_ui.widgets.two_pane import TwoPane

from .screen import Screen

BANNER = "\n".join([
    "###   #   #  #   #   ###",
    "#     # #  #  ##  #  #   ",
    "###    #   #  # # #  #   ",
    "  #    #   #  #  ##  #   ",
    "###    #   #  #   #   ###",
])

# Wide enough that the frame runs well past the banner: stale text only shows
# up in the columns the banner does not itself write over.
COLS = 100
SHORT, TALL = 24, 40


@pytest.fixture
def banner():
    configure_header(BANNER, "1.5.0")
    yield
    configure_header("", "")


def pane():
    rows = ["CSC Released Packs", "Popular Charters", "Guitar Hero"]
    return TwoPane(
        title="Chart Packs",
        left_rows=lambda: [(lambda f, c, t=t: t, t, True) for t in rows],
        right_rows=lambda active, query: [(lambda f, c: "Enable all", "on", True)],
        footer=lambda: "  S sync\n  Tab panes  Esc quit",
        footer_lines=2,
        fill_height=True,
    )


def paint(widget, screen, monkeypatch):
    """Render one frame at the screen's current size and replay it."""
    size = os.terminal_size((screen.cols, screen.rows))
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): size)
    written = []
    sink = _Sink(written)
    monkeypatch.setattr("sys.stdout", sink)
    monkeypatch.setattr("sys.__stdout__", sink)
    widget.render_once()
    monkeypatch.undo()
    screen.feed("".join(written))


class _Sink:
    """Stands in for the console. print_header() goes through sys.stdout and the
    frame through sys.__stdout__; both have to land in the same place or the
    ordering the bug depends on is lost."""

    def __init__(self, sink):
        self._sink = sink

    def write(self, text):
        self._sink.append(text)

    def flush(self):
        pass

    def isatty(self):
        return True


def test_grown_window_shows_no_trace_of_the_previous_frame(banner, monkeypatch):
    widget = pane()
    screen = Screen(COLS, SHORT)
    paint(widget, screen, monkeypatch)
    before = screen.text()
    assert "Chart Packs" in before

    screen.snapshot()
    screen.grow(COLS, TALL)
    paint(widget, screen, monkeypatch)

    # One title, one box, one footer. Two of anything means the frame drawn at
    # the old size is still showing through.
    assert screen.text().count("Chart Packs") == 1
    assert screen.text().count("Tab panes") == 1
    assert len([line for line in screen.lines() if line.startswith("╭")]) == 1


def test_repaint_over_a_dirty_screen_leaves_no_stale_text(banner, monkeypatch):
    """No resize, just a screen with something already on it: coming back from
    another screen, or a frame that was wider. Repainting is not a clear, so
    every line of the frame, banner included, has to erase what it lands on."""
    widget = pane()
    screen = Screen(COLS, TALL)
    paint(widget, screen, monkeypatch)

    stale = "STALE"
    for row in range(header_height()):
        screen.grid[row][COLS - len(stale):] = list(stale)
    assert stale in screen.text()

    paint(widget, screen, monkeypatch)
    assert stale not in screen.text()


def test_frame_fits_the_window(banner, monkeypatch):
    """A frame taller than the window scrolls the terminal, which moves home out
    from under the next repaint."""
    widget = pane()
    for rows in (SHORT, TALL):
        screen = Screen(COLS, rows)
        paint(widget, screen, monkeypatch)
        assert screen.lines()[0] == "", "banner should start at the top, unscrolled"
        assert "Tab panes" in screen.lines()[rows - 1]
