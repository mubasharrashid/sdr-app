"""
KnowledgeDocument Model - Documents uploaded to knowledge bases.

Individual files that are processed, chunked, and indexed for RAG.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class KnowledgeDocument(Base):
    """
    Documents uploaded to knowledge bases.
    
    Each document is processed, chunked, and indexed in a vector database
    for retrieval during AI agent conversations.
    """
    
    __tablename__ = "knowledge_documents"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    knowledge_base_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Document details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # File information
    file_type = Column(String(50), index=True, comment="pdf, docx, txt, csv, html, md")
    file_size = Column(Integer, comment="Size in bytes")
    file_url = Column(Text, comment="S3/storage URL")
    original_filename = Column(String(255))
    
    # Content
    content_text = Column(Text, comment="Extracted text content")
    content_hash = Column(String(64), index=True, comment="SHA256 hash for deduplication")
    
    # Processing status
    status = Column(
        String(20), 
        default="pending", 
        index=True,
        comment="Status: pending, processing, ready, failed"
    )
    processing_error = Column(Text)
    
    # Chunking information
    chunk_count = Column(Integer, default=0)
    
    # Vector IDs for cleanup
    vector_ids = Column(JSON, default=list, comment="Vector IDs in Pinecone")
    
    # Metadata
    metadata = Column(JSON, default=dict, comment="Extracted document metadata")
    
    # Upload tracking
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    # Timestamps
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_ready(self) -> bool:
        """Check if document is processed and ready."""
        return self.status == "ready"
    
    @property
    def is_processing(self) -> bool:
        """Check if document is being processed."""
        return self.status == "processing"
    
    @property
    def has_failed(self) -> bool:
        """Check if processing failed."""
        return self.status == "failed"
    
    @property
    def file_size_kb(self) -> float:
        """Get file size in KB."""
        if self.file_size:
            return round(self.file_size / 1024, 2)
        return 0
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
