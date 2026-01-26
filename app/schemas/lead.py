"""Pydantic schemas for Lead."""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class LeadBase(BaseModel):
    """Base schema for Lead."""
    
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    company_domain: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    source_id: Optional[str] = Field(None, max_length=255)


class LeadCreate(LeadBase):
    """Schema for creating a Lead."""
    
    campaign_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    status: str = Field(default="new")
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LeadCreateInternal(LeadCreate):
    """Internal schema for creating a Lead."""
    
    tenant_id: str


class LeadUpdate(BaseModel):
    """Schema for updating a Lead."""
    
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    company_domain: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    campaign_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    status: Optional[str] = None
    lead_score: Optional[int] = None
    engagement_score: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    ai_notes: Optional[str] = None
    is_unsubscribed: Optional[bool] = None
    do_not_contact: Optional[bool] = None
    # Ghost tracking
    conversation_state: Optional[str] = None
    ai_last_response_at: Optional[datetime] = None
    sequence_paused_at_step: Optional[int] = None
    ghost_timeout_hours: Optional[int] = None
    re_engagement_count: Optional[int] = None
    max_re_engagements: Optional[int] = None
    # BANT qualification
    bant_score: Optional[int] = Field(None, ge=0, le=12)
    bant_status: Optional[str] = Field(None, pattern="^(unqualified|partially_qualified|qualified)$")
    bant_data: Optional[Dict[str, Any]] = None
    bant_sales_notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Response schema for Lead."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    campaign_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    source: Optional[str] = None
    status: str
    lead_score: int = 0
    engagement_score: int = 0
    current_sequence_step: int = 0
    last_contacted_at: Optional[datetime] = None
    last_replied_at: Optional[datetime] = None
    next_followup_at: Optional[datetime] = None
    emails_sent: int = 0
    emails_opened: int = 0
    emails_replied: int = 0
    calls_made: int = 0
    calls_connected: int = 0
    meetings_booked: int = 0
    tags: Optional[List[str]] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    is_unsubscribed: bool = False
    do_not_contact: bool = False
    # Ghost tracking
    conversation_state: str = "in_sequence"
    ai_last_response_at: Optional[datetime] = None
    sequence_paused_at_step: Optional[int] = None
    ghost_timeout_hours: int = 48
    re_engagement_count: int = 0
    max_re_engagements: int = 5
    # BANT qualification
    bant_score: int = 0
    bant_status: str = "unqualified"
    bant_data: Dict[str, Any] = Field(default_factory=dict)
    bant_sales_notes: Optional[str] = None
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed
    display_name: Optional[str] = None
    is_contactable: Optional[bool] = None
    open_rate: Optional[float] = None
    is_awaiting_reply: Optional[bool] = None
    can_re_engage: Optional[bool] = None
    is_bant_qualified: Optional[bool] = None



class LeadStats(BaseModel):
    """Statistics for Leads."""
    
    total_leads: int
    new_leads: int
    engaged_leads: int
    qualified_leads: int
    meetings_scheduled: int


class LeadSummary(BaseModel):
    """Summary schema for Lead."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    lead_score: int = 0


class LeadListResponse(BaseModel):
    """List response for Leads."""
    
    items: List[LeadResponse]
    total: int
