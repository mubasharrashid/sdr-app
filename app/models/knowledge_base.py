"""
KnowledgeBase Model - Knowledge base containers for RAG.

Stores collections of documents that AI agents can reference for context.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class KnowledgeBase(Base):
    """
    Knowledge base containers for RAG (Retrieval Augmented Generation).
    
    Each knowledge base can contain multiple documents and is linked
    to a tenant and optionally to a specific agent.
    """
    
    __tablename__ = "knowledge_bases"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional: restrict KB to specific agent"
    )
    
    # Knowledge base details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Type
    kb_type = Column(
        String(50), 
        default="general",
        index=True,
        comment="Type: general, product, faq, competitor, industry"
    )
    
    # Vector database configuration
    vector_index_name = Column(String(255), comment="Pinecone index name")
    embedding_model = Column(String(100), default="text-embedding-3-small")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    
    # Status
    status = Column(
        String(20), 
        default="active", 
        index=True,
        comment="Status: active, processing, inactive"
    )
    
    # Statistics
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    last_synced_at = Column(DateTime(timezone=True))
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name='{self.name}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if knowledge base is active."""
        return self.status == "active"
    
    @property
    def is_agent_specific(self) -> bool:
        """Check if KB is restricted to a specific agent."""
        return self.agent_id is not None
