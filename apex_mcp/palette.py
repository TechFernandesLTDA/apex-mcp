"""Unified color palette for all visual, chart, and UI tools.

Provides named color constants, palette generators, and theme-aware
color resolution. All chart_tools, ui_tools, and visual_tools should
use this module instead of inline color dictionaries.
"""
from __future__ import annotations

# ── Named brand colors ────────────────────────────────────────────────────────
COLORS: dict[str, str] = {
    # Brand
    "primary": "#1E88E5",
    "secondary": "#43A047",
    "accent": "#FF9800",
    "danger": "#E53935",
    "warning": "#FFA726",
    "success": "#43A047",
    "info": "#29B6F6",
    "muted": "#90A4AE",
    # Named colors
    "blue": "#1E88E5",
    "green": "#43A047",
    "orange": "#FF9800",
    "red": "#E53935",
    "purple": "#8E24AA",
    "teal": "#00897B",
    "indigo": "#3949AB",
    "amber": "#FFB300",
    "cyan": "#00ACC1",
    "pink": "#D81B60",
    "lime": "#7CB342",
    "brown": "#6D4C41",
    "grey": "#78909C",
    "navy": "#1A237E",
    "gold": "#F9A825",
    "coral": "#FF7043",
    # Unimed legacy
    "unimed": "#00995D",
}

# ── Pre-built palettes ────────────────────────────────────────────────────────
PALETTES: dict[str, list[str]] = {
    "default": ["#1E88E5", "#43A047", "#FF9800", "#E53935", "#8E24AA", "#00897B", "#3949AB", "#FFB300"],
    "cool": ["#1E88E5", "#29B6F6", "#00ACC1", "#00897B", "#3949AB", "#7C4DFF", "#448AFF", "#00BCD4"],
    "warm": ["#E53935", "#FF9800", "#FFB300", "#FF7043", "#F9A825", "#D81B60", "#FF5722", "#FFA726"],
    "earth": ["#6D4C41", "#8D6E63", "#795548", "#A1887F", "#BCAAA4", "#4E342E", "#3E2723", "#D7CCC8"],
    "pastel": ["#90CAF9", "#A5D6A7", "#FFCC80", "#EF9A9A", "#CE93D8", "#80CBC4", "#9FA8DA", "#FFE082"],
    "monochrome": ["#263238", "#37474F", "#455A64", "#546E7A", "#607D8B", "#78909C", "#90A4AE", "#B0BEC5"],
    "corporate": ["#1565C0", "#0D47A1", "#1976D2", "#1E88E5", "#2196F3", "#42A5F5", "#64B5F6", "#90CAF9"],
    "rainbow": ["#E53935", "#FF9800", "#FFB300", "#43A047", "#1E88E5", "#3949AB", "#8E24AA", "#D81B60"],
    "unimed": ["#00995D", "#00B36B", "#33CC99", "#66DDAA", "#009688", "#4DB6AC", "#80CBC4", "#B2DFDB"],
}


def resolve_color(color: str) -> str:
    """Resolve a color name or hex code to a hex string.

    Accepts: named color ("blue"), hex ("#1E88E5"), or palette:index ("default:0").
    Returns: hex color string.
    """
    if not color:
        return COLORS["primary"]
    color = color.strip()
    # Direct hex
    if color.startswith("#"):
        return color
    # Named color
    lower = color.lower()
    if lower in COLORS:
        return COLORS[lower]
    # Palette:index format
    if ":" in lower:
        parts = lower.split(":", 1)
        palette_name = parts[0]
        try:
            idx = int(parts[1])
        except (ValueError, IndexError):
            return COLORS["primary"]
        palette = PALETTES.get(palette_name, PALETTES["default"])
        return palette[idx % len(palette)]
    return COLORS.get(lower, color)


def resolve_palette(palette: str | list[str] | None, size: int = 8) -> list[str]:
    """Resolve a palette name or list of colors to a list of hex strings.

    Args:
        palette: Named palette ("cool"), list of hex colors, or None for default.
        size: Number of colors needed (cycles if palette is shorter).
    Returns:
        List of hex color strings.
    """
    if palette is None:
        colors = PALETTES["default"]
    elif isinstance(palette, str):
        colors = PALETTES.get(palette.lower(), PALETTES["default"])
    elif isinstance(palette, list):
        colors = [resolve_color(c) for c in palette]
    else:
        colors = PALETTES["default"]
    # Cycle to fill requested size
    if len(colors) == 0:
        colors = PALETTES["default"]
    result = []
    for i in range(size):
        result.append(colors[i % len(colors)])
    return result


def css_gradient(color1: str, color2: str, direction: str = "135deg") -> str:
    """Generate a CSS linear gradient string."""
    c1 = resolve_color(color1)
    c2 = resolve_color(color2)
    return f"linear-gradient({direction}, {c1}, {c2})"
