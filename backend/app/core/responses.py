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


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Fetched successfully",
) -> dict[str, Any]:
    total_pages = (total + page_size - 1) // page_size if total else 0
    return success_response(
        message=message,
        data={
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    )


def error_response(
    message: str = "Invalid request",
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "errors": errors or [],
    }
