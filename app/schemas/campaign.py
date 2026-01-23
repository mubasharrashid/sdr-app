"""Pydantic schemas for Campaign."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, time


class CampaignBase(BaseModel):
    """Base schema for Campaign."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    campaign_type: str = Field(..., pattern="^(email|call|linkedin|multi-channel)$")
    channel: Optional[str] = None #Field(None, pattern="^(email|phone|linkedin|sms)$")
    timezone: str = Field(default="UTC", max_length=50)
    daily_limit: int = Field(default=100, ge=1, le=10000)
    hourly_limit: int = Field(default=20, ge=1, le=1000)
    use_ai_personalization: bool = True
    ai_tone: str = Field(default="professional", pattern="^(professional|friendly|casual|formal)$")


class CampaignCreate(CampaignBase):
    """Schema for creating a Campaign."""
    
    agent_id: Optional[UUID] = None
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    sending_days: Optional[List[str]] = Field(
        default=["monday", "tuesday", "wednesday", "thursday", "friday"]
    )
    sending_start_time: Optional[time] = Field(default=time(9, 0))
    sending_end_time: Optional[time] = Field(default=time(17, 0))
    target_criteria: Optional[Dict[str, Any]] = Field(default_factory=dict)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CampaignCreateInternal(CampaignCreate):
    """Internal schema for creating a Campaign."""
    
    tenant_id: str
    created_by: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Schema for updating a Campaign."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_id: Optional[UUID] = None
    channel: Optional[str] = Field(None, pattern="^(email|phone|linkedin|sms)$")
    status: Optional[str] = Field(None, pattern="^(draft|scheduled|active|paused|completed|archived)$")
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    sending_days: Optional[List[str]] = None
    sending_start_time: Optional[time] = None
    sending_end_time: Optional[time] = None
    daily_limit: Optional[int] = Field(None, ge=1, le=10000)
    hourly_limit: Optional[int] = Field(None, ge=1, le=1000)
    target_criteria: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    use_ai_personalization: Optional[bool] = None
    ai_tone: Optional[str] = Field(None, pattern="^(professional|friendly|casual|formal)$")


class CampaignUpdateMetrics(BaseModel):
    """Schema for updating campaign metrics."""
    
    total_leads: Optional[int] = None
    leads_contacted: Optional[int] = None
    leads_responded: Optional[int] = None
    leads_converted: Optional[int] = None
    emails_sent: Optional[int] = None
    emails_opened: Optional[int] = None
    emails_clicked: Optional[int] = None
    emails_replied: Optional[int] = None
    emails_bounced: Optional[int] = None
    calls_made: Optional[int] = None
    calls_connected: Optional[int] = None
    meetings_booked: Optional[int] = None


class CampaignResponse(BaseModel):
    """Response schema for Campaign."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    campaign_type: str
    channel: Optional[str] = None
    status: str
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timezone: str
    sending_days: Optional[List[str]] = None
    sending_start_time: Optional[time] = None
    sending_end_time: Optional[time] = None
    daily_limit: int
    hourly_limit: int
    target_criteria: Dict[str, Any] = Field(default_factory=dict)
    total_leads: int = 0
    leads_contacted: int = 0
    leads_responded: int = 0
    leads_converted: int = 0
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    calls_made: int = 0
    calls_connected: int = 0
    meetings_booked: int = 0
    settings: Dict[str, Any] = Field(default_factory=dict)
    use_ai_personalization: bool
    ai_tone: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_active: Optional[bool] = None
    open_rate: Optional[float] = None
    reply_rate: Optional[float] = None
    conversion_rate: Optional[float] = None


class CampaignSummary(BaseModel):
    """Summary schema for Campaign."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    campaign_type: str
    status: str
    total_leads: int = 0
    leads_converted: int = 0
    created_at: datetime


class CampaignListResponse(BaseModel):
    """List response for Campaigns."""
    
    items: List[CampaignResponse]
    total: int
