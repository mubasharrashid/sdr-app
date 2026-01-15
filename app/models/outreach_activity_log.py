"""OutreachActivityLog model - Outreach activity logging."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, INET
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class OutreachActivityLog(Base):
    """Comprehensive log of all outreach activities."""
    
    __tablename__ = "outreach_activity_logs"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    sequence_step_id = Column(UUID(as_uuid=True), ForeignKey("campaign_sequences.id", ondelete="SET NULL"), nullable=True)
    
    # Activity type
    activity_type = Column(String(50), nullable=False, index=True)
    
    # Channel
    channel = Column(String(30), nullable=True, index=True)
    
    # Activity details
    description = Column(Text, nullable=True)
    
    # Related entities
    related_type = Column(String(50), nullable=True)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Email-specific
    email_subject = Column(String(500), nullable=True)
    email_message_id = Column(String(255), nullable=True)
    
    # Call-specific
    call_duration_seconds = Column(Integer, nullable=True)
    call_outcome = Column(String(50), nullable=True)
    
    # Link tracking
    link_url = Column(Text, nullable=True)
    link_clicked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Source
    source = Column(String(50), nullable=True)
    source_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # IP/Device
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(30), nullable=True)
    
    # Timestamp
    activity_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    @property
    def is_email_activity(self) -> bool:
        """Check if email activity."""
        return self.channel == "email" or self.activity_type.startswith("email_")
    
    @property
    def is_call_activity(self) -> bool:
        """Check if call activity."""
        return self.channel == "phone" or self.activity_type.startswith("call_")
    
    @property
    def is_positive_engagement(self) -> bool:
        """Check if positive engagement."""
        positive_types = ["email_replied", "email_clicked", "call_connected", "meeting_booked", "linkedin_reply"]
        return self.activity_type in positive_types
