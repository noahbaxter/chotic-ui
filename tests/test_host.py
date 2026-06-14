import os

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


def test_bootstrap_with_title_sets_title(capsys):
    host.bootstrap("MyApp")
    out = capsys.readouterr().out
    assert out == "\x1b]2;MyApp\x07"


def test_bootstrap_without_title_emits_nothing(capsys):
    host.bootstrap()
    out = capsys.readouterr().out
    assert out == ""
