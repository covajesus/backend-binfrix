"""Colores del storefront — defaults por plantilla y validación."""

import re

THEME_COLOR_KEYS = (
    "header_background",
    "header_text",
    "top_bar_background",
    "top_bar_text",
    "nav_background",
    "nav_text",
    "nav_hover",
    "accent",
    "accent_hover",
    "button_primary_background",
    "button_primary_text",
    "footer_background",
    "footer_text",
    "page_background",
    "page_text",
)

_HEX_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")

DEFAULT_THEME_BY_TEMPLATE: dict[str, dict[str, str]] = {
    "sports": {
        "header_background": "#ffffff",
        "header_text": "#111111",
        "top_bar_background": "#111111",
        "top_bar_text": "#ffffff",
        "nav_background": "#ffffff",
        "nav_text": "#111111",
        "nav_hover": "#fa5400",
        "accent": "#fa5400",
        "accent_hover": "#e04a00",
        "button_primary_background": "#111111",
        "button_primary_text": "#ffffff",
        "footer_background": "#111111",
        "footer_text": "#ffffff",
        "page_background": "#ffffff",
        "page_text": "#111111",
    },
    "industrial-kitchen": {
        "header_background": "#ffffff",
        "header_text": "#111827",
        "top_bar_background": "#0f172a",
        "top_bar_text": "#f8fafc",
        "nav_background": "#ffffff",
        "nav_text": "#111827",
        "nav_hover": "#b91c3c",
        "accent": "#b91c3c",
        "accent_hover": "#991b1b",
        "button_primary_background": "#b91c3c",
        "button_primary_text": "#ffffff",
        "footer_background": "#0f172a",
        "footer_text": "#f8fafc",
        "page_background": "#f8fafc",
        "page_text": "#111827",
    },
    "electronics": {
        "header_background": "#0b1220",
        "header_text": "#f8fafc",
        "top_bar_background": "#0b1220",
        "top_bar_text": "#94a3b8",
        "nav_background": "#0b1220",
        "nav_text": "#94a3b8",
        "nav_hover": "#00d4ff",
        "accent": "#00d4ff",
        "accent_hover": "#00b8db",
        "button_primary_background": "#00d4ff",
        "button_primary_text": "#0b1220",
        "footer_background": "#020617",
        "footer_text": "#94a3b8",
        "page_background": "#0f172a",
        "page_text": "#f8fafc",
    },
}


def normalize_hex_color(value: str) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if not _HEX_RE.match(raw):
        return None
    if len(raw) == 4:
        r, g, b = raw[1], raw[2], raw[3]
        return f"#{r}{r}{g}{g}{b}{b}".lower()
    return raw.lower()


def default_theme_for_template(template_id: str) -> dict[str, str]:
    return dict(
        DEFAULT_THEME_BY_TEMPLATE.get(template_id, DEFAULT_THEME_BY_TEMPLATE["sports"])
    )


def merge_theme_colors(
    template_id: str,
    stored: dict | None,
) -> dict[str, str]:
    merged = default_theme_for_template(template_id)
    if not stored:
        return merged
    for key in THEME_COLOR_KEYS:
        if key not in stored:
            continue
        normalized = normalize_hex_color(str(stored.get(key, "")))
        if normalized:
            merged[key] = normalized
    return merged


def serialize_theme_colors_update(colors: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in THEME_COLOR_KEYS:
        if key not in colors:
            continue
        normalized = normalize_hex_color(str(colors[key]))
        if normalized:
            result[key] = normalized
    return result
