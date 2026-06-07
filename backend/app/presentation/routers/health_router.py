"""
Health Check Router — verifies API availability and database connectivity.
Public route, no authentication required.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.infrastructure.database import engine

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("", status_code=200)
async def health_check():
    """
    GET /health — returns overall system status and database connectivity.

    Response:
        200: {"status": "healthy", "database": "connected"}
        503: {"status": "unhealthy", "database": "unreachable"}
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "unreachable"},
        )
