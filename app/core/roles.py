ROLE_ADMIN = "administrador"
ROLE_CLIENT_1 = "cliente_tipo_1"
ROLE_CLIENT_2 = "cliente_tipo_2"

PLATFORM_ROLES = [
    {
        "slug": ROLE_ADMIN,
        "name": "Administrador",
        "description": "Acceso total a la plataforma: clientes, licencias y usuarios.",
    },
    {
        "slug": ROLE_CLIENT_1,
        "name": "Cliente tipo 1",
        "description": "Acceso a módulos Binfrix asignados por licencia (operación estándar).",
    },
    {
        "slug": ROLE_CLIENT_2,
        "name": "Cliente tipo 2",
        "description": "Acceso a módulos Binfrix con permisos de gestión ampliada.",
    },
]


def is_platform_admin(role_slug: str | None) -> bool:
    return role_slug == ROLE_ADMIN
