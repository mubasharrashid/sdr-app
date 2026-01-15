"""CallTask model - AI call tasks for Retell AI."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class CallTask(Base):
    """AI call task for Retell AI integration."""
    
    __tablename__ = "call_tasks"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Call details
    phone_number = Column(String(50), nullable=False)
    caller_id = Column(String(50), nullable=True)
    
    # Scheduling
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    timezone = Column(String(50), default="UTC")
    
    # Status
    status = Column(String(30), default="pending", index=True)
    
    # Call context
    call_objective = Column(String(255), nullable=True)
    call_script = Column(Text, nullable=True)
    talking_points = Column(JSONB, default=list)
    
    # AI context
    lead_context = Column(JSONB, default=dict)
    ai_instructions = Column(Text, nullable=True)
    
    # Retell AI specific
    retell_call_id = Column(String(255), nullable=True, index=True)
    retell_agent_id = Column(String(255), nullable=True)
    
    # Call outcome
    call_started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    call_ended_at = Column(TIMESTAMP(timezone=True), nullable=True)
    call_duration_seconds = Column(Integer, nullable=True)
    
    # Recording
    recording_url = Column(Text, nullable=True)
    recording_duration_seconds = Column(Integer, nullable=True)
    
    # Transcription
    transcript = Column(Text, nullable=True)
    transcript_summary = Column(Text, nullable=True)
    
    # AI analysis
    sentiment = Column(String(20), nullable=True)
    key_topics = Column(ARRAY(Text), nullable=True)
    action_items = Column(JSONB, default=list)
    next_steps = Column(Text, nullable=True)
    
    # Outcome
    outcome = Column(String(50), nullable=True)
    meeting_booked = Column(Boolean, default=False)
    callback_scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Quality
    quality_score = Column(Integer, nullable=True)
    quality_notes = Column(Text, nullable=True)
    
    # Cost
    cost_cents = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    @property
    def is_completed(self) -> bool:
        """Check if call is completed."""
        return self.status == "completed"
    
    @property
    def is_successful(self) -> bool:
        """Check if call connected."""
        return self.status == "completed" and self.call_duration_seconds and self.call_duration_seconds > 0
    
    @property
    def cost_dollars(self) -> float:
        """Get cost in dollars."""
        return (self.cost_cents or 0) / 100
