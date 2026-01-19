"""LeadAIConversation model - AI conversation history."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class LeadAIConversation(Base):
    """AI conversation history with leads."""
    
    __tablename__ = "leads_ai_conversation"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_executions.id", ondelete="SET NULL"), nullable=True)
    
    # Conversation context
    channel = Column(String(30), nullable=False, index=True)
    
    # Message details
    role = Column(String(20), nullable=False)
    message_type = Column(String(30), nullable=True)
    
    # Content
    content = Column(Text, nullable=False)
    
    # For email/linkedin
    subject = Column(String(500), nullable=True)
    
    # For calls
    audio_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # AI model info
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    # Sentiment
    sentiment = Column(String(20), nullable=True)
    
    # Related entities
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    call_task_id = Column(UUID(as_uuid=True), ForeignKey("call_tasks.id", ondelete="SET NULL"), nullable=True)
    email_reply_id = Column(UUID(as_uuid=True), ForeignKey("email_replies.id", ondelete="SET NULL"), nullable=True)
    
    # Was this sent?
    is_sent = Column(Boolean, default=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # BANT tracking for this message
    bant_data = Column(JSONB, default=dict)  # BANT qualification data from AI response
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    
    @property
    def is_from_ai(self) -> bool:
        """Check if message is from AI."""
        return self.role == "assistant"
    
    @property
    def is_from_lead(self) -> bool:
        """Check if message is from lead."""
        return self.role == "user"
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return (self.prompt_tokens or 0) + (self.completion_tokens or 0)
