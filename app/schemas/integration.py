"""Pydantic schemas for Integration."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class IntegrationBase(BaseModel):
    """Base schema for Integration."""
    
    slug: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    provider: Optional[str] = Field(None, max_length=100)
    provider_url: Optional[str] = None
    auth_type: str = Field(..., pattern="^(oauth2|api_key|basic|webhook)$")
    oauth_authorization_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    required_fields: Optional[List[str]] = Field(default_factory=list)
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_active: bool = True
    is_premium: bool = False
    docs_url: Optional[str] = None
    setup_instructions: Optional[str] = None


class IntegrationCreate(IntegrationBase):
    """Schema for creating an Integration."""
    pass


class IntegrationUpdate(BaseModel):
    """Schema for updating an Integration."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    provider: Optional[str] = Field(None, max_length=100)
    provider_url: Optional[str] = None
    oauth_authorization_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    required_fields: Optional[List[str]] = None
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    docs_url: Optional[str] = None
    setup_instructions: Optional[str] = None


class IntegrationResponse(IntegrationBase):
    """Response schema for Integration."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_oauth: Optional[bool] = None
    is_api_key: Optional[bool] = None


class IntegrationSummary(BaseModel):
    """Summary schema for Integration."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    slug: str
    name: str
    category: str
    auth_type: str
    icon_url: Optional[str] = None
    is_active: bool


class IntegrationListResponse(BaseModel):
    """List response for Integrations."""
    
    items: List[IntegrationResponse]
    total: int
