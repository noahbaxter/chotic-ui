import os
import sys

import pytest

from chotic_ui.primitives import host


def test_enable_windows_vt_returns_bool_and_never_raises():
    result = host.enable_windows_vt()
    assert isinstance(result, bool)


def test_enable_windows_vt_is_noop_off_windows():
    if os.name != "nt":
        assert host.enable_windows_vt() is False


def test_set_window_title_emits_osc2(capsys):
    host.set_window_title("Stemchotic")
    out = capsys.readouterr().out
    assert out == "\x1b]2;Stemchotic\x07"


def test_bootstrap_emits_title_on_a_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    host.bootstrap("MyApp")
    assert capsys.readouterr().out == "\x1b]2;MyApp\x07"


def test_bootstrap_skips_title_when_not_a_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    host.bootstrap("MyApp")
    assert capsys.readouterr().out == ""


def test_bootstrap_without_title_emits_nothing(capsys):
    host.bootstrap()
    assert capsys.readouterr().out == ""


def test_shims_exported_at_top_level():
    import chotic_ui
    assert callable(chotic_ui.bootstrap)
    assert callable(chotic_ui.set_window_title)
    assert callable(chotic_ui.enable_windows_vt)


class FakeConsole:
    def __init__(self, tty=True):
        self.written = []
        self._tty = tty

    def write(self, text):
        self.written.append(text)

    def flush(self):
        pass

    def isatty(self):
        return self._tty

    def text(self):
        return "".join(self.written)


@pytest.fixture
def console(monkeypatch):
    """A fake console in place of the real one, with the alt-screen flag reset
    around the test so one leaving it dirty cannot skew the next."""
    fake = FakeConsole()
    monkeypatch.setattr("sys.__stdout__", fake)
    monkeypatch.setattr(host, "_alt_screen", False)
    yield fake
    host._alt_screen = False


def test_enter_alt_screen_switches_and_clears(console):
    assert host.enter_alt_screen() is True
    assert console.text() == "\x1b[?1049h\x1b[H\x1b[2J"


def test_enter_alt_screen_is_idempotent(console):
    host.enter_alt_screen()
    assert host.enter_alt_screen() is False
    assert console.text().count("\x1b[?1049h") == 1


def test_leave_alt_screen_restores_the_primary_buffer(console):
    host.enter_alt_screen()
    host.leave_alt_screen()
    host.leave_alt_screen()
    assert console.text().endswith("\x1b[?1049l")
    assert console.text().count("\x1b[?1049l") == 1


def test_leave_alt_screen_without_entering_writes_nothing(console):
    host.leave_alt_screen()
    assert console.text() == ""


def test_alt_screen_is_a_noop_when_not_a_tty(monkeypatch):
    fake = FakeConsole(tty=False)
    monkeypatch.setattr("sys.__stdout__", fake)
    monkeypatch.setattr(host, "_alt_screen", False)
    assert host.use_alt_screen() is False
    assert fake.text() == ""


def test_excepthook_leaves_the_buffer_before_the_traceback(console, monkeypatch):
    """A traceback printed inside the alternate buffer is thrown away with it,
    so the process would die with nothing on screen to explain why."""
    order = []
    monkeypatch.setattr(sys, "excepthook", lambda *a: order.append("traceback"))
    assert host.use_alt_screen() is True
    console.written.clear()

    sys.excepthook(RuntimeError, RuntimeError("boom"), None)

    assert console.text() == "\x1b[?1049l"
    assert order == ["traceback"]
    assert host._alt_screen is False
