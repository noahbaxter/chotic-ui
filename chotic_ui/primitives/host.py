"""Native-host runtime shims.

Make a chotic-ui app render correctly and look like an app regardless of which
terminal (or bundled host) it runs in. Dependency-free and import-safe on every
platform: the Windows-only ctypes calls live behind an os.name guard and are
imported lazily.
"""

import os
import sys


def enable_windows_vt() -> bool:
    """Enable ANSI/VT escape processing on the Windows console.

    chotic-ui writes raw ANSI to stdout. On a default Windows 10 conhost (and
    under ConPTY) a child writing raw VT must enable
    ENABLE_VIRTUAL_TERMINAL_PROCESSING itself or the escapes render as literal
    garbage. No-op (returns False) off Windows or when the console mode cannot
    be read/set (e.g. redirected stdout).

    Returns True if VT processing is enabled after the call, else False.
    """
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        STD_OUTPUT_HANDLE = -11

        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if not kernel32.SetConsoleMode(handle, new_mode):
            return False
        return True
    except Exception:
        return False


def set_window_title(title: str) -> None:
    """Set the terminal/host window title via OSC 2. Honored by every modern
    terminal and by the bundled WezTerm host, identically across OSes. Uses the
    BEL (\\x07) string terminator for the widest compatibility."""
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()


def bootstrap(title: str | None = None) -> None:
    """Call once at app startup, before any TUI rendering. Enables Windows VT
    processing and, if given, sets the host window title. Safe to call on every
    platform and in headless/redirected contexts."""
    enable_windows_vt()
    if title:
        set_window_title(title)
