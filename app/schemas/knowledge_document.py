"""
Pydantic Schemas for KnowledgeDocument model.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class KnowledgeDocumentBase(BaseModel):
    """Base schema with common document fields."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """Schema for creating a document."""
    
    knowledge_base_id: UUID
    tenant_id: UUID
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    original_filename: Optional[str] = None
    content_text: Optional[str] = None
    uploaded_by: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentCreateInternal(BaseModel):
    """Internal schema for creating document."""
    
    knowledge_base_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    original_filename: Optional[str] = None
    content_text: Optional[str] = None
    content_hash: Optional[str] = None
    uploaded_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentUpdate(BaseModel):
    """Schema for updating a document."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r'^(pending|processing|ready|failed)$')
    processing_error: Optional[str] = None
    chunk_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    """Schema for document API responses."""
    
    id: UUID
    knowledge_base_id: UUID
    tenant_id: UUID
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    original_filename: Optional[str] = None
    content_hash: Optional[str] = None
    status: str
    processing_error: Optional[str] = None
    chunk_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    uploaded_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_ready: bool = Field(description="Whether document is processed")
    file_size_kb: float = Field(description="File size in KB")
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentListResponse(BaseModel):
    """Paginated list response for documents."""
    
    items: List[KnowledgeDocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class KnowledgeDocumentSummary(BaseModel):
    """Minimal document info."""
    
    id: UUID
    name: str
    file_type: Optional[str] = None
    status: str
    chunk_count: int
    
    model_config = ConfigDict(from_attributes=True)
