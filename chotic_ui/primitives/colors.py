"""
Shared color definitions for terminal output.

Accent colors are named by ROLE, not hue, so the names stay correct across
every theme:
  PRIMARY    interactive accent (hotkeys, prompts, key actions, cursor)
  SELECTION  the ▸ pointer on the selected row
  BORDER     box frames

Fixed status colors (ERROR/SUCCESS/INFO) do not change with the theme.
"""


# -- Theme definitions --
# Each theme: (role_accents_dict, gradient_list)

_THEME_ORDER = [
    "gemini", "flame", "ocean", "synthwave", "forest", "frost", "sunset", "mono",
    "dracula", "nord", "gruvbox", "catppuccin",
    "rose-pine", "tokyo-night", "kanagawa", "everforest", "one-dark", "solarized",
]

_THEME_ACCENTS = {
    "gemini": {
        "PRIMARY": (167, 139, 250),
        "SELECTION": (244, 114, 182),
        "BORDER": (99, 102, 241),
    },
    "flame": {
        "PRIMARY": (255, 175, 45),
        "SELECTION": (252, 130, 20),
        "BORDER": (240, 90, 15),
    },
    "ocean": {
        "PRIMARY": (110, 230, 235),
        "SELECTION": (80, 220, 235),
        "BORDER": (30, 150, 215),
    },
    "synthwave": {
        "PRIMARY": (200, 150, 210),
        "SELECTION": (245, 75, 110),
        "BORDER": (210, 30, 160),
    },
    "forest": {
        "PRIMARY": (130, 232, 140),
        "SELECTION": (100, 222, 115),
        "BORDER": (40, 178, 60),
    },
    "frost": {
        "PRIMARY": (190, 222, 244),
        "SELECTION": (208, 232, 248),
        "BORDER": (150, 195, 228),
    },
    "sunset": {
        "PRIMARY": (255, 185, 50),
        "SELECTION": (250, 80, 30),
        "BORDER": (235, 40, 45),
    },
    "mono": {
        "PRIMARY": (225, 228, 231),
        "SELECTION": (210, 214, 218),
        "BORDER": (165, 170, 175),
    },
    "dracula": {
        "PRIMARY": (189, 147, 249),
        "SELECTION": (255, 121, 198),
        "BORDER": (98, 114, 164),
    },
    "nord": {
        "PRIMARY": (136, 192, 208),
        "SELECTION": (180, 142, 173),
        "BORDER": (76, 86, 106),
    },
    "gruvbox": {
        "PRIMARY": (250, 189, 47),
        "SELECTION": (254, 128, 25),
        "BORDER": (146, 131, 116),
    },
    "catppuccin": {
        "PRIMARY": (203, 166, 247),
        "SELECTION": (245, 194, 231),
        "BORDER": (108, 112, 134),
    },
    "rose-pine": {
        "PRIMARY": (196, 167, 231),    # iris
        "SELECTION": (235, 111, 146),  # love
        "BORDER": (110, 106, 134),     # muted
    },
    "tokyo-night": {
        "PRIMARY": (122, 162, 247),    # blue
        "SELECTION": (187, 154, 247),  # magenta
        "BORDER": (86, 95, 137),       # comment
    },
    "kanagawa": {
        "PRIMARY": (126, 156, 216),    # crystal blue
        "SELECTION": (210, 126, 153),  # sakura pink
        "BORDER": (101, 133, 148),     # dragon blue
    },
    "everforest": {
        "PRIMARY": (167, 192, 128),    # green
        "SELECTION": (230, 152, 117),  # orange
        "BORDER": (133, 146, 137),     # grey
    },
    "one-dark": {
        "PRIMARY": (97, 175, 239),     # blue
        "SELECTION": (198, 120, 221),  # purple
        "BORDER": (92, 99, 112),       # comment
    },
    "solarized": {
        "PRIMARY": (38, 139, 210),     # blue
        "SELECTION": (211, 54, 130),   # magenta
        "BORDER": (88, 110, 117),      # base01
    },
}

_THEME_GRADIENTS = {
    "gemini": [
        (138, 43, 226),   # Blue-violet
        (123, 44, 191),   # Purple
        (108, 45, 156),   # Deep purple
        (93, 63, 211),    # Slate blue
        (79, 70, 229),    # Indigo
        (99, 102, 241),   # Light indigo
        (129, 140, 248),  # Periwinkle
        (167, 139, 250),  # Light purple
        (196, 118, 232),  # Orchid
        (232, 121, 197),  # Pink
        (244, 114, 182),  # Hot pink
        (251, 113, 133),  # Rose
    ],
    "flame": [
        (120, 10, 5),     # Deep maroon
        (155, 20, 8),     # Dark crimson
        (190, 30, 8),     # Crimson
        (215, 45, 8),     # Blood red
        (230, 60, 10),    # Red
        (240, 80, 12),    # Red-orange
        (248, 105, 15),   # Dark orange
        (252, 130, 20),   # Orange
        (254, 155, 30),   # Warm orange
        (255, 175, 45),   # Amber
        (255, 195, 65),   # Golden amber
        (255, 210, 90),   # Warm gold
    ],
    "ocean": [
        (10, 20, 80),     # Deep navy
        (15, 40, 120),    # Dark blue
        (20, 60, 155),    # Blue
        (20, 85, 180),    # Medium blue
        (25, 115, 200),   # Steel blue
        (30, 150, 215),   # Sky blue
        (40, 180, 225),   # Light blue
        (55, 205, 230),   # Cyan
        (80, 220, 235),   # Light cyan
        (110, 230, 235),  # Seafoam
        (150, 240, 238),  # Pale seafoam
        (190, 248, 242),  # Mint
    ],
    "synthwave": [
        (60, 10, 120),    # Deep purple
        (90, 15, 150),    # Purple
        (130, 20, 170),   # Violet
        (170, 25, 175),   # Magenta
        (210, 30, 160),   # Hot magenta
        (235, 50, 130),   # Pink
        (245, 75, 110),   # Salmon
        (250, 100, 120),  # Rose
        (240, 130, 160),  # Light rose
        (200, 150, 210),  # Lavender
        (140, 170, 240),  # Periwinkle
        (90, 200, 250),   # Electric blue
    ],
    "forest": [
        (10, 60, 20),     # Dark forest
        (15, 85, 30),     # Forest green
        (20, 110, 35),    # Green
        (25, 135, 40),    # Medium green
        (30, 158, 50),    # Kelly green
        (40, 178, 60),    # Bright green
        (55, 195, 75),    # Light green
        (75, 210, 95),    # Lime green
        (100, 222, 115),  # Spring green
        (130, 232, 140),  # Mint green
        (165, 242, 170),  # Pale green
        (200, 250, 200),  # Honeydew
    ],
    "frost": [
        (60, 80, 120),    # Steel
        (75, 100, 150),   # Slate blue
        (90, 125, 180),   # Medium slate
        (110, 150, 200),  # Light slate
        (130, 175, 215),  # Sky
        (150, 195, 228),  # Pale blue
        (170, 210, 238),  # Ice blue
        (190, 222, 244),  # Light ice
        (208, 232, 248),  # Frost
        (222, 240, 252),  # Near white blue
        (235, 246, 254),  # Faint blue
        (245, 250, 255),  # Ghost white
    ],
    "sunset": [
        (80, 20, 120),    # Deep purple
        (110, 25, 130),   # Purple
        (150, 25, 120),   # Plum
        (185, 30, 95),    # Magenta-red
        (215, 35, 65),    # Crimson
        (235, 40, 45),    # Red
        (245, 55, 35),    # Scarlet
        (250, 80, 30),    # Red-orange
        (252, 115, 30),   # Dark orange
        (254, 150, 35),   # Orange
        (255, 185, 50),   # Amber
        (255, 215, 75),   # Warm gold
    ],
    "mono": [
        (70, 75, 80),     # Dark gray
        (90, 95, 100),    # Gray
        (110, 115, 120),  # Medium gray
        (130, 135, 140),  # Silver-gray
        (148, 153, 158),  # Silver
        (165, 170, 175),  # Light silver
        (180, 185, 190),  # Pale silver
        (195, 200, 205),  # Light gray
        (210, 214, 218),  # Near white
        (225, 228, 231),  # Faint gray
        (238, 240, 242),  # Ghost gray
        (248, 249, 250),  # Almost white
    ],
    "dracula": [
        (98, 114, 164),   # Comment blue
        (130, 120, 200),  # Muted violet
        (160, 135, 235),  # Light violet
        (189, 147, 249),  # Purple
        (212, 138, 232),  # Orchid
        (235, 128, 214),  # Magenta
        (255, 121, 198),  # Pink
        (255, 145, 175),  # Rose
        (255, 165, 145),  # Coral
        (255, 184, 108),  # Orange
        (245, 215, 125),  # Warm yellow
        (241, 250, 140),  # Yellow
    ],
    "nord": [
        (59, 66, 82),     # Polar night
        (76, 86, 106),    # Slate
        (94, 129, 172),   # Frost deep
        (110, 148, 185),  # Frost blue
        (129, 161, 193),  # Frost
        (136, 192, 208),  # Frost cyan
        (143, 188, 187),  # Frost teal
        (163, 190, 140),  # Aurora green
        (180, 142, 173),  # Aurora purple
        (200, 195, 175),  # Pale
        (216, 222, 233),  # Snow
        (236, 239, 244),  # Bright snow
    ],
    "gruvbox": [
        (157, 0, 6),      # Dark red
        (204, 36, 29),    # Red
        (231, 60, 35),    # Bright red
        (251, 73, 52),    # Coral red
        (253, 110, 38),   # Red-orange
        (254, 128, 25),   # Orange
        (250, 160, 38),   # Amber
        (250, 189, 47),   # Yellow
        (200, 190, 42),   # Lime
        (184, 187, 38),   # Green
        (142, 192, 124),  # Aqua
        (215, 200, 160),  # Cream
    ],
    "catppuccin": [
        (137, 180, 250),  # Blue
        (180, 190, 254),  # Lavender
        (203, 166, 247),  # Mauve
        (224, 180, 240),  # Light mauve
        (245, 194, 231),  # Pink
        (244, 160, 188),  # Rose
        (243, 139, 168),  # Red
        (247, 160, 150),  # Salmon
        (250, 179, 135),  # Peach
        (249, 226, 175),  # Yellow
        (200, 230, 168),  # Light green
        (148, 226, 213),  # Teal
    ],
    "rose-pine": [
        (49, 116, 143),   # Pine
        (90, 155, 170),   # Teal
        (130, 190, 205),  # Light teal
        (156, 207, 216),  # Foam
        (180, 190, 225),  # Pale iris
        (196, 167, 231),  # Iris
        (220, 178, 210),  # Mauve rose
        (235, 188, 186),  # Rose
        (240, 172, 160),  # Coral
        (246, 193, 119),  # Gold
        (240, 150, 150),  # Warm rose
        (235, 111, 146),  # Love
    ],
    "tokyo-night": [
        (86, 95, 137),    # Comment
        (110, 135, 205),  # Dim blue
        (122, 162, 247),  # Blue
        (125, 207, 255),  # Cyan
        (115, 218, 202),  # Teal
        (158, 206, 106),  # Green
        (224, 175, 104),  # Yellow
        (255, 158, 100),  # Orange
        (247, 118, 142),  # Red
        (210, 135, 195),  # Pink-magenta
        (187, 154, 247),  # Magenta
        (160, 170, 240),  # Periwinkle
    ],
    "kanagawa": [
        (101, 133, 148),  # Dragon blue
        (126, 156, 216),  # Crystal blue
        (127, 180, 202),  # Spring blue
        (122, 168, 159),  # Wave aqua
        (152, 187, 108),  # Spring green
        (200, 192, 147),  # Old white
        (230, 195, 132),  # Carp yellow
        (255, 160, 102),  # Surimi orange
        (210, 126, 153),  # Sakura pink
        (185, 115, 150),  # Plum
        (149, 127, 184),  # Oni violet
        (165, 150, 200),  # Light violet
    ],
    "everforest": [
        (133, 146, 137),  # Grey
        (127, 187, 179),  # Blue
        (131, 192, 146),  # Aqua
        (167, 192, 128),  # Green
        (195, 195, 140),  # Lime
        (219, 188, 127),  # Yellow
        (230, 152, 117),  # Orange
        (230, 126, 128),  # Red
        (220, 140, 160),  # Pink-red
        (214, 153, 182),  # Purple
        (210, 180, 175),  # Mauve
        (211, 198, 170),  # Foreground
    ],
    "one-dark": [
        (92, 99, 112),    # Comment
        (97, 175, 239),   # Blue
        (86, 182, 194),   # Cyan
        (120, 195, 150),  # Teal-green
        (152, 195, 121),  # Green
        (229, 192, 123),  # Yellow
        (209, 154, 102),  # Orange
        (224, 108, 117),  # Red
        (212, 116, 175),  # Pink
        (198, 120, 221),  # Purple
        (150, 145, 230),  # Violet
        (171, 178, 191),  # Foreground
    ],
    "solarized": [
        (38, 139, 210),   # Blue
        (42, 161, 152),   # Cyan
        (90, 160, 80),    # Blue-green
        (133, 153, 0),    # Green
        (181, 137, 0),    # Yellow
        (203, 75, 22),    # Orange
        (220, 50, 47),    # Red
        (216, 52, 90),    # Red-magenta
        (211, 54, 130),   # Magenta
        (160, 85, 160),   # Violet-magenta
        (108, 113, 196),  # Violet
        (70, 125, 205),   # Indigo-blue
    ],
}


# -- Active theme state --

# Dev-only theme tweaking. Flip to True to expose the `T` theme-cycle hotkey in
# menus (cycles + rerenders live). Ships off; not meant for end users.
THEME_SWITCHER_ENABLED = False

_active_theme_idx = _THEME_ORDER.index("sunset")

GRADIENT_COLORS = list(_THEME_GRADIENTS[_THEME_ORDER[_active_theme_idx]])


def _esc(r, g, b):
    return f"\x1b[38;2;{r};{g};{b}m"


class Colors:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    ITALIC = "\x1b[3m"
    DIM_HOVER = "\x1b[38;2;140;150;160m"
    MUTED = "\x1b[38;2;148;163;184m"
    MUTED_DIM = "\x1b[38;2;90;100;110m"
    STALE = "\x1b[38;2;100;110;125m"
    # Fixed status colors (theme-independent)
    ERROR = "\x1b[38;2;239;68;68m"
    SUCCESS = "\x1b[38;2;34;197;94m"
    INFO = "\x1b[38;2;34;211;238m"
    INFO_DIM = "\x1b[38;2;20;110;130m"
    # Theme-dependent accents by role (set by _apply_theme)
    PRIMARY = ""
    SELECTION = ""
    BORDER = ""


def _apply_theme():
    """Apply the current theme to Colors class and GRADIENT_COLORS list."""
    name = _THEME_ORDER[_active_theme_idx]
    accents = _THEME_ACCENTS[name]
    for attr, (r, g, b) in accents.items():
        setattr(Colors, attr, _esc(r, g, b))
    GRADIENT_COLORS.clear()
    GRADIENT_COLORS.extend(_THEME_GRADIENTS[name])


_apply_theme()


def get_theme_name() -> str:
    return _THEME_ORDER[_active_theme_idx]


def cycle_theme() -> str:
    """Advance to next theme. Returns the new theme name."""
    global _active_theme_idx
    _active_theme_idx = (_active_theme_idx + 1) % len(_THEME_ORDER)
    _apply_theme()
    return get_theme_name()


def set_theme(name: str) -> str:
    """Set the active theme by name. Apps call this once at startup to pick
    their look. Returns the active theme name."""
    global _active_theme_idx
    if name not in _THEME_ORDER:
        raise ValueError(f"unknown theme {name!r}; choices: {', '.join(_THEME_ORDER)}")
    _active_theme_idx = _THEME_ORDER.index(name)
    _apply_theme()
    return get_theme_name()


def rgb(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def get_gradient_color(pos: float) -> tuple:
    """Get interpolated color at position 0.0-1.0."""
    pos = max(0.0, min(1.0, pos))
    scaled = pos * (len(GRADIENT_COLORS) - 1)
    idx = int(scaled)
    if idx >= len(GRADIENT_COLORS) - 1:
        return GRADIENT_COLORS[-1]
    return lerp_color(GRADIENT_COLORS[idx], GRADIENT_COLORS[idx + 1], scaled - idx)
