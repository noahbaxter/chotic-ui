"""
Application header component.

Generic: the host app supplies its own ASCII banner and version via
`configure_header()`. Renders with a diagonal theme gradient. If never
configured, `print_header()` is a no-op.
"""

from ..primitives import Colors, rgb, get_gradient_color
from ..primitives.colors import get_theme_name, THEME_SWITCHER_ENABLED


_ascii_art = ""
_version = ""
_header_cache = None
_header_theme = None


def configure_header(ascii_art: str, version: str = "") -> None:
    """Set the banner art and version string the app wants rendered."""
    global _ascii_art, _version
    _ascii_art = ascii_art.strip("\n") if ascii_art else ""
    _version = version
    invalidate_header_cache()


def invalidate_header_cache() -> None:
    """Clear cached header (call on terminal resize or theme change)."""
    global _header_cache, _header_theme
    _header_cache = None
    _header_theme = None


def print_header() -> None:
    """Print the configured ASCII header with a diagonal gradient and version."""
    global _header_cache, _header_theme

    if not _ascii_art:
        return

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

        if _version:
            version_line = f" {Colors.DIM}v{_version}{Colors.RESET}"
            if THEME_SWITCHER_ENABLED:
                version_line += f"  {Colors.MUTED}theme: {Colors.PRIMARY}{current_theme}{Colors.RESET}"
            cached_lines.append(version_line)
        cached_lines.append("")
        _header_cache = "\n".join(cached_lines)

    print(f"\n{_header_cache}")
