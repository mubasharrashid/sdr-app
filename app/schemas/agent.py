"""
Pydantic Schemas for Agent model.

Handles validation and serialization for agent-related endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID


class AgentBase(BaseModel):
    """Base schema with common agent fields."""
    
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="URL-safe identifier",
        examples=["jules", "joy", "george"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name",
        examples=["Jules", "Joy", "George"]
    )
    description: Optional[str] = Field(
        None,
        description="Agent description"
    )
    category: str = Field(
        ...,
        description="Agent category",
        examples=["marketing", "sales", "customer_success"]
    )


class AgentCreate(AgentBase):
    """Schema for creating a new agent (admin only)."""
    
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of agent capabilities"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Default system prompt for AI model"
    )
    default_model: str = Field(
        default="gpt-4",
        description="Default LLM model"
    )
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for AI responses"
    )
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class AgentUpdate(BaseModel):
    """Schema for updating an agent (admin only)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    default_model: Optional[str] = None
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    is_active: Optional[bool] = None
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    model_config = ConfigDict(extra="forbid")


class AgentResponse(AgentBase):
    """Schema for agent API responses."""
    
    id: UUID
    capabilities: List[Any] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    default_model: str
    default_temperature: float
    is_active: bool
    icon_url: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AgentSummary(BaseModel):
    """Minimal agent info for embedding in other responses."""
    
    id: UUID
    slug: str
    name: str
    category: str
    color: Optional[str] = None
    is_active: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """List response for agents."""
    
    items: List[AgentResponse]
    total: int
