"""Pydantic schemas for TenantIntegration."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class TenantIntegrationBase(BaseModel):
    """Base schema for TenantIntegration."""
    
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TenantIntegrationConnect(BaseModel):
    """Schema for connecting an integration."""
    
    integration_id: UUID
    # For API key integrations
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TenantIntegrationConnectOAuth(BaseModel):
    """Schema for OAuth callback."""
    
    integration_id: UUID
    code: str  # OAuth authorization code
    state: Optional[str] = None
    redirect_uri: str


class TenantIntegrationCreateInternal(BaseModel):
    """Internal schema for creating tenant integration."""
    
    tenant_id: str
    integration_id: str
    status: str = "pending"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    credentials: Optional[Dict[str, Any]] = Field(default_factory=dict)
    oauth_account_id: Optional[str] = None
    oauth_account_email: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    connected_by: Optional[str] = None
    connected_at: Optional[datetime] = None


class TenantIntegrationUpdate(BaseModel):
    """Schema for updating tenant integration."""
    
    settings: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None


class TenantIntegrationUpdateInternal(BaseModel):
    """Internal schema for updating tenant integration."""
    
    status: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    credentials: Optional[Dict[str, Any]] = None
    oauth_account_id: Optional[str] = None
    oauth_account_email: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    last_used_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_count: Optional[int] = None
    disconnected_at: Optional[datetime] = None


class TenantIntegrationResponse(BaseModel):
    """Response schema for TenantIntegration."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    integration_id: UUID
    status: str
    oauth_account_email: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    last_used_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_count: int = 0
    connected_by: Optional[UUID] = None
    connected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_connected: Optional[bool] = None
    is_expired: Optional[bool] = None
    has_error: Optional[bool] = None


class TenantIntegrationWithDetails(TenantIntegrationResponse):
    """Response with integration details."""
    
    integration: Optional[Dict[str, Any]] = None


class TenantIntegrationListResponse(BaseModel):
    """List response for TenantIntegrations."""
    
    items: List[TenantIntegrationResponse]
    total: int
