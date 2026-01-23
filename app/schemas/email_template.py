"""Pydantic schemas for Email Template."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class EmailTemplateBase(BaseModel):
    """Base schema for Email Template."""
    
    template_name: Optional[str] = Field(None, max_length=255, description="Name of the template")
    icp_person_id: Optional[UUID] = Field(None, description="Reference to ICP this template targets")
    icp_person_name: Optional[str] = Field(None, max_length=255, description="Name of the ICP person/target")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject line")
    body_content: str = Field(..., min_length=1, description="Email body content (supports variables)")
    email_sequence: int = Field(default=1, ge=1, description="Step number in the email sequence")
    template_type: str = Field(
        default="outreach", 
        pattern="^(outreach|follow_up|reply|nurture|objection_handling|closing)$",
        description="Type of email template"
    )
    description: Optional[str] = Field(None, description="Template description")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Available personalization variables")
    is_active: bool = Field(default=True, description="Whether the template is active")


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an Email Template."""
    pass


class EmailTemplateCreateInternal(EmailTemplateCreate):
    """Internal schema for creating an Email Template."""
    
    tenant_id: str
    created_by: Optional[str] = None


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an Email Template."""
    
    template_name: Optional[str] = Field(None, max_length=255)
    icp_person_id: Optional[UUID] = None
    icp_person_name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body_content: Optional[str] = Field(None, min_length=1)
    email_sequence: Optional[int] = Field(None, ge=1)
    template_type: Optional[str] = Field(
        None, 
        pattern="^(outreach|follow_up|reply|nurture|objection_handling|closing)$"
    )
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for Email Template response."""
    
    id: UUID
    tenant_id: UUID
    created_by: Optional[UUID] = None
    times_used: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EmailTemplateListResponse(BaseModel):
    """Schema for list of Email Templates."""
    
    items: list[EmailTemplateResponse]
    total: int
