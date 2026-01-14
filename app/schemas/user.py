"""
Pydantic Schemas for User model.

Handles validation, serialization, and API documentation for user endpoints.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re


class UserBase(BaseModel):
    """Base schema with common user fields."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@acme.com"]
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's first name",
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's last name",
        examples=["Doe"]
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Phone number",
        examples=["+1-555-123-4567"]
    )
    job_title: Optional[str] = Field(
        None,
        max_length=100,
        description="Job title",
        examples=["Sales Manager"]
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    tenant_id: UUID = Field(
        ...,
        description="ID of the tenant this user belongs to"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)"
    )
    role: str = Field(
        default="member",
        pattern=r'^(owner|admin|member)$',
        description="User role"
    )
    timezone: Optional[str] = Field(None, max_length=50)
    locale: str = Field(default="en", max_length=10)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserCreateInternal(BaseModel):
    """Internal schema for creating user (with hashed password)."""
    
    tenant_id: UUID
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    job_title: Optional[str] = None
    role: str = "member"
    timezone: Optional[str] = None
    locale: str = "en"
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    preferences: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


class UserUpdateAdmin(UserUpdate):
    """Admin-only schema for updating user with privileged fields."""
    
    role: Optional[str] = Field(None, pattern=r'^(owner|admin|member)$')
    status: Optional[str] = Field(None, pattern=r'^(active|inactive|suspended)$')
    permissions: Optional[List[str]] = None
    is_verified: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for changing user password."""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserResponse(BaseModel):
    """Schema for user API responses."""
    
    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str = Field(description="Combined first and last name")
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    role: str
    status: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    timezone: Optional[str] = None
    locale: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_active: bool = Field(description="Whether user account is active")
    is_admin: bool = Field(description="Whether user is admin or owner")
    
    model_config = ConfigDict(from_attributes=True)


class UserResponseAdmin(UserResponse):
    """Admin-only response with additional fields."""
    
    permissions: List[str] = Field(default_factory=list)
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    password_changed_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Paginated list response for users."""
    
    items: List[UserResponse]
    total: int = Field(description="Total number of users matching the query")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    pages: int = Field(ge=0, description="Total number of pages")


class UserSummary(BaseModel):
    """Minimal user info for embedding in other responses."""
    
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    
    model_config = ConfigDict(from_attributes=True)
