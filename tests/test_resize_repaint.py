"""A screen waiting for a key still repaints when the window changes size.
Windows has no SIGWINCH, so without polling the frame sat re-wrapped and stale
until something was pressed."""

import contextlib
import os
import shutil
import sys

from chotic_ui.primitives import KEY_ESC
from chotic_ui.widgets import filter_list as filter_module
from chotic_ui.widgets import menu as menu_module
from chotic_ui.widgets.filter_list import FilterList
from chotic_ui.widgets.menu import Menu, MenuItem

from .test_repaint import _Sink


def _resizing_keys(monkeypatch, module):
    """Window is 80x24; the first wait times out as the window shrinks, the
    second delivers Esc."""
    size = [os.terminal_size((80, 24))]
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): size[0])
    monkeypatch.setattr("chotic_ui.primitives.terminal.get_terminal_width", lambda: size[0].columns)
    monkeypatch.setattr(module, "cbreak_noecho", contextlib.nullcontext)
    sink = _Sink([])
    monkeypatch.setattr(sys, "__stdout__", sink)
    waits = iter(["resize", KEY_ESC])

    def wait(*args, **kwargs):
        step = next(waits)
        if step == "resize":
            size[0] = os.terminal_size((60, 20))
            return None
        return step

    monkeypatch.setattr(module, "getch_with_timeout", wait)
    return sink


def test_a_menu_repaints_when_the_window_is_resized(monkeypatch):
    sink = _resizing_keys(monkeypatch, menu_module)
    menu = Menu(title="Resized menu")
    menu.add_item(MenuItem("One", value=1))
    menu.run()

    assert "".join(sink._sink).count("Resized menu") == 2


def test_a_filter_list_repaints_when_the_window_is_resized(monkeypatch):
    sink = _resizing_keys(monkeypatch, filter_module)
    FilterList([("One", 1)], title="Resized list").run()

    assert "".join(sink._sink).count("Resized list") == 2
