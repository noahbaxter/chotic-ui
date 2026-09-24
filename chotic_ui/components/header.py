"""
Application header component.

Generic: the host app supplies its own ASCII banner and version via
`configure_header()`. Renders with a diagonal theme gradient. If never
configured, `print_header()` is a no-op.
"""

from ..primitives import Colors, rgb, get_gradient_color
from ..primitives import terminal
from ..primitives.colors import get_theme_name, THEME_SWITCHER_ENABLED


ERASE_EOL = "\033[K"

_ascii_art = ""
_version = ""
_detail = None
_header_cache = None
_header_theme = None


def configure_header(ascii_art: str, version: str = "", detail=None) -> None:
    """Set the banner art and version string the app wants rendered.

    detail, if given, is a ``(room: int) -> str`` whose result is drawn after
    the version on the same line, given the columns left there. It is called on
    every draw instead of being cached with the art, because what a host puts
    there (where its data lives, say) can change while the app is running, and
    a banner still showing the old value is worse than one showing none.
    """
    global _ascii_art, _version, _detail
    _ascii_art = ascii_art.strip("\n") if ascii_art else ""
    _version = version
    _detail = detail
    invalidate_header_cache()


def invalidate_header_cache() -> None:
    """Clear cached header (call on terminal resize or theme change)."""
    global _header_cache, _header_theme
    _header_cache = None
    _header_theme = None


def header_height() -> int:
    """Display rows print_header() occupies: a leading blank line, the art, the
    version line, and a trailing blank. Callers size their own frames against
    this rather than hardcoding a guess -- the art is per-app, and being wrong
    here scrolls the banner off the top of the screen."""
    if not _ascii_art:
        return 0
    return 1 + len(_ascii_art.split("\n")) + (1 if _has_status_line() else 0) + 1


def _has_status_line() -> bool:
    return bool(_version or _detail)


def print_header() -> None:
    """Print the configured ASCII header with a diagonal gradient and version."""
    print(header_text(), end="")


def header_text() -> str:
    """The header exactly as print_header() writes it: header_height() rows,
    ending in a newline. "" if never configured. For a screen that draws
    itself and has to put the banner back after clearing."""
    global _header_cache, _header_theme

    if not _ascii_art:
        return ""

    current_theme = get_theme_name()
    if _header_cache is None or _header_theme != current_theme:
        _header_theme = current_theme

        lines = _ascii_art.split("\n")
        total = len(lines)
        cached_lines = []

        for row, line in enumerate(lines):
            result = []
            for col, char in enumerate(line):
                if char != " ":
                    pos = (row / total) * 0.4 + (col / max(1, len(line))) * 0.6
                    r, g, b = get_gradient_color(pos)
                    result.append(f"{rgb(r, g, b)}{char}")
                else:
                    result.append(char)
            cached_lines.append("".join(result) + Colors.RESET)

        # Each line erases to end of line. Callers repaint in place from the
        # home position, so a banner line that stops at its own last glyph
        # leaves the previous frame's text sitting to the right of it.
        _header_cache = "\n".join(line + ERASE_EOL for line in cached_lines)

    lines = [_header_cache]
    if _has_status_line():
        lines.append(_status_line(current_theme) + ERASE_EOL)
    lines.append(ERASE_EOL)
    return f"{ERASE_EOL}\n" + "\n".join(lines) + "\n"


def _status_line(theme: str) -> str:
    """Version, theme, and whatever the host's detail says, on one line.

    Built on every draw, unlike the art: the detail can change underneath it.
    """
    line = f" {Colors.DIM}v{_version}{Colors.RESET}" if _version else ""
    if THEME_SWITCHER_ENABLED:
        line += f"  {Colors.MUTED}theme: {Colors.PRIMARY}{theme}{Colors.RESET}"
    if _detail:
        gap = "   " if line else " "
        room = terminal.get_terminal_width() - terminal.visible_len(line) - len(gap) - 1
        try:
            extra = _detail(max(0, room)) if room > 0 else ""
        except Exception:
            extra = ""  # a broken detail must not take the banner down with it
        if extra:
            line += gap + terminal.truncate_ansi(extra, room)
    return line
