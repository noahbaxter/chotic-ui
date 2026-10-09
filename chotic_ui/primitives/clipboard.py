"""Read text off the system clipboard, for terminals that hand Ctrl+V to the
app as a keypress instead of pasting."""

import os
import subprocess
import sys


def read_text() -> str:
    """The clipboard's text, or '' when it holds none or cannot be read."""
    try:
        if os.name == "nt":
            return _read_windows()
        if sys.platform == "darwin":
            return _run(["pbpaste"])
        for cmd in (["wl-paste", "-n"], ["xclip", "-selection", "clipboard", "-o"],
                    ["xsel", "-ob"]):
            text = _run(cmd)
            if text:
                return text
    except Exception:
        pass
    return ""


def _run(cmd: list[str]) -> str:
    try:
        done = subprocess.run(cmd, capture_output=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.decode("utf-8", errors="replace") if done.returncode == 0 else ""


def _read_windows() -> str:
    import ctypes
    import time
    from ctypes import wintypes

    CF_UNICODETEXT = 13
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    # Another process may hold the clipboard for a moment.
    for _ in range(10):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.01)
    else:
        return ""
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        locked = kernel32.GlobalLock(handle)
        if not locked:
            return ""
        try:
            return ctypes.wstring_at(locked)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
