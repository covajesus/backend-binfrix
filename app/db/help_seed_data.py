"""Contenido demo de páginas de ayuda (se inserta en BD por tenant)."""

DEMO_HELP_PAGES = [
    {
        "slug": "help-center",
        "nav_label": "Centro de ayuda",
        "title": "Centro de ayuda",
        "subtitle": "Respuestas rápidas sobre tu compra",
        "intro": (
            "Bienvenido al centro de ayuda. Aquí encontrarás información sobre pedidos, "
            "envíos, devoluciones y pagos. Si no resuelves tu duda, contáctanos por correo "
            "o teléfono."
        ),
        "sort_order": 0,
        "sections": [
            {
                "id": "temas",
                "title": "Temas frecuentes",
                "paragraphs": ["Selecciona un tema para ver más detalles:"],
                "bullets": [
                    "Estado del pedido: cómo seguir tu compra paso a paso.",
                    "Envíos y entregas: plazos, costos y cobertura.",
                    "Devoluciones: plazos y condiciones para cambiar o devolver.",
                    "Opciones de pago: medios disponibles y cuotas sin interés.",
                ],
            },
            {
                "id": "horario",
                "title": "Horario de atención",
                "paragraphs": [
                    "Nuestro equipo de atención al cliente está disponible de lunes a viernes "
                    "de 9:00 a 18:00 hrs. Fuera de ese horario puedes escribirnos y responderemos "
                    "el siguiente día hábil.",
                ],
                "bullets": [],
            },
            {
                "id": "contacto",
                "title": "¿Necesitas más ayuda?",
                "paragraphs": [
                    "Escríbenos por correo, llámanos o utiliza el enlace de atención al cliente "
                    "en la parte superior del sitio.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "order-status",
        "nav_label": "Estado del pedido",
        "title": "Estado del pedido",
        "subtitle": "Sigue el progreso de tu compra",
        "intro": (
            "Después de confirmar tu pedido recibirás un correo con el número de orden "
            "y los pasos para hacer seguimiento."
        ),
        "sort_order": 1,
        "sections": [
            {
                "id": "pasos",
                "title": "Etapas del pedido",
                "paragraphs": ["Tu pedido puede pasar por las siguientes etapas:"],
                "bullets": [
                    "Confirmado: recibimos tu pedido y validamos el pago.",
                    "En preparación: estamos empacando tus productos.",
                    "Despachado: el pedido salió de nuestro centro de distribución.",
                    "En tránsito: el courier está llevando el paquete a tu dirección.",
                    "Entregado: recibiste el pedido correctamente.",
                ],
            },
            {
                "id": "consultar",
                "title": "Cómo consultar tu pedido",
                "paragraphs": [
                    "Revisa el correo de confirmación: incluye el número de pedido y un enlace de seguimiento cuando esté disponible.",
                    "Si no encuentras el correo, revisa spam o contáctanos con tu nombre, RUT y fecha de compra.",
                ],
                "bullets": [],
            },
            {
                "id": "retrasos",
                "title": "Retrasos o incidencias",
                "paragraphs": [
                    "Si el plazo estimado de entrega venció, contáctanos para revisar el estado con el operador logístico.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "shipping",
        "nav_label": "Envíos y entregas",
        "title": "Envíos y entregas",
        "subtitle": "Plazos, costos y cobertura en Chile",
        "intro": (
            "Trabajamos con operadores logísticos para entregar tu pedido de forma segura. "
            "Los plazos pueden variar según la región y la disponibilidad del producto."
        ),
        "sort_order": 2,
        "sections": [
            {
                "id": "plazos",
                "title": "Plazos de entrega",
                "paragraphs": [
                    "Región Metropolitana: compra hoy, recibe mañana en pedidos confirmados antes de las 14:00 hrs (días hábiles).",
                    "Regiones: entre 2 y 5 días hábiles según destino, salvo zonas extremas o aisladas.",
                ],
                "bullets": [],
            },
            {
                "id": "costos",
                "title": "Costo de envío",
                "paragraphs": [
                    "El costo de despacho se calcula al finalizar la compra según dirección y peso del pedido.",
                    "Periódicamente ofrecemos envío gratuito en compras sobre un monto mínimo.",
                ],
                "bullets": [],
            },
            {
                "id": "seguimiento",
                "title": "Seguimiento",
                "paragraphs": [
                    "Cuando tu pedido sea despachado, recibirás un correo con el número de seguimiento del courier.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "returns",
        "nav_label": "Devoluciones",
        "title": "Devoluciones",
        "subtitle": "Cambios y devoluciones hasta en 60 días",
        "intro": (
            "Queremos que estés conforme con tu compra. Si el producto no te convence o presenta un defecto, "
            "revisa las condiciones siguientes."
        ),
        "sort_order": 3,
        "sections": [
            {
                "id": "plazo",
                "title": "Plazo",
                "paragraphs": [
                    "Tienes hasta 60 días desde la recepción del pedido para solicitar un cambio o devolución.",
                ],
                "bullets": [],
            },
            {
                "id": "condiciones",
                "title": "Condiciones",
                "paragraphs": ["El producto debe cumplir lo siguiente:"],
                "bullets": [
                    "Sin uso y en su estado original.",
                    "Con etiquetas, empaque y accesorios incluidos.",
                    "Con boleta o comprobante de compra.",
                ],
            },
            {
                "id": "proceso",
                "title": "Cómo solicitar una devolución",
                "paragraphs": [
                    "1. Escríbenos indicando número de pedido, producto y motivo.",
                    "2. Te enviaremos las instrucciones para el despacho o retiro según tu región.",
                    "3. Una vez recibido y revisado el producto, procesaremos el reembolso o cambio.",
                ],
                "bullets": [],
            },
        ],
    },
    {
        "slug": "payment",
        "nav_label": "Opciones de pago",
        "title": "Opciones de pago",
        "subtitle": "Medios de pago y financiamiento",
        "intro": "Ofrecemos distintas alternativas para que completes tu compra de forma segura.",
        "sort_order": 4,
        "sections": [
            {
                "id": "medios",
                "title": "Medios de pago aceptados",
                "paragraphs": ["Puedes pagar con:"],
                "bullets": [
                    "Tarjetas de crédito y débito (Visa, Mastercard, American Express).",
                    "Transferencia bancaria.",
                    "Webpay y otras pasarelas habilitadas en el checkout.",
                ],
            },
            {
                "id": "cuotas",
                "title": "Cuotas sin interés",
                "paragraphs": [
                    "Compra en hasta 12 cuotas sin interés con bancos y tarjetas participantes.",
                ],
                "bullets": [],
            },
            {
                "id": "seguridad",
                "title": "Seguridad",
                "paragraphs": [
                    "Los pagos se procesan en plataformas certificadas. No almacenamos el número completo de tu tarjeta.",
                ],
                "bullets": [],
            },
        ],
    },
]
