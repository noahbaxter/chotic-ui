"""A frame never outgrows the window. A row wider than the window wraps and a
frame taller than it scrolls, and either one wrecks every repaint after it, so
at any size the frame may lose its edges but never overflow."""

import os
import re
import shutil

import pytest

from chotic_ui.components import configure_header
from chotic_ui.primitives.terminal import fit_to_window, visible_len
from chotic_ui.widgets.filter_list import FilterList
from chotic_ui.widgets.menu import Menu, MenuItem
from chotic_ui.widgets.two_pane import TwoPane

from .test_repaint import BANNER, _Sink

SIZES = [(120, 40), (80, 24), (60, 12), (40, 8), (30, 6), (20, 4), (12, 3), (5, 2), (1, 1)]
LABELS = ["Rock Band", "マクロス MACROSS 82-99", "Guitar Hero " * 6, "plain"]


def menu():
    return Menu(title="Pick one", subtitle="a longer subtitle " * 5,
                items=[MenuItem(label=name, value=i) for i, name in enumerate(LABELS * 4)],
                footer="  Esc back")


def filter_list():
    fl = FilterList([(name, i) for i, name in enumerate(LABELS * 4)], title="Pick", subtitle="sub " * 30)
    return lambda: fl._render([(name, i) for i, name in enumerate(LABELS * 4)])


def two_pane():
    pane = TwoPane(
        title="Chart Packs",
        left_rows=lambda: [(lambda f, c, t=t: t, t, True) for t in LABELS * 3],
        right_rows=lambda active, query: [(lambda f, c: "Enable all " * 5, "on", True)],
        footer=lambda: "  S sync\n  Tab panes  Esc quit",
        footer_lines=2,
        fill_height=True,
    )
    return pane.render_once


WIDGETS = {"menu": lambda: menu()._render, "filter_list": filter_list, "two_pane": two_pane}


def draw(render, cols, rows, monkeypatch):
    size = os.terminal_size((cols, rows))
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): size)
    monkeypatch.setattr("chotic_ui.primitives.terminal.get_terminal_width", lambda: cols)
    written = []
    sink = _Sink(written)
    monkeypatch.setattr("sys.stdout", sink)
    monkeypatch.setattr("sys.__stdout__", sink)
    render()
    monkeypatch.undo()
    return "".join(written)


@pytest.mark.parametrize("name", WIDGETS)
@pytest.mark.parametrize("cols,rows", SIZES)
def test_frame_fits_the_window(name, cols, rows, monkeypatch):
    configure_header(BANNER, "1.5.0")
    try:
        out = draw(WIDGETS[name](), cols, rows, monkeypatch)
    finally:
        configure_header("", "")
    lines = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", out).split("\n")
    assert len(lines) <= rows, f"{len(lines)} rows in a {rows}-row window"
    wide = [ln for ln in lines if visible_len(ln) > cols]
    assert not wide, f"row wider than {cols}: {wide[0]!r}"


class TestFitToWindow:
    def test_clips_rows_and_columns(self):
        out = fit_to_window("abcdefghij\nsecond\nthird", 5, 2)
        assert out == "abcd…\033[K\nseco…"

    def test_wide_characters_count_two_columns(self):
        out = fit_to_window("ああああ", 5, 1)
        assert visible_len(out) <= 5

    def test_short_frames_pass_through(self):
        assert fit_to_window("one\ntwo", 80, 24) == "one\033[K\ntwo"
