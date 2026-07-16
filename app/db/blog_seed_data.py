"""Seed data for corporate blog posts (binfrix.io)."""

from datetime import date

BLOG_SEED_POSTS = [
    {
        "slug": "ecommerce-propio-shopify-wordpress",
        "title": "Cómo elegir entre ecommerce propio, Shopify o WordPress",
        "type": "Guía",
        "published_at": date(2026, 3, 12),
        "read_time": "8 min",
        "excerpt": (
            "Compara ecommerce a medida, Shopify y WordPress según presupuesto, "
            "plazos, catálogo y operación diaria de tu negocio."
        ),
        "sort_order": 0,
        "related_slugs": ["checklist-tienda-online", "wordpress-vs-desarrollo-medida"],
        "sections": [
            {
                "id": "intro",
                "paragraphs": [
                    "Elegir plataforma no es solo una decisión técnica: define cuánto tardas en lanzar, cuánto pagas mes a mes y qué tan ágil es tu equipo para operar campañas, catálogo y pedidos.",
                    "En Binfrix vemos tres caminos frecuentes: desarrollo propio (B2C o B2B), Shopify como plataforma administrada y WordPress con WooCommerce para sitios más flexibles en contenido.",
                ],
                "bullets": [],
            },
            {
                "id": "propio",
                "title": "Ecommerce propio",
                "paragraphs": [
                    "Conviene cuando necesitas reglas comerciales específicas, integraciones a medida o un modelo B2B con intranet, presupuestos y listas de precio por cliente.",
                ],
                "bullets": [
                    "Control total del flujo de compra y backoffice",
                    "Ideal para B2B, catálogos complejos o integraciones internas",
                    "Mayor inversión inicial y roadmap de evolución planificado",
                ],
            },
            {
                "id": "shopify",
                "title": "Shopify",
                "paragraphs": [
                    "Es una opción sólida para retail B2C que quiere salir rápido con catálogo, pagos, envíos y apps del ecosistema.",
                ],
                "bullets": [
                    "Time-to-market más corto que un desarrollo desde cero",
                    "Costo recurrente por plan y apps",
                    "Menos flexibilidad en lógica muy custom sin desarrollo adicional",
                ],
            },
            {
                "id": "wordpress",
                "title": "WordPress + WooCommerce",
                "paragraphs": [
                    "Funciona bien cuando el contenido editorial, SEO y páginas informativas son tan importantes como la venta online.",
                ],
                "bullets": [
                    "Flexibilidad en contenido y estructura del sitio",
                    "Requiere mantención de plugins, seguridad y performance",
                    "Puede escalar, pero hay que diseñar bien hosting y caché",
                ],
            },
            {
                "id": "cierre",
                "title": "Qué evaluar antes de decidir",
                "paragraphs": [
                    "Revisa catálogo, volumen de pedidos, canales (B2C, B2B, WhatsApp), integraciones (ERP, facturación, logística) y capacidad interna para operar la plataforma.",
                    "Si quieres una recomendación concreta, en Binfrix partimos por un diagnóstico corto antes de proponer stack e implementación.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "vender-whatsapp-retail",
        "title": "Buenas prácticas para vender por WhatsApp en retail",
        "type": "Artículo",
        "published_at": date(2026, 2, 20),
        "read_time": "6 min",
        "excerpt": (
            "Organiza conversaciones, evita errores en precios y convierte chats "
            "en pedidos registrados con seguimiento claro."
        ),
        "sort_order": 1,
        "related_slugs": [
            "ecommerce-propio-shopify-wordpress",
            "landing-page-conversion",
        ],
        "sections": [
            {
                "id": "intro",
                "paragraphs": [
                    "WhatsApp es uno de los canales con mejor conversión en retail, pero también el más caótico si no hay reglas: mensajes perdidos, precios mal copiados y pedidos anotados en distintos lugares.",
                ],
                "bullets": [],
            },
            {
                "id": "flujo",
                "title": "Define un flujo único de venta",
                "paragraphs": [
                    "Cada conversación debería terminar en un estado claro: consulta, cotización, pedido confirmado o descartado. Sin eso, el equipo no sabe qué priorizar.",
                ],
                "bullets": [
                    "Asigna conversaciones por vendedor o turno",
                    "Usa plantillas para preguntas frecuentes",
                    "Registra el pedido en el mismo sistema, no en chats sueltos",
                ],
            },
            {
                "id": "catalogo",
                "title": "Catálogo y precios consistentes",
                "paragraphs": [
                    "Envía productos con precio y disponibilidad actualizados. Si el catálogo vive en una hoja aparte del canal de venta, los errores aparecen enseguida.",
                ],
                "bullets": [],
            },
            {
                "id": "metricas",
                "title": "Mide lo que importa",
                "paragraphs": [
                    "Tiempo de respuesta, tasa de conversión por vendedor y ticket promedio te dicen si el canal escala o solo aumenta la carga operativa.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "landing-page-conversion",
        "title": "Qué debe incluir una landing page orientada a conversión",
        "type": "Blog",
        "published_at": date(2026, 1, 15),
        "read_time": "5 min",
        "excerpt": (
            "Estructura, mensaje y CTA de una landing que convierta tráfico de "
            "campañas en leads o ventas medibles."
        ),
        "sort_order": 2,
        "related_slugs": ["checklist-tienda-online", "vender-whatsapp-retail"],
        "sections": [
            {
                "id": "intro",
                "paragraphs": [
                    "Una landing no es la home de tu marca: es una página con un objetivo concreto por campaña. Cada bloque debe empujar hacia una acción medible.",
                ],
                "bullets": [],
            },
            {
                "id": "estructura",
                "title": "Estructura recomendada",
                "paragraphs": [],
                "bullets": [
                    "Hero con propuesta de valor clara y CTA visible",
                    "Beneficios concretos, no adjetivos vacíos",
                    "Prueba social o casos breves",
                    "FAQ para objeciones frecuentes",
                    "Formulario corto o botón a checkout/WhatsApp",
                ],
            },
            {
                "id": "performance",
                "title": "Performance y medición",
                "paragraphs": [
                    "Si inviertes en ads, la landing debe cargar rápido en móvil y tener pixels o eventos configurados para medir clics, envíos y conversiones.",
                    "Conecta la landing con tu ecommerce o canal comercial para no perder el hilo entre campaña y venta.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "checklist-tienda-online",
        "title": "Checklist antes de lanzar una tienda en línea",
        "type": "Artículo",
        "published_at": date(2025, 12, 8),
        "read_time": "7 min",
        "excerpt": (
            "Catálogo, pagos, envíos, legal y operación: lo esencial para "
            "publicar sin sorpresas el día del lanzamiento."
        ),
        "sort_order": 3,
        "related_slugs": [
            "ecommerce-propio-shopify-wordpress",
            "mantencion-preventiva-web",
        ],
        "sections": [
            {
                "id": "catalogo",
                "title": "Catálogo y stock",
                "paragraphs": [],
                "bullets": [
                    "Productos con fotos, variantes y precios revisados",
                    "Stock sincronizado o reglas claras si vendes sin inventario en línea",
                    "Políticas de cambio y devolución visibles",
                ],
            },
            {
                "id": "pagos",
                "title": "Pagos y checkout",
                "paragraphs": [],
                "bullets": [
                    "Pasarela configurada y probada con montos reales",
                    "Flujo de compra claro en móvil",
                    "Correos transaccionales de confirmación funcionando",
                ],
            },
            {
                "id": "legal",
                "title": "Legal y confianza",
                "paragraphs": [],
                "bullets": [
                    "Términos, privacidad y datos de contacto publicados",
                    "Información de despacho y plazos",
                    "Certificado SSL activo en el dominio",
                ],
            },
            {
                "id": "operacion",
                "title": "Operación post-lanzamiento",
                "paragraphs": [
                    "Define quién procesa pedidos, quién responde consultas y cómo se escalan incidencias el primer mes. Un lanzamiento exitoso depende tanto del software como del equipo detrás.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "wordpress-vs-desarrollo-medida",
        "title": "Cuándo conviene un sitio WordPress vs. desarrollo a medida",
        "type": "Guía",
        "published_at": date(2025, 11, 22),
        "read_time": "6 min",
        "excerpt": (
            "WordPress acelera contenido y SEO; el desarrollo a medida encaja "
            "cuando el negocio necesita lógica y integraciones propias."
        ),
        "sort_order": 4,
        "related_slugs": [
            "ecommerce-propio-shopify-wordpress",
            "mantencion-preventiva-web",
        ],
        "sections": [
            {
                "id": "intro",
                "paragraphs": [
                    "WordPress sigue siendo una buena opción para sitios corporativos, blogs y ecommerce de complejidad media. El desarrollo a medida tiene sentido cuando el software es parte central del negocio.",
                ],
                "bullets": [],
            },
            {
                "id": "wordpress",
                "title": "Elige WordPress cuando…",
                "paragraphs": [],
                "bullets": [
                    "El contenido editorial pesa más que la lógica custom",
                    "Necesitas publicar y actualizar páginas con agilidad",
                    "El presupuesto y plazo son acotados",
                ],
            },
            {
                "id": "medida",
                "title": "Elige desarrollo a medida cuando…",
                "paragraphs": [],
                "bullets": [
                    "Hay procesos únicos (B2B, vertical, operación interna)",
                    "Requieres integraciones profundas con otros sistemas",
                    "La plataforma es producto, no solo presencia web",
                ],
            },
            {
                "id": "cierre",
                "paragraphs": [
                    "En muchos proyectos combinamos ambos enfoques: WordPress para contenido y un módulo a medida para la operación crítica.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "mantencion-preventiva-web",
        "title": "Mantención preventiva: qué revisar cada mes en tu web",
        "type": "Artículo",
        "published_at": date(2025, 10, 30),
        "read_time": "5 min",
        "excerpt": (
            "Actualizaciones, respaldos, uptime y seguridad: una rutina mensual "
            "para evitar emergencias costosas."
        ),
        "sort_order": 5,
        "related_slugs": ["checklist-tienda-online", "wordpress-vs-desarrollo-medida"],
        "sections": [
            {
                "id": "intro",
                "paragraphs": [
                    "Después del lanzamiento, la mayoría de los problemas graves se evita con mantención preventiva. Un chequeo mensual reduce caídas, hackeos y pérdida de datos.",
                ],
                "bullets": [],
            },
            {
                "id": "checklist",
                "title": "Checklist mensual",
                "paragraphs": [],
                "bullets": [
                    "Actualizar CMS, plugins o dependencias críticas",
                    "Verificar que los respaldos se ejecuten y se puedan restaurar",
                    "Revisar uptime y tiempos de carga",
                    "Probar formularios, checkout y correos transaccionales",
                    "Auditar accesos de administradores y contraseñas",
                ],
            },
            {
                "id": "plan",
                "title": "Cuándo contratar un plan de mantención",
                "paragraphs": [
                    "Si tu sitio genera ventas o leads de forma constante, un plan de soporte con tiempos de respuesta definidos suele costar menos que una emergencia en temporada alta.",
                ],
                "bullets": [],
            },
        ],
    },
]
