from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response


class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class AuthenticationError(AppError):
    def __init__(self, message: str = "Invalid authentication credentials") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str, errors: list[dict[str, str]] | None = None) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, errors)


class BusinessRuleError(AppError):
    pass


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=exc.message, errors=exc.errors),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail: Any = exc.detail
    if isinstance(detail, str):
        message = detail
        errors = []
    elif isinstance(detail, dict):
        message = str(detail.get("code", "Request failed"))
        errors = [
            {"field": str(field), "message": str(value)}
            for field, value in detail.items()
            if field not in {"code", "errors"}
        ]
        errors.extend(detail.get("errors", []))
    else:
        message = "Request failed"
        errors = []

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=message, errors=errors),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        errors.append(
            {
                "field": location or "request",
                "message": error.get("msg", "Invalid value"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(message="Validation failed", errors=errors),
    )
