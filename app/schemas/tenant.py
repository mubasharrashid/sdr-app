"""
Pydantic Schemas for Tenant model.

These schemas handle validation, serialization, and API documentation
for all tenant-related endpoints.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import re


class TenantBase(BaseModel):
    """Base schema with common tenant fields."""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Company display name",
        examples=["Acme Corporation"]
    )
    slug: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        pattern=r'^[a-z0-9-]+$',
        description="URL-safe unique identifier (lowercase letters, numbers, hyphens)",
        examples=["acme-corp"]
    )
    logo_url: Optional[str] = Field(
        None,
        description="URL to company logo image",
        examples=["https://cdn.example.com/logos/acme.png"]
    )
    primary_color: Optional[str] = Field(
        None, 
        pattern=r'^#[0-9A-Fa-f]{6}$',
        description="Brand color in hex format",
        examples=["#FF5733"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Primary contact email",
        examples=["admin@acme.com"]
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Primary phone number",
        examples=["+1-555-123-4567"]
    )
    website: Optional[str] = Field(
        None,
        max_length=255,
        description="Company website URL",
        examples=["https://www.acme.com"]
    )
    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="IANA timezone identifier",
        examples=["America/New_York", "Europe/London", "Asia/Dubai"]
    )
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase and properly formatted."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Slug cannot start or end with a hyphen')
        if '--' in v:
            raise ValueError('Slug cannot contain consecutive hyphens')
        return v.lower()


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    
    plan: str = Field(
        default="free", 
        pattern=r'^(free|starter|pro|enterprise)$',
        description="Subscription plan tier",
        examples=["free", "starter", "pro", "enterprise"]
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tenant-specific configuration settings"
    )
    
    # Optional address fields for initial setup
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Optional billing fields
    billing_email: Optional[EmailStr] = None


class TenantUpdate(BaseModel):
    """Schema for updating an existing tenant. All fields are optional."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Address fields
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Billing fields
    billing_email: Optional[EmailStr] = None
    
    # Settings
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        extra="forbid"  # Reject unknown fields
    )


class TenantUpdateAdmin(TenantUpdate):
    """Admin-only schema for updating tenant with privileged fields."""
    
    # Plan management (admin only)
    plan: Optional[str] = Field(None, pattern=r'^(free|starter|pro|enterprise)$')
    plan_started_at: Optional[datetime] = None
    plan_expires_at: Optional[datetime] = None
    
    # Usage limits (admin only)
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_leads: Optional[int] = Field(None, ge=100, le=10000000)
    max_emails_per_day: Optional[int] = Field(None, ge=0, le=100000)
    max_calls_per_day: Optional[int] = Field(None, ge=0, le=10000)
    
    # Status management (admin only)
    status: Optional[str] = Field(None, pattern=r'^(active|suspended|cancelled)$')
    suspended_reason: Optional[str] = None
    
    # Stripe integration
    stripe_customer_id: Optional[str] = None


class TenantResponse(TenantBase):
    """Schema for tenant API responses."""
    
    id: UUID
    
    # Address fields
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Subscription & Billing
    plan: str
    plan_started_at: Optional[datetime] = None
    plan_expires_at: Optional[datetime] = None
    billing_email: Optional[str] = None
    
    # Usage Limits
    max_users: int
    max_leads: int
    max_emails_per_day: int
    max_calls_per_day: int
    
    # Status & Settings
    status: str
    settings: Dict[str, Any]
    
    # Timestamps
    onboarded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_active: bool = Field(description="Whether the tenant account is active")
    is_on_paid_plan: bool = Field(description="Whether the tenant is on a paid plan")
    
    model_config = ConfigDict(
        from_attributes=True
    )


class TenantResponseAdmin(TenantResponse):
    """Admin-only response with additional sensitive fields."""
    
    stripe_customer_id: Optional[str] = None
    suspended_reason: Optional[str] = None


class TenantListResponse(BaseModel):
    """Paginated list response for tenants."""
    
    items: List[TenantResponse]
    total: int = Field(description="Total number of tenants matching the query")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "pages": 5
            }
        }
    )


class TenantSummary(BaseModel):
    """Minimal tenant info for embedding in other responses."""
    
    id: UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    plan: str
    status: str
    
    model_config = ConfigDict(
        from_attributes=True
    )
