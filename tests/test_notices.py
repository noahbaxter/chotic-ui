"""Text printed before a screen opens is shown in it, not drawn over.

Every screen repaints from the top, so a warning printed just before one opened
was gone before anyone read it: a pre-sync check shipped as a bare "Sync
anyway?" because its reasons were printed above the dialog. Animations and
frames must pass through untouched and never come back as a notice.
"""
import contextlib
import os
import shutil
import sys

import pytest

from chotic_ui.components import configure_header
from chotic_ui.primitives import KEY_DOWN, KEY_ESC, notices
from chotic_ui.primitives.keyboard_input import _marks_read
from chotic_ui.widgets import menu as menu_module
from chotic_ui.widgets.menu import Menu, MenuItem
from chotic_ui.widgets.two_pane import TwoPane

from .screen import Screen

COLS, ROWS = 80, 30
BANNER = "\n".join(["###  #  #", "#     ## ", "###  #  #"])


@pytest.fixture(autouse=True)
def fresh():
    notices.mark_read()
    configure_header(BANNER, "1.0")
    yield
    notices.mark_read()
    configure_header("", "")


class _Sink:
    def __init__(self):
        self.written = []

    def write(self, text):
        self.written.append(text)

    def flush(self):
        pass

    def isatty(self):
        return True


def _sized(monkeypatch):
    size = os.terminal_size((COLS, ROWS))
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): size)
    monkeypatch.setattr("chotic_ui.primitives.terminal.get_terminal_width", lambda: COLS)


class TestWhatIsKept:
    def test_plain_lines_are_kept(self):
        notices.record("Library not connected\n  /Volumes/NAS\n")
        assert notices.take() == ["Library not connected", "  /Volumes/NAS"]

    def test_colour_is_allowed(self):
        notices.record("\x1b[31mFAILURE\x1b[0m: no space\n")
        assert notices.take() == ["\x1b[31mFAILURE\x1b[0m: no space"]

    @pytest.mark.parametrize("frame", [
        "\r  ⠋ Reading /Volumes/NAS",          # spinner
        "\x1b[2K\rScanning 3/9 Misc",           # print_progress
        "\x1b[12A",                             # sync painter moving up
        "\r│ row │\x1b[K\n",                    # a frame row
        "\x1b[H\x1b[J",                         # a screen homing
        "ab\x08 \x08",                          # typed echo and a backspace
        "\x1b]0;Synchotic\x07",                 # window title
    ])
    def test_animation_and_frames_are_never_kept(self, frame):
        notices.record(frame)
        assert notices.take() == []

    def test_a_progress_line_takes_its_unfinished_text_with_it(self):
        notices.record("Checking")
        notices.record("\r\x1b[2KChecking 2/9")
        notices.record("\n")
        assert notices.take() == []

    def test_blank_edges_are_trimmed(self):
        notices.record("\n\nhello\n\n")
        assert notices.take() == ["hello"]

    def test_a_flood_is_capped(self):
        notices.record("".join(f"line {i}\n" for i in range(20)))
        kept = notices.take()
        assert len(kept) == notices.MAX_LINES
        assert kept[-1] == "…"

    def test_taking_clears_them(self):
        notices.record("once\n")
        notices.take()
        assert notices.take() == []


class TestCapture:
    def test_it_passes_writes_and_attributes_through(self):
        class Tee(_Sink):
            def log_only(self, text):
                self.written.append(("log", text))

        tee = Tee()
        capture = notices.Capture(tee)
        capture.write("shown\n")
        capture.log_only("debug")
        assert tee.written == ["shown\n", ("log", "debug")]
        assert notices.take() == ["shown"]

    def test_install_wraps_once(self, monkeypatch):
        monkeypatch.setattr(sys, "stdout", _Sink())
        notices.install()
        notices.install()
        assert isinstance(sys.stdout, notices.Capture)
        assert not isinstance(sys.stdout._stream, notices.Capture)


def test_a_wait_marks_what_was_on_screen_as_read():
    """A sync summary sat on screen through a countdown; showing it again on
    the next screen would repeat what was already read."""
    notices.record("Sync finished\n")
    _marks_read(lambda: None)()
    assert notices.take() == []


def test_a_wait_marks_read_even_when_escaped():
    notices.record("Sign in failed\n")

    def escaped():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _marks_read(escaped)()
    assert notices.take() == []


def test_the_waits_are_all_marked():
    from chotic_ui.primitives import keyboard_input as k
    for wait in (k.wait_with_skip, k.wait_for_key, k.input_with_esc, k.menu_input):
        assert hasattr(wait, "__wrapped__"), f"{wait.__name__} does not mark read"


def test_a_menu_shows_what_was_printed_before_it(monkeypatch):
    """The shipped bug: reasons printed, then a dialog painted over them."""
    _sized(monkeypatch)
    sink = _Sink()
    monkeypatch.setattr(sys, "__stdout__", sink)
    monkeypatch.setattr(menu_module, "cbreak_noecho", contextlib.nullcontext)
    # Arrow down first: the notice has to survive a repaint, not just the
    # first frame.
    keys = iter([KEY_DOWN, KEY_ESC])
    monkeypatch.setattr(menu_module, "getch_with_timeout", lambda *a, **k: next(keys))
    monkeypatch.setattr(Menu, "_drain_arrow_keys", lambda self: 0)

    notices.record("Not enough disk space\nNeeds 40 GB, you have 18 GB.\n")
    menu = Menu(title="Sync anyway?")
    menu.add_item(MenuItem("No", value=False))
    menu.add_item(MenuItem("Yes", value=True))
    menu.run()

    screen = Screen(COLS, ROWS)
    screen.feed("".join(sink.written))
    text = screen.text()
    assert "Not enough disk space" in text
    assert "Needs 40 GB, you have 18 GB." in text
    assert text.index("Not enough disk space") < text.index("Sync anyway?")


def _pane():
    return TwoPane(
        title="Library",
        left_rows=lambda: [(lambda f, c: "Drive", "d", True)],
        right_rows=lambda active, query: [(lambda f, c: "Setlist", "s", True)],
        footer=lambda: "  S sync\n  Esc quit",
        footer_lines=2,
        fill_height=True,
    )


def _paint(pane, screen, monkeypatch):
    _sized(monkeypatch)
    sink = _Sink()
    monkeypatch.setattr(sys, "__stdout__", sink)
    pane.render_once()
    monkeypatch.undo()
    screen.feed("".join(sink.written))


def test_a_live_screen_keeps_a_notice_on_every_frame(monkeypatch):
    """Home repaints four times a second. A notice shown on one frame and gone
    the next is as unread as one never shown."""
    pane = _pane()
    screen = Screen(COLS, ROWS)
    notices.record("Scan failed: Misc\n")
    _paint(pane, screen, monkeypatch)
    _paint(pane, screen, monkeypatch)
    assert "Scan failed: Misc" in screen.text()


def test_a_notice_still_fits_the_window(monkeypatch):
    """Rows spent on the notice come out of the body, not off the top."""
    pane = _pane()
    screen = Screen(COLS, ROWS)
    notices.record("".join(f"warning {i}\n" for i in range(20)))
    _paint(pane, screen, monkeypatch)
    _paint(pane, screen, monkeypatch)
    lines = screen.lines()
    assert lines[0] == "", "banner should start at the top, unscrolled"
    assert "Esc quit" in lines[ROWS - 1]
