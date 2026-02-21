"""
Audit-related Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
from datetime import datetime


# ---------------------------
# Request Models - Audit
# ---------------------------

class AuditQueryParams(BaseModel):
    """Parameters for querying audit logs"""
    entity_type: Optional[str] = Field(None, description="Filter by entity type (Product, User, Sale, etc.)")
    entity_id: Optional[int] = Field(None, description="Filter by specific entity ID")
    user_id: Optional[int] = Field(None, description="Filter by user who performed the action")
    action: Optional[str] = Field(None, description="Filter by action (CREATE, UPDATE, DELETE)")
    date_from: Optional[datetime] = Field(None, description="Filter by start date")
    date_to: Optional[datetime] = Field(None, description="Filter by end date")
    limit: int = Field(50, ge=1, le=500, description="Maximum number of records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip")


# ---------------------------
# Response Models - Audit
# ---------------------------

class UserBasicInfo(BaseModel):
    """Basic user information for audit logs"""
    id: int
    username: str
    email: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: int
    timestamp: datetime
    user_id: int
    user: UserBasicInfo  # Information about who performed the action
    entity_type: str
    entity_id: int
    action: str  # CREATE, UPDATE, DELETE
    changes: dict  # JSON field with change details
    correlation_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditHistoryResponse(BaseModel):
    """Response for audit history list with pagination metadata"""
    total: int = Field(..., description="Total number of audit records matching filters")
    limit: int = Field(..., description="Number of records per page")
    offset: int = Field(..., description="Number of records skipped")
    records: List[AuditLogResponse] = Field(..., description="List of audit log records")


class AuditSummaryResponse(BaseModel):
    """Summary statistics for auditing"""
    total_actions: int
    total_creates: int
    total_updates: int
    total_deletes: int
    entities_affected: int
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None


# ---------------------------
# Sale-Specific Audit Models
# ---------------------------

class SaleItemChange(BaseModel):
    """Represents a change in a sale item"""
    id: int
    changes: Optional[dict] = None  # For modified items
    data: Optional[dict] = None  # For added/removed items


class SaleAuditDetail(BaseModel):
    """Detailed audit information specific to sales"""
    audit_id: int
    timestamp: datetime
    user: UserBasicInfo
    action: str
    sale_id: int
    changes: dict  # Includes basic sale changes
    items_added: List[SaleItemChange] = []
    items_removed: List[SaleItemChange] = []
    items_modified: List[SaleItemChange] = []
    
    @classmethod
    def from_audit_log(cls, audit_log: Any) -> "SaleAuditDetail":
        """Convert AuditLog to SaleAuditDetail with parsed item changes"""
        changes = audit_log.changes
        items_info = changes.get("items", {})
        
        return cls(
            audit_id=audit_log.id,
            timestamp=audit_log.timestamp,
            user=UserBasicInfo.model_validate(audit_log.user),
            action=audit_log.action,
            sale_id=audit_log.entity_id,
            changes={k: v for k, v in changes.items() if k != "items"},
            items_added=[SaleItemChange(**item) for item in items_info.get("items_added", [])],
            items_removed=[SaleItemChange(**item) for item in items_info.get("items_removed", [])],
            items_modified=[SaleItemChange(**item) for item in items_info.get("items_modified", [])],
        )


class RecentActivityResponse(BaseModel):
    """Response for recent system activity"""
    activity: List[AuditLogResponse]
    count: int
