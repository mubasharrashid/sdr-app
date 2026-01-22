"""Email Template model - Email templates for outreach campaigns."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class EmailTemplate(Base):
    """Email template for outreach campaigns."""
    
    __tablename__ = "email_templates"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    icp_person_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("icps.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    created_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Template identification
    template_name = Column(String(255), nullable=True)
    icp_person_name = Column(String(255), nullable=True)
    
    # Email content
    subject = Column(String(500), nullable=False)
    body_content = Column(Text, nullable=False)
    
    # Sequence information
    email_sequence = Column(Integer, default=1, nullable=False)
    
    # Template metadata
    template_type = Column(String(50), default="outreach", index=True)
    description = Column(Text, nullable=True)
    
    # Personalization variables
    variables = Column(JSONB, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_used(self) -> bool:
        """Check if template has been used."""
        return self.times_used > 0
