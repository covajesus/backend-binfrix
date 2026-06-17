"""Punto de entrada del API.

Producción (systemd): uvicorn main:app --host 0.0.0.0 --port 8097
Desarrollo local: python main.py
"""

from app.main import app  # noqa: F401 — export para `uvicorn main:app`

from app.config import get_settings

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)
