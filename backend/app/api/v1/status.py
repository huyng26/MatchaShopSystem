from fastapi import APIRouter, HTTPException

from app.core.database import ping_database
from app.core.responses import success_response

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    return success_response(data={"status": "api_v1_ready"})


@router.get("/status/db")
async def database_status() -> dict:
    try:
        await ping_database()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="database_unavailable",
        ) from exc

    return success_response(data={"status": "database_ready"})
