"""
Pydantic Schemas for KnowledgeBase model.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class KnowledgeBaseBase(BaseModel):
    """Base schema with common knowledge base fields."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kb_type: str = Field(
        default="general",
        pattern=r'^(general|product|faq|competitor|industry)$'
    )


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Schema for creating a knowledge base."""
    
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    settings: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseCreateInternal(BaseModel):
    """Internal schema for creating knowledge base."""
    
    tenant_id: str
    agent_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    kb_type: str = "general"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 500
    chunk_overlap: int = 50
    settings: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    kb_type: Optional[str] = Field(None, pattern=r'^(general|product|faq|competitor|industry)$')
    status: Optional[str] = Field(None, pattern=r'^(active|processing|inactive)$')
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Schema for knowledge base API responses."""
    
    id: UUID
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    vector_index_name: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    status: str
    document_count: int
    total_chunks: int
    last_synced_at: Optional[datetime] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_active: bool = Field(description="Whether KB is active")
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseListResponse(BaseModel):
    """Paginated list response for knowledge bases."""
    
    items: List[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


class KnowledgeBaseSummary(BaseModel):
    """Minimal knowledge base info."""
    
    id: UUID
    name: str
    kb_type: str
    document_count: int
    status: str
    
    model_config = ConfigDict(from_attributes=True)
