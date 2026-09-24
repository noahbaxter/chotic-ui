"""The detail a host draws after the version, under the banner.

It is called on every draw rather than cached with the art: what a host puts
there can change while the app runs, and the art cache would keep showing the
value from the first frame forever.
"""

import io
import re
from contextlib import redirect_stdout

import pytest

from chotic_ui.components.header import configure_header, header_height, print_header

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BANNER = "###\n# #\n###"


@pytest.fixture(autouse=True)
def reset():
    yield
    configure_header("", "")


def drawn():
    out = io.StringIO()
    with redirect_stdout(out):
        print_header()
    return CSI.sub("", out.getvalue())


def drawn_rows():
    """Rows on screen: everything print wrote, less the newline that ends the
    last one. The trailing blank row is part of the banner and counts."""
    return drawn().split("\n")[:-1]


def test_the_detail_follows_the_version():
    configure_header(BANNER, "1.2.3", detail=lambda room: "library → ~/Songs")

    line = next(ln for ln in drawn().split("\n") if "v1.2.3" in ln)
    assert line.endswith("library → ~/Songs")


def test_it_is_asked_again_on_every_draw():
    value = ["first"]
    configure_header(BANNER, "1.2.3", detail=lambda room: value[0])

    assert "first" in drawn()
    value[0] = "second"
    text = drawn()
    assert "second" in text and "first" not in text


def test_it_is_told_how_much_room_there_is(monkeypatch):
    monkeypatch.setattr("chotic_ui.primitives.terminal.get_terminal_width", lambda: 40)
    seen = []
    configure_header(BANNER, "1.2.3", detail=lambda room: seen.append(room) or "x" * 200)

    line = next(ln for ln in drawn().split("\n") if "v1.2.3" in ln)
    assert seen and 0 < seen[0] < 40
    assert len(line) < 40, "a detail longer than its room pushed the line past the edge"


def test_a_broken_detail_does_not_take_the_banner_with_it():
    def explode(room):
        raise RuntimeError("the library went away")

    configure_header(BANNER, "1.2.3", detail=explode)

    assert "v1.2.3" in drawn()


def test_a_detail_alone_still_gets_its_line_counted():
    """Hosts size their frames against header_height; an uncounted line
    scrolls the top of the banner off the screen."""
    configure_header(BANNER, "", detail=lambda room: "library → ~/Songs")

    rows = drawn_rows()
    assert header_height() == len(rows)
    assert any("library" in row for row in rows)


def test_the_text_is_what_gets_printed_and_as_tall_as_it_says():
    """A screen that draws itself puts the banner back from header_text() and
    sizes its frame by header_height(); the two have to agree with print_header."""
    from chotic_ui.components.header import header_text
    configure_header(BANNER, "1.2.3", detail=lambda room: "library → ~/Songs")

    out = io.StringIO()
    with redirect_stdout(out):
        print_header()
    assert header_text() == out.getvalue()
    assert header_text().count("\n") == header_height()


def test_without_a_detail_nothing_changes():
    configure_header(BANNER, "1.2.3")

    rows = drawn_rows()
    assert header_height() == len(rows)
    assert rows[-2].strip() == "v1.2.3"
