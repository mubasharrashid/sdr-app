"""Pydantic schemas for ApiKey."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ApiKeyBase(BaseModel):
    """Base schema for ApiKey."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scopes: List[str] = Field(default=["read"])
    rate_limit: int = Field(default=1000, ge=1, le=100000)


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an ApiKey."""
    
    expires_at: Optional[datetime] = None
    allowed_ips: Optional[List[str]] = None


class ApiKeyCreateInternal(ApiKeyCreate):
    """Internal schema for creating an ApiKey."""
    
    tenant_id: str
    created_by: str
    key_prefix: str
    key_hash: str


class ApiKeyUpdate(BaseModel):
    """Schema for updating an ApiKey."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=100000)
    is_active: Optional[bool] = None
    allowed_ips: Optional[List[str]] = None


class ApiKeyRevoke(BaseModel):
    """Schema for revoking an ApiKey."""
    
    reason: Optional[str] = None


class ApiKeyResponse(BaseModel):
    """Response schema for ApiKey."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    created_by: UUID
    name: str
    description: Optional[str] = None
    key_prefix: str
    scopes: List[str] = Field(default=["read"])
    allowed_ips: Optional[List[str]] = None
    rate_limit: int
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    revoke_reason: Optional[str] = None
    
    # Computed
    is_expired: Optional[bool] = None
    is_revoked: Optional[bool] = None
    is_valid: Optional[bool] = None


class ApiKeyResponseWithSecret(ApiKeyResponse):
    """Response with the actual key (only returned on creation)."""
    
    key: str  # The actual API key (only shown once)


class ApiKeySummary(BaseModel):
    """Summary schema for ApiKey."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyListResponse(BaseModel):
    """List response for ApiKeys."""
    
    items: List[ApiKeyResponse]
    total: int
