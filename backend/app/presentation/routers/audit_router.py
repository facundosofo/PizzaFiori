"""
Audit Router - Handles audit log queries and history
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from dependency_injector.wiring import inject, Provide
from typing import Optional, List
from datetime import datetime
import structlog

from app.application.audit_service import AuditService
from app.containers import Container
from app.presentation.schemas.audit_schemas import (
    AuditLogResponse,
    AuditHistoryResponse,
    RecentActivityResponse,
    SaleAuditDetail
)
from app.presentation.routers.dependencies import require_admin


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
    dependencies=[Depends(require_admin)],
)
logger = structlog.get_logger(__name__)


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=AuditHistoryResponse,
    summary="Get Entity History",
    description="Get complete audit history for a specific entity",
)
@inject
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: AuditService = Depends(Provide[Container.audit_service]),
):
    """
    Get audit history for a specific entity.
    
    - **entity_type**: Type of entity (Product, User, Category, Offer, Sale)
    - **entity_id**: ID of the entity
    - **limit**: Number of records to return (default 50, max 500)
    - **offset**: Number of records to skip (for pagination)
    
    Returns list of audit records ordered by timestamp (newest first).
    """
    result = await service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    
    if result.error:
        logger.error(
            "Error retrieving entity history",
            entity_type=entity_type,
            entity_id=entity_id,
            error=result.error,
        )
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    # Get total count
    from app.domain.unit_of_work import AbstractUnitOfWork
    uow: AbstractUnitOfWork = Provide[Container.unit_of_work]
    async with uow as uow_instance:
        # Note: This is a simplified count, ideally would filter by entity
        total = len(result.value)  # In practice, implement proper count in repo
    
    return AuditHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        records=[AuditLogResponse.model_validate(log) for log in result.value],
    )


@router.get(
    "/user/{username}",
    response_model=AuditHistoryResponse,
    summary="Get User Actions",
    description="Get all actions performed by a specific user (Admin only)",
)
@inject
async def get_user_actions(
    username: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: AuditService = Depends(Provide[Container.audit_service]),
):
    """
    Get all actions performed by a user (Admin only).
    
    - **username**: Username of the user
    - **limit**: Number of records to return
    - **offset**: Number of records to skip
    """
    result = await service.get_user_actions(
        username=username,
        limit=limit,
        offset=offset,
    )
    
    if result.error:
        logger.error(
            "Error retrieving user actions",
            username=username,
            error=result.error,
        )
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return AuditHistoryResponse(
        total=len(result.value),
        limit=limit,
        offset=offset,
        records=[AuditLogResponse.model_validate(log) for log in result.value],
    )


@router.get(
    "/recent",
    response_model=RecentActivityResponse,
    summary="Get Recent Activity",
    description="Get recent system activity (Admin only)",
)
@inject
async def get_recent_activity(
    limit: int = Query(100, ge=1, le=500),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    service: AuditService = Depends(Provide[Container.audit_service]),
):
    """
    Get recent system activity (Admin only).
    
    - **limit**: Number of records to return
    - **entity_type**: Optional filter by entity type
    """
    result = await service.get_recent_activity(
        limit=limit,
        entity_type=entity_type,
    )
    
    if result.error:
        logger.error(
            "Error retrieving recent activity",
            error=result.error,
        )
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return RecentActivityResponse(
        activity=[AuditLogResponse.model_validate(log) for log in result.value],
        count=len(result.value),
    )


@router.get(
    "/sales/{sale_id}",
    response_model=List[SaleAuditDetail],
    summary="Get Sale Audit History",
    description="Get detailed audit history for a sale including item changes",
)
@inject
async def get_sale_history(
    sale_id: int,
    service: AuditService = Depends(Provide[Container.audit_service]),
):
    """
    Get detailed audit history for a sale.
    
    Returns audit records with parsed item changes (items added, removed, modified).
    """
    result = await service.get_entity_history(
        entity_type="Sale",
        entity_id=sale_id,
        limit=100,
        offset=0,
    )
    
    if result.error:
        logger.error(
            "Error retrieving sale history",
            sale_id=sale_id,
            error=result.error,
        )
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    # Convert to SaleAuditDetail
    return [SaleAuditDetail.from_audit_log(log) for log in result.value]


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
        total=len(result.value),
        limit=limit,
        offset=offset,
        records=[AuditLogResponse.model_validate(log) for log in result.value],
    )
