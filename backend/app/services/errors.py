from typing import Any


class ServiceError(Exception):
    def __init__(
        self,
        code: str,
        *,
        status_code: int = 400,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.context = context or {}
