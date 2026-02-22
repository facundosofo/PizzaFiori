"""
Audit Router - Handles audit log queries and history
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from dependency_injector.wiring import inject, Provide
from typing import Optional
from datetime import datetime
import structlog

from app.application.audit_service import AuditService
from app.containers import Container
from app.presentation.schemas.audit_schemas import (
    AuditLogResponse,
    AuditHistoryResponse,
)
from app.presentation.routers.dependencies import require_admin


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
    dependencies=[Depends(require_admin)],
)
logger = structlog.get_logger(__name__)





@router.get(
    "/search",
    response_model=AuditHistoryResponse,
    summary="Search Audit Logs",
    description="Search audit logs with multiple filters (Admin only)",
)
@inject
async def search_audit_logs(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    entity_type: Optional[str] = Query(None, description="Entity type"),
    username: Optional[str] = Query(None, description="Username"),
    action: Optional[str] = Query(None, description="Action type (CREATE, UPDATE, DELETE)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: AuditService = Depends(Provide[Container.audit_service]),
):
    """
    Search audit logs with multiple filters (Admin only).
    
    - **start_date**: Filter by start date
    - **end_date**: Filter by end date
    - **entity_type**: Filter by entity type
    - **username**: Filter by user who performed the action
    - **action**: Filter by action type (CREATE, UPDATE, DELETE)
    - **limit**: Number of records to return
    - **offset**: Number of records to skip
    """
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before end_date",
        )
    
    # Set defaults if not provided
    if not start_date and end_date:
        # If only end_date, default to 30 days before
        from datetime import timedelta
        start_date = end_date - timedelta(days=30)
    elif not end_date and start_date:
        # If only start_date, default to now
        end_date = datetime.now()
    elif not start_date and not end_date:
        # If neither, default to last 7 days
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
    
    result = await service.get_by_date_range(
        start_date=start_date,
        end_date=end_date,
        entity_type=entity_type,
        username=username,
        action=action,
        limit=limit,
        offset=offset,
    )
    
    if result.error:
        logger.error(
            "Error searching audit logs",
            error=result.error,
        )
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return AuditHistoryResponse(
        total=result.value["total"],
        limit=limit,
        offset=offset,
        records=[AuditLogResponse.model_validate(log) for log in result.value["records"]],
    )
