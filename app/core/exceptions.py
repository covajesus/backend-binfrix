"""Excepciones de dominio — mapear a HTTP en routers o middleware."""

from fastapi import HTTPException, status


class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Acceso denegado"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflicto con el estado actual"):
        super().__init__(message, status.HTTP_409_CONFLICT)


def raise_http(exc: AppError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)
