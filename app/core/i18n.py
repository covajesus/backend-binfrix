"""Traducción de mensajes API según Accept-Language (es | en)."""

from __future__ import annotations

ALLOWED_LOCALES = frozenset({"es", "en"})
DEFAULT_LOCALE = "es"

# Mensajes exactos emitidos por la API (español → inglés).
_API_MESSAGES: dict[str, str] = {
    "Recurso no encontrado": "Resource not found",
    "Acceso denegado": "Access denied",
    "Conflicto con el estado actual": "Conflict with current state",
    "Tenant no definido": "Tenant not defined",
    "Ya existe licencia para este producto": "A license already exists for this product",
    "Rol no válido": "Invalid role",
    "El slug ya está en uso": "Slug is already in use",
    "El usuario ya pertenece al tenant": "User already belongs to this tenant",
    "La categoría tiene productos asociados": "Category has associated products",
}

_PREFIX_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("Red social no válida:", "Invalid social network:"),
    ("Plantilla no válida:", "Invalid template:"),
    ("Idioma no válido:", "Invalid locale:"),
)


def resolve_locale(accept_language: str | None) -> str:
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        token = part.strip().split(";")[0].lower()
        if token.startswith("en"):
            return "en"
        if token.startswith("es"):
            return "es"
    return DEFAULT_LOCALE


def translate_api_message(message: str, locale: str) -> str:
    if locale == "es" or not message:
        return message
    if message in _API_MESSAGES:
        return _API_MESSAGES[message]
    for prefix_es, prefix_en in _PREFIX_TRANSLATIONS:
        if message.startswith(prefix_es):
            return prefix_en + message[len(prefix_es):]
    return message
