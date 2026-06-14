import os
import sys

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
