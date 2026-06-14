import os

from chotic_ui.primitives import host


def test_enable_windows_vt_returns_bool_and_never_raises():
    result = host.enable_windows_vt()
    assert isinstance(result, bool)


def test_enable_windows_vt_is_noop_off_windows():
    if os.name != "nt":
        assert host.enable_windows_vt() is False
