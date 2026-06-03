from typing import Any


def success_response(
    data: Any = None,
    message: str = "Fetched successfully",
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(
    message: str = "Invalid request",
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "errors": errors or [],
    }
