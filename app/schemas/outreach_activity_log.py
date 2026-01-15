"""Pydantic schemas for OutreachActivityLog."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class OutreachActivityLogBase(BaseModel):
    """Base schema for OutreachActivityLog."""
    
    activity_type: str = Field(..., max_length=50)
    channel: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None


class OutreachActivityLogCreate(OutreachActivityLogBase):
    """Schema for creating an OutreachActivityLog."""
    
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    sequence_step_id: Optional[UUID] = None
    related_type: Optional[str] = Field(None, max_length=50)
    related_id: Optional[UUID] = None
    email_subject: Optional[str] = Field(None, max_length=500)
    email_message_id: Optional[str] = Field(None, max_length=255)
    call_duration_seconds: Optional[int] = None
    call_outcome: Optional[str] = Field(None, max_length=50)
    link_url: Optional[str] = None
    link_clicked_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    source: Optional[str] = Field(None, max_length=50)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = Field(None, max_length=30)
    activity_at: Optional[datetime] = None


class OutreachActivityLogCreateInternal(OutreachActivityLogCreate):
    """Internal schema for creating an OutreachActivityLog."""
    
    tenant_id: str
    source_user_id: Optional[str] = None


class OutreachActivityLogResponse(BaseModel):
    """Response schema for OutreachActivityLog."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    sequence_step_id: Optional[UUID] = None
    activity_type: str
    channel: Optional[str] = None
    description: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[UUID] = None
    email_subject: Optional[str] = None
    email_message_id: Optional[str] = None
    call_duration_seconds: Optional[int] = None
    call_outcome: Optional[str] = None
    link_url: Optional[str] = None
    link_clicked_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None
    source_user_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    activity_at: datetime
    created_at: datetime
    
    # Computed
    is_email_activity: Optional[bool] = None
    is_call_activity: Optional[bool] = None
    is_positive_engagement: Optional[bool] = None


class OutreachActivityLogSummary(BaseModel):
    """Summary schema for OutreachActivityLog."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lead_id: UUID
    activity_type: str
    channel: Optional[str] = None
    activity_at: datetime


class OutreachActivityLogListResponse(BaseModel):
    """List response for OutreachActivityLogs."""
    
    items: List[OutreachActivityLogResponse]
    total: int
