"""EmailReply model - Email reply tracking."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class EmailReply(Base):
    """Email reply tracking and analysis."""
    
    __tablename__ = "email_replies"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    sequence_step_id = Column(UUID(as_uuid=True), ForeignKey("campaign_sequences.id", ondelete="SET NULL"), nullable=True)
    
    # Email details
    message_id = Column(String(255), nullable=True)
    thread_id = Column(String(255), nullable=True, index=True)
    
    # From/To
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    to_email = Column(String(255), nullable=False)
    
    # Content
    subject = Column(String(500), nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Attachments
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    attachments = Column(JSONB, default=list)
    
    # Classification
    reply_type = Column(String(30), nullable=True, index=True)
    is_auto_reply = Column(Boolean, default=False)
    is_out_of_office = Column(Boolean, default=False)
    is_bounce = Column(Boolean, default=False)
    
    # AI analysis
    sentiment = Column(String(20), nullable=True)
    intent = Column(String(50), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    
    # AI response
    suggested_response = Column(Text, nullable=True)
    response_sent = Column(Boolean, default=False)
    response_sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Action required
    requires_action = Column(Boolean, default=True, index=True)
    action_taken = Column(String(100), nullable=True)
    action_taken_at = Column(TIMESTAMP(timezone=True), nullable=True)
    action_taken_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Integration data
    gmail_message_id = Column(String(255), nullable=True)
    outlook_message_id = Column(String(255), nullable=True)
    
    # Timestamps
    received_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_positive(self) -> bool:
        """Check if reply has positive sentiment."""
        return self.sentiment == "positive" or self.reply_type == "interested"
    
    @property
    def needs_attention(self) -> bool:
        """Check if reply needs immediate attention."""
        return self.requires_action and not self.is_auto_reply and not self.is_out_of_office
