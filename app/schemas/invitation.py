"""
Pydantic Schemas for Invitation model.

Handles validation, serialization, and API documentation for invitation endpoints.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class InvitationBase(BaseModel):
    """Base schema with common invitation fields."""
    
    email: EmailStr = Field(
        ...,
        description="Email address of the person being invited",
        examples=["new.user@company.com"]
    )
    role: str = Field(
        default="member",
        pattern=r'^(owner|admin|member)$',
        description="Role to assign when invitation is accepted",
        examples=["member", "admin"]
    )
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional message from the inviter",
        examples=["Welcome to our team! Looking forward to working with you."]
    )


class InvitationCreate(InvitationBase):
    """Schema for creating a new invitation."""
    
    tenant_id: UUID = Field(
        ...,
        description="ID of the tenant to invite the user to"
    )
    invited_by: Optional[UUID] = Field(
        None,
        description="ID of the user sending the invitation"
    )
    expires_in_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days until invitation expires"
    )


class InvitationCreateInternal(BaseModel):
    """Internal schema for creating invitation (with generated fields)."""
    
    tenant_id: str  # String for JSON serialization
    email: str
    role: str = "member"
    token: str
    invited_by: Optional[str] = None
    expires_at: str  # ISO format string
    message: Optional[str] = None
    status: str = "pending"


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""
    
    token: str = Field(
        ...,
        description="Invitation token from the invite link"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password for the new account"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name"
    )


class InvitationResponse(BaseModel):
    """Schema for invitation API responses."""
    
    id: UUID
    tenant_id: UUID
    email: str
    role: str
    status: str
    invited_by: Optional[UUID] = None
    message: Optional[str] = None
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_valid: bool = Field(description="Whether invitation can still be accepted")
    is_expired: bool = Field(description="Whether invitation has expired")
    
    model_config = ConfigDict(from_attributes=True)


class InvitationResponseWithToken(InvitationResponse):
    """Response including token (only for inviter to share)."""
    
    token: str = Field(description="Invitation token to share with invitee")


class InvitationListResponse(BaseModel):
    """Paginated list response for invitations."""
    
    items: List[InvitationResponse]
    total: int = Field(description="Total number of invitations matching the query")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    pages: int = Field(ge=0, description="Total number of pages")


class InvitationVerify(BaseModel):
    """Response when verifying an invitation token."""
    
    valid: bool = Field(description="Whether the invitation is valid")
    email: Optional[str] = Field(None, description="Email the invitation is for")
    role: Optional[str] = Field(None, description="Role that will be assigned")
    tenant_name: Optional[str] = Field(None, description="Name of the tenant")
    expires_at: Optional[datetime] = Field(None, description="When the invitation expires")
    message: Optional[str] = Field(None, description="Message from the inviter")
