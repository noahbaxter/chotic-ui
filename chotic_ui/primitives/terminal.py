"""
Terminal utilities for DM Chart Sync.

Handles terminal size, clearing, and progress display.
"""

import os
import re
import unicodedata

ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_PATTERN.sub('', text)


def set_terminal_size(cols: int = 90, rows: int = 40):
    """
    Set terminal window size.

    Args:
        cols: Number of columns (width)
        rows: Number of rows (height)
    """
    try:
        if os.name == 'nt':
            # Windows: use mode command (may fail if not in a proper console)
            import subprocess
            subprocess.run(
                f'mode con: cols={cols} lines={rows}',
                shell=True,
                capture_output=True
            )
        else:
            # macOS/Linux: use ANSI escape sequence
            # \x1b[8;{rows};{cols}t sets window size
            print(f'\x1b[8;{rows};{cols}t', end='', flush=True)
    except Exception:
        pass  # Fail silently if terminal resize isn't supported


def clear_screen():
    """Clear the terminal screen using ANSI escape codes."""
    import sys
    # Use sys.__stdout__ to bypass any wrappers (like TeeOutput)
    # \033[H moves cursor home, \033[2J clears screen, \033[3J clears scrollback
    out = sys.__stdout__ if sys.__stdout__ else sys.stdout
    out.write("\033[H\033[2J\033[3J")
    out.flush()


def get_terminal_width() -> int:
    """Get terminal width, with fallback."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def char_width(ch: str) -> int:
    """Terminal columns one character takes: 2 for CJK and other wide glyphs,
    0 for combining marks and joiners, else 1. Counting a wide glyph as one
    makes a line longer than it looks, so it wraps and the frame shifts."""
    if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text: str) -> int:
    """Columns plain text (no ANSI) takes on screen."""
    return sum(char_width(ch) for ch in text)


def _cut(text: str, columns: int) -> str:
    """The longest prefix of plain text within `columns`."""
    used = 0
    for i, ch in enumerate(text):
        used += char_width(ch)
        if used > columns:
            return text[:i]
    return text


def truncate_text(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate text to max_len columns, adding suffix if truncated. Returns plain text (no ANSI)."""
    text = strip_ansi(text)  # Strip first - colors should be added after truncation, not before
    if display_width(text) <= max_len:
        return text
    if max_len <= len(suffix):
        return _cut(text, max_len)
    return _cut(text, max_len - len(suffix)) + suffix


def visible_len(text: str) -> int:
    """Printable width of text in columns, ignoring ANSI color codes."""
    return display_width(strip_ansi(text))


def truncate_ansi(text: str, max_visible: int) -> str:
    """Truncate to max_visible columns, preserving ANSI codes,
    appending an ellipsis when truncated."""
    if visible_len(text) <= max_visible:
        return text
    if max_visible <= 1:
        return "…"
    target = max_visible - 1
    out, visible, i = [], 0, 0
    while i < len(text):
        if text[i] == "\x1b":
            j = i + 1
            while j < len(text) and text[j] != "m":
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
            continue
        width = char_width(text[i])
        if visible + width > target:
            out.append("…")
            break
        out.append(text[i])
        visible += width
        i += 1
    return "".join(out)


def fit_to_window(text: str, cols: int, rows: int) -> str:
    """A full-screen frame cut to the window: no row wider than `cols` and no
    more than `rows` of them, each ended with erase-to-end-of-line. A row that
    wraps, or a frame taller than the window, scrolls on every repaint, so a
    small window loses the edges instead."""
    lines = text.split("\n")[:max(rows, 1)]
    return "\033[K\n".join(truncate_ansi(line, cols) for line in lines)


def pad_right(text: str, width: int) -> str:
    """Right-pad to `width` columns (no truncating), counting wide glyphs as two."""
    return text + " " * max(0, width - visible_len(text))


def pad_to(text: str, width: int) -> str:
    """Truncate (ANSI-aware) to width, then right-pad with spaces to width."""
    text = truncate_ansi(text, width)
    return text + " " * (width - visible_len(text))


def get_available_width(reserved: int = 0, min_width: int = 20) -> int:
    """Get available terminal width minus reserved chars."""
    return max(min_width, get_terminal_width() - reserved)


def print_progress(message: str, prefix: str = "  "):
    """
    Print a progress message that overwrites the previous line.

    Handles narrow terminals by truncating and using ANSI clear codes.
    """
    width = get_terminal_width()
    full_msg = f"{prefix}{message}"

    # Truncate if too long
    if len(strip_ansi(full_msg)) >= width:
        full_msg = truncate_text(full_msg, width - 1)

    # Clear line and print (\033[2K clears entire line)
    print(f"\033[2K\r{full_msg}", end="", flush=True)


def print_long_path_warning(count: int):
    """Print Windows long path warning with registry fix instructions."""
    print(f"  WARNING: {count} files skipped due to path length > 260 chars")
    print(f"  To fix: Enable long paths in Windows Registry:")
    print(f"    HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem")
    print(f"    Set LongPathsEnabled to 1")
    print(f"  IMPORTANT: You must restart your computer after changing this setting!")


SECTION_WIDTH = 50


def print_section_header(name: str, width: int = SECTION_WIDTH):
    """Print a styled section header using box-drawing characters."""
    from .colors import Colors
    c = Colors
    header = f"━━━ {name} "
    header += "━" * max(5, width - len(header))
    print(f"\n{c.BOLD}{header}{c.RESET}")


def make_separator(char: str = "━", width: int = SECTION_WIDTH) -> str:
    """Create a horizontal separator line string."""
    return char * width


def print_separator(char: str = "━", width: int = SECTION_WIDTH):
    """Print a horizontal separator line."""
    print(make_separator(char, width))
