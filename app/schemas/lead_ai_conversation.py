"""Pydantic schemas for LeadAIConversation."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class LeadAIConversationBase(BaseModel):
    """Base schema for LeadAIConversation."""
    
    channel: str = Field(..., pattern="^(email|call|linkedin|sms|chat)$")
    role: str = Field(..., pattern="^(system|assistant|user|function)$")
    message_type: Optional[str] = Field(None, max_length=30)
    content: str


class LeadAIConversationCreate(LeadAIConversationBase):
    """Schema for creating a LeadAIConversation."""
    
    lead_id: UUID
    agent_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    subject: Optional[str] = Field(None, max_length=500)
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_used: Optional[str] = Field(None, max_length=100)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")
    campaign_id: Optional[UUID] = None
    call_task_id: Optional[UUID] = None
    email_reply_id: Optional[UUID] = None
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    # BANT tracking
    bant_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LeadAIConversationCreateInternal(LeadAIConversationCreate):
    """Internal schema for creating a LeadAIConversation."""
    
    tenant_id: str


class LeadAIConversationResponse(BaseModel):
    """Response schema for LeadAIConversation."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lead_id: UUID
    agent_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    channel: str
    role: str
    message_type: Optional[str] = None
    content: str
    subject: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_used: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    sentiment: Optional[str] = None
    campaign_id: Optional[UUID] = None
    call_task_id: Optional[UUID] = None
    email_reply_id: Optional[UUID] = None
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    # BANT tracking
    bant_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    # Computed
    is_from_ai: Optional[bool] = None
    is_from_lead: Optional[bool] = None
    total_tokens: Optional[int] = None


class LeadAIConversationSummary(BaseModel):
    """Summary schema for LeadAIConversation."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    channel: str
    role: str
    content: str
    created_at: datetime


class LeadAIConversationListResponse(BaseModel):
    """List response for LeadAIConversations."""
    
    items: List[LeadAIConversationResponse]
    total: int
