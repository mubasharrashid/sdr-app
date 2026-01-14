"""
Pydantic Schemas for TenantAgent model.

Handles validation and serialization for tenant-agent assignment endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class TenantAgentBase(BaseModel):
    """Base schema with common tenant_agent fields."""
    
    tenant_id: UUID = Field(..., description="ID of the tenant")
    agent_id: UUID = Field(..., description="ID of the agent")


class TenantAgentCreate(TenantAgentBase):
    """Schema for assigning an agent to a tenant."""
    
    custom_system_prompt: Optional[str] = Field(
        None,
        description="Override the agent's default system prompt"
    )
    custom_model: Optional[str] = Field(
        None,
        max_length=50,
        description="Override the agent's default model"
    )
    custom_temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Override the agent's default temperature"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tenant-specific agent settings"
    )


class TenantAgentCreateInternal(BaseModel):
    """Internal schema for creating tenant_agent."""
    
    tenant_id: str
    agent_id: str
    is_active: bool = True
    custom_system_prompt: Optional[str] = None
    custom_model: Optional[str] = None
    custom_temperature: Optional[float] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class TenantAgentUpdate(BaseModel):
    """Schema for updating a tenant agent assignment."""
    
    is_active: Optional[bool] = None
    custom_system_prompt: Optional[str] = None
    custom_model: Optional[str] = Field(None, max_length=50)
    custom_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


class TenantAgentResponse(BaseModel):
    """Schema for tenant_agent API responses."""
    
    id: UUID
    tenant_id: UUID
    agent_id: UUID
    is_active: bool
    custom_system_prompt: Optional[str] = None
    custom_model: Optional[str] = None
    custom_temperature: Optional[float] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    total_executions: int = 0
    last_execution_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TenantAgentWithAgent(TenantAgentResponse):
    """Response including agent details."""
    
    agent_slug: Optional[str] = None
    agent_name: Optional[str] = None
    agent_category: Optional[str] = None


class TenantAgentListResponse(BaseModel):
    """List response for tenant agents."""
    
    items: List[TenantAgentResponse]
    total: int


class AssignAgentRequest(BaseModel):
    """Request body for assigning an agent to a tenant."""
    
    agent_id: UUID = Field(..., description="ID of the agent to assign")
    custom_system_prompt: Optional[str] = Field(
        None,
        description="Custom system prompt for this tenant"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tenant-specific agent settings"
    )
