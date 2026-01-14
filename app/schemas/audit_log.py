"""Pydantic schemas for AuditLog."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class AuditLogBase(BaseModel):
    """Base schema for AuditLog."""
    
    action: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[UUID] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an AuditLog."""
    
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = Field(None, max_length=100)
    endpoint: Optional[str] = Field(None, max_length=255)
    http_method: Optional[str] = Field(None, max_length=10)
    response_status: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: str = Field("info", pattern="^(debug|info|warning|error|critical)$")


class AuditLogResponse(BaseModel):
    """Response schema for AuditLog."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_status: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    severity: str
    created_at: datetime
    
    # Computed
    is_error: Optional[bool] = None
    is_system_level: Optional[bool] = None


class AuditLogSummary(BaseModel):
    """Summary schema for AuditLog."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    action: str
    resource_type: str
    severity: str
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """List response for AuditLogs."""
    
    items: List[AuditLogResponse]
    total: int


class AuditLogFilter(BaseModel):
    """Filter schema for querying audit logs."""
    
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
