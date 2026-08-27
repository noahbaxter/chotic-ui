"""Native-host runtime shims.

Make a chotic-ui app render correctly and look like an app regardless of which
terminal (or bundled host) it runs in. Dependency-free and import-safe on every
platform: the Windows-only ctypes calls live behind an os.name guard and are
imported lazily.
"""

import atexit
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
    if title and sys.stdout.isatty():
        set_window_title(title)


_alt_screen = False


def _raw_out():
    """The real console, bypassing any stdout wrapper (log tees and the like)."""
    return sys.__stdout__ if sys.__stdout__ else sys.stdout


def enter_alt_screen() -> bool:
    """Switch the terminal to its alternate screen buffer.

    The alternate buffer has no scrollback, so a frame can never scroll off the
    top and a window resize can never pull old content back into view under a
    repaint. It also means the shell the app was launched from comes back
    untouched on exit. No-op (returns False) when stdout is not a terminal or
    the buffer is already active.
    """
    global _alt_screen
    out = _raw_out()
    if _alt_screen or not (out and out.isatty()):
        return False
    out.write("\033[?1049h\033[H\033[2J")
    out.flush()
    _alt_screen = True
    return True


def leave_alt_screen() -> None:
    """Return to the primary screen buffer. Safe to call when not in one."""
    global _alt_screen
    if not _alt_screen:
        return
    _alt_screen = False
    out = _raw_out()
    out.write("\033[?1049l")
    out.flush()


def use_alt_screen() -> bool:
    """Enter the alternate screen and guarantee the app leaves it again.

    A process that dies inside the alternate buffer strands the user looking at
    a frozen frame, so the exit path is wired up here rather than left to the
    caller: atexit covers a normal return and sys.exit, and the excepthook runs
    before the traceback so the traceback lands somewhere visible.
    """
    if not enter_alt_screen():
        return False
    atexit.register(leave_alt_screen)
    previous = sys.excepthook

    def hook(exc_type, exc, tb):
        leave_alt_screen()
        previous(exc_type, exc, tb)

    sys.excepthook = hook
    return True
