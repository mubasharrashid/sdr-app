"""Pydantic schemas for EmailReply."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class EmailReplyBase(BaseModel):
    """Base schema for EmailReply."""
    
    from_email: str = Field(..., max_length=255)
    from_name: Optional[str] = Field(None, max_length=255)
    to_email: str = Field(..., max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class EmailReplyCreate(EmailReplyBase):
    """Schema for creating an EmailReply."""
    
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    sequence_step_id: Optional[UUID] = None
    message_id: Optional[str] = Field(None, max_length=255)
    thread_id: Optional[str] = Field(None, max_length=255)
    received_at: datetime
    has_attachments: bool = False
    attachment_count: int = 0
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class EmailReplyCreateInternal(EmailReplyCreate):
    """Internal schema for creating an EmailReply."""
    
    tenant_id: str


class EmailReplyUpdate(BaseModel):
    """Schema for updating an EmailReply."""
    
    reply_type: Optional[str] = None
    is_auto_reply: Optional[bool] = None
    is_out_of_office: Optional[bool] = None
    is_bounce: Optional[bool] = None
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")
    intent: Optional[str] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    suggested_response: Optional[str] = None
    requires_action: Optional[bool] = None
    action_taken: Optional[str] = Field(None, max_length=100)


class EmailReplyResponse(BaseModel):
    """Response schema for EmailReply."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lead_id: UUID
    campaign_id: Optional[UUID] = None
    sequence_step_id: Optional[UUID] = None
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    to_email: str
    subject: Optional[str] = None
    body_text: Optional[str] = None
    has_attachments: bool = False
    attachment_count: int = 0
    reply_type: Optional[str] = None
    is_auto_reply: bool = False
    is_out_of_office: bool = False
    is_bounce: bool = False
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    suggested_response: Optional[str] = None
    response_sent: bool = False
    requires_action: bool = True
    action_taken: Optional[str] = None
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_positive: Optional[bool] = None
    needs_attention: Optional[bool] = None


class EmailReplySummary(BaseModel):
    """Summary schema for EmailReply."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lead_id: UUID
    from_email: str
    subject: Optional[str] = None
    reply_type: Optional[str] = None
    received_at: datetime


class EmailReplyListResponse(BaseModel):
    """List response for EmailReplies."""
    
    items: List[EmailReplyResponse]
    total: int
