"""
Reusable visual building blocks.

Non-interactive components for rendering UI elements.
"""

from .box import (
    BOX_TL,
    BOX_TR,
    BOX_BL,
    BOX_BR,
    BOX_H,
    BOX_V,
    BOX_TL_DIV,
    BOX_TR_DIV,
    box_row,
)
from .header import (
    configure_header,
    print_header,
    invalidate_header_cache,
)
from .formatting import (
    strip_ansi,
    calc_percent,
)

__all__ = [
    # Box drawing
    "BOX_TL",
    "BOX_TR",
    "BOX_BL",
    "BOX_BR",
    "BOX_H",
    "BOX_V",
    "BOX_TL_DIV",
    "BOX_TR_DIV",
    "box_row",
    # Header
    "configure_header",
    "print_header",
    "invalidate_header_cache",
    # Formatting
    "strip_ansi",
    "calc_percent",
]
