"""Pydantic schemas for CallTask."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CallTaskBase(BaseModel):
    """Base schema for CallTask."""
    
    phone_number: str = Field(..., max_length=50)
    caller_id: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    timezone: str = Field(default="UTC", max_length=50)
    call_objective: Optional[str] = Field(None, max_length=255)
    call_script: Optional[str] = None
    talking_points: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    ai_instructions: Optional[str] = None


class CallTaskCreate(CallTaskBase):
    """Schema for creating a CallTask."""
    
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    lead_context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CallTaskCreateInternal(CallTaskCreate):
    """Internal schema for creating a CallTask."""
    
    tenant_id: str
    created_by: Optional[str] = None


class CallTaskUpdate(BaseModel):
    """Schema for updating a CallTask."""
    
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    call_objective: Optional[str] = Field(None, max_length=255)
    call_script: Optional[str] = None
    talking_points: Optional[List[Dict[str, Any]]] = None
    ai_instructions: Optional[str] = None
    lead_context: Optional[Dict[str, Any]] = None


class CallTaskComplete(BaseModel):
    """Schema for completing a call."""
    
    call_duration_seconds: int
    transcript: Optional[str] = None
    transcript_summary: Optional[str] = None
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")
    key_topics: Optional[List[str]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    next_steps: Optional[str] = None
    outcome: Optional[str] = None
    meeting_booked: bool = False
    quality_score: Optional[int] = Field(None, ge=1, le=5)
    cost_cents: Optional[int] = Field(None, ge=0)


class CallTaskResponse(BaseModel):
    """Response schema for CallTask."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    phone_number: str
    caller_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    timezone: str
    status: str
    call_objective: Optional[str] = None
    call_script: Optional[str] = None
    talking_points: List[Dict[str, Any]] = Field(default_factory=list)
    retell_call_id: Optional[str] = None
    call_started_at: Optional[datetime] = None
    call_ended_at: Optional[datetime] = None
    call_duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_summary: Optional[str] = None
    sentiment: Optional[str] = None
    key_topics: Optional[List[str]] = None
    outcome: Optional[str] = None
    meeting_booked: bool = False
    quality_score: Optional[int] = None
    cost_cents: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_completed: Optional[bool] = None
    is_successful: Optional[bool] = None
    cost_dollars: Optional[float] = None


class CallTaskSummary(BaseModel):
    """Summary schema for CallTask."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lead_id: UUID
    phone_number: str
    status: str
    scheduled_at: Optional[datetime] = None
    outcome: Optional[str] = None


class CallTaskListResponse(BaseModel):
    """List response for CallTasks."""
    
    items: List[CallTaskResponse]
    total: int
