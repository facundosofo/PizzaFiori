"""
Audit-related Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List
from datetime import datetime


# ---------------------------
# Response Models - Audit
# ---------------------------

class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: int
    timestamp: datetime
    username: str  # Username del usuario que realizó la acción
    entity_type: str
    entity_id: int
    action: str  # CREATE, UPDATE, DELETE
    changes: dict  # JSON field with change details
    
    model_config = ConfigDict(from_attributes=True)


class AuditHistoryResponse(BaseModel):
    """Response for audit history list with pagination metadata"""
    total: int = Field(..., description="Total number of audit records matching filters")
    limit: int = Field(..., description="Number of records per page")
    offset: int = Field(..., description="Number of records skipped")
    records: List[AuditLogResponse] = Field(..., description="List of audit log records")
