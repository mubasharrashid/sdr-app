"""Pydantic schemas for Meeting."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date


class MeetingBase(BaseModel):
    """Base schema for Meeting."""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    meeting_type: Optional[str] = Field(None, max_length=50)
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    timezone: str = Field(default="UTC", max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    meeting_url: Optional[str] = None
    meeting_platform: Optional[str] = Field(None, max_length=50)


class MeetingCreate(MeetingBase):
    """Schema for creating a Meeting."""
    
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    attendees: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    booking_source: Optional[str] = Field(None, max_length=50)
    prep_notes: Optional[str] = None


class MeetingCreateInternal(MeetingCreate):
    """Internal schema for creating a Meeting."""
    
    tenant_id: str
    booked_by: Optional[str] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a Meeting."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    meeting_type: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    timezone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    meeting_url: Optional[str] = None
    meeting_platform: Optional[str] = Field(None, max_length=50)
    attendees: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    prep_notes: Optional[str] = None
    ai_prep_summary: Optional[str] = None


class MeetingComplete(BaseModel):
    """Schema for completing a meeting."""
    
    meeting_notes: Optional[str] = None
    outcome: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")
    next_steps: Optional[str] = None
    follow_up_date: Optional[date] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None


class MeetingResponse(BaseModel):
    """Response schema for Meeting."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    booked_by: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    meeting_type: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    timezone: str
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_platform: Optional[str] = None
    attendees: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    calendar_event_id: Optional[str] = None
    calendar_provider: Optional[str] = None
    booking_source: Optional[str] = None
    prep_notes: Optional[str] = None
    ai_prep_summary: Optional[str] = None
    meeting_notes: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    follow_up_date: Optional[date] = None
    recording_url: Optional[str] = None
    reminder_sent: bool = False
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_upcoming: Optional[bool] = None
    is_completed: Optional[bool] = None
    was_successful: Optional[bool] = None


class MeetingSummary(BaseModel):
    """Summary schema for Meeting."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lead_id: UUID
    title: str
    scheduled_at: datetime
    status: str


class MeetingListResponse(BaseModel):
    """List response for Meetings."""
    
    items: List[MeetingResponse]
    total: int
