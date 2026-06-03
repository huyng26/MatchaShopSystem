from fastapi import APIRouter, HTTPException

from app.core.database import ping_database

router = APIRouter()


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "api_v1_ready"}


@router.get("/status/db")
async def database_status() -> dict[str, str]:
    try:
        await ping_database()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="database_unavailable",
        ) from exc

    return {"status": "database_ready"}
