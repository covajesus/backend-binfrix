"""Punto de entrada: ejecutar desde la raíz del proyecto con `py main.py`."""

from app.config import get_settings

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
