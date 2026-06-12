"""
chotic-ui - a small raw-terminal TUI toolkit.

Layered: primitives (terminal/keyboard/colors), components (box/header/format),
widgets (Menu, FilterList, ConfirmDialog). Shared across the -chotic apps.

Apps set their banner once with `configure_header(ascii_art, version)`.
"""

from .primitives import (
    clear_screen,
    get_terminal_width,
    print_progress,
    getch,
    input_with_esc,
    wait_for_key,
    wait_with_skip,
    CancelInput,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_ENTER,
    KEY_ESC,
    KEY_SPACE,
    KEY_BACKSPACE,
    Colors,
    rgb,
    set_theme,
    visible_len,
    truncate_ansi,
    pad_to,
)
from .components import (
    configure_header,
    print_header,
    invalidate_header_cache,
    strip_ansi,
    calc_percent,
)
from .widgets import (
    Menu,
    MenuItem,
    MenuDivider,
    MenuGroupHeader,
    MenuAction,
    MenuResult,
    ConfirmDialog,
    FilterList,
)

__version__ = "0.1.0"

__all__ = [
    "clear_screen",
    "get_terminal_width",
    "print_progress",
    "getch",
    "input_with_esc",
    "wait_for_key",
    "wait_with_skip",
    "CancelInput",
    "KEY_UP",
    "KEY_DOWN",
    "KEY_LEFT",
    "KEY_RIGHT",
    "KEY_ENTER",
    "KEY_ESC",
    "KEY_SPACE",
    "KEY_BACKSPACE",
    "Colors",
    "rgb",
    "set_theme",
    "visible_len",
    "truncate_ansi",
    "pad_to",
    "configure_header",
    "print_header",
    "invalidate_header_cache",
    "strip_ansi",
    "calc_percent",
    "Menu",
    "MenuItem",
    "MenuDivider",
    "MenuGroupHeader",
    "MenuAction",
    "MenuResult",
    "ConfirmDialog",
    "FilterList",
]
