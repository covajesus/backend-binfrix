"""Validación y parseo de paquetes ZIP de plantillas personalizadas."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass

from app.core.exceptions import ConflictError
from app.schemas.store_settings import ALLOWED_STOREFRONT_TEMPLATES
from app.utils.store_theme import THEME_COLOR_KEYS, normalize_hex_color

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")
_MAX_CSS_BYTES = 256 * 1024
_MAX_PREVIEW_BYTES = 512 * 1024


@dataclass(frozen=True)
class ParsedTemplatePackage:
    slug: str
    name: str
    description: str
    extends_template: str
    theme_colors: dict[str, str]
    custom_css: str
    preview_image: str


def _find_manifest_name(names: list[str]) -> str | None:
    for name in names:
        normalized = name.replace("\\", "/").strip("/")
        if normalized == "manifest.json" or normalized.endswith("/manifest.json"):
            return name
    return None


def _read_zip_text(zf: zipfile.ZipFile, name: str) -> str:
    with zf.open(name) as raw:
        data = raw.read()
    return data.decode("utf-8-sig")


def _read_zip_bytes(zf: zipfile.ZipFile, name: str, max_bytes: int) -> bytes:
    info = zf.getinfo(name)
    if info.file_size > max_bytes:
        raise ConflictError(f"El archivo {name} supera el tamaño máximo permitido")
    with zf.open(name) as raw:
        return raw.read()


def _find_file(names: list[str], filename: str) -> str | None:
    for name in names:
        normalized = name.replace("\\", "/").strip("/")
        if normalized == filename or normalized.endswith(f"/{filename}"):
            return name
    return None


def _preview_as_data_url(data: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        mime = "image/png"
    elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
        mime = "image/jpeg"
    elif lower.endswith(".webp"):
        mime = "image/webp"
    elif lower.endswith(".gif"):
        mime = "image/gif"
    else:
        raise ConflictError("La vista previa debe ser PNG, JPG, WEBP o GIF")
    import base64

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def parse_template_zip(file_bytes: bytes) -> ParsedTemplatePackage:
    if not file_bytes:
        raise ConflictError("El archivo ZIP está vacío")

    try:
        zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile as exc:
        raise ConflictError("El archivo no es un ZIP válido") from exc

    names = zf.namelist()
    manifest_name = _find_manifest_name(names)
    if manifest_name is None:
        raise ConflictError("El ZIP debe incluir manifest.json en la raíz")

    try:
        manifest = json.loads(_read_zip_text(zf, manifest_name))
    except json.JSONDecodeError as exc:
        raise ConflictError("manifest.json no es un JSON válido") from exc

    if not isinstance(manifest, dict):
        raise ConflictError("manifest.json debe ser un objeto JSON")

    slug = str(manifest.get("id") or manifest.get("slug") or "").strip().lower()
    if not slug or not _SLUG_RE.match(slug):
        raise ConflictError(
            "El id del manifest debe ser un slug (minúsculas, números y guiones, 2-40 caracteres)"
        )

    name = str(manifest.get("name") or slug).strip()
    if not name:
        raise ConflictError("El manifest debe incluir name")

    description = str(manifest.get("description") or "").strip()
    extends = str(manifest.get("extends") or manifest.get("base") or "sports").strip().lower()
    if extends not in ALLOWED_STOREFRONT_TEMPLATES:
        raise ConflictError(
            f"extends debe ser una plantilla base: {', '.join(sorted(ALLOWED_STOREFRONT_TEMPLATES))}"
        )

    theme_raw = manifest.get("theme") or manifest.get("theme_colors") or {}
    if not isinstance(theme_raw, dict):
        raise ConflictError("theme debe ser un objeto con colores hex")

    theme_colors: dict[str, str] = {}
    for key in THEME_COLOR_KEYS:
        if key in theme_raw:
            color = normalize_hex_color(str(theme_raw[key]))
            if color:
                theme_colors[key] = color

    css_name = _find_file(names, "styles.css")
    custom_css = ""
    if css_name:
        css_bytes = _read_zip_bytes(zf, css_name, _MAX_CSS_BYTES)
        custom_css = css_bytes.decode("utf-8-sig").strip()

    preview_image = ""
    preview_name = _find_file(names, "preview.png") or _find_file(names, "preview.jpg")
    if preview_name:
        preview_bytes = _read_zip_bytes(zf, preview_name, _MAX_PREVIEW_BYTES)
        preview_image = _preview_as_data_url(preview_bytes, preview_name)

    return ParsedTemplatePackage(
        slug=slug,
        name=name[:120],
        description=description[:500],
        extends_template=extends,
        theme_colors=theme_colors,
        custom_css=custom_css,
        preview_image=preview_image,
    )
