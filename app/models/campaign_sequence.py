"""CampaignSequence model - Multi-step campaign sequences."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class CampaignSequence(Base):
    """Campaign sequence step."""
    
    __tablename__ = "campaign_sequences"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    campaign_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("campaigns.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Sequence order
    step_number = Column(Integer, nullable=False)
    
    # Identification
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Step type
    step_type = Column(String(50), nullable=False, index=True)
    
    # Timing
    delay_days = Column(Integer, default=0)
    delay_hours = Column(Integer, default=0)
    delay_minutes = Column(Integer, default=0)
    
    # Conditions
    condition_type = Column(String(50), nullable=True)
    condition_value = Column(JSONB, nullable=True)
    
    # Email content
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    email_template_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Call script
    call_script = Column(Text, nullable=True)
    call_objective = Column(String(255), nullable=True)
    
    # LinkedIn content
    linkedin_message = Column(Text, nullable=True)
    linkedin_connection_note = Column(String(300), nullable=True)
    
    # AI settings
    use_ai_generation = Column(Boolean, default=True)
    ai_prompt_template = Column(Text, nullable=True)
    ai_variables = Column(JSONB, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metrics
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    
    # A/B testing
    is_ab_test = Column(Boolean, default=False)
    ab_variant = Column(String(10), nullable=True)
    ab_test_group_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def total_delay_minutes(self) -> int:
        """Get total delay in minutes."""
        return (self.delay_days or 0) * 24 * 60 + (self.delay_hours or 0) * 60 + (self.delay_minutes or 0)
    
    @property
    def is_email_step(self) -> bool:
        """Check if step is email type."""
        return self.step_type == "email"
    
    @property
    def is_call_step(self) -> bool:
        """Check if step is call type."""
        return self.step_type == "call"
    
    @property
    def is_linkedin_step(self) -> bool:
        """Check if step is LinkedIn type."""
        return self.step_type in ("linkedin_message", "linkedin_connect")
    
    @property
    def open_rate(self) -> float:
        """Calculate open rate for this step."""
        if self.total_sent == 0:
            return 0.0
        return (self.total_opened / self.total_sent) * 100
    
    @property
    def reply_rate(self) -> float:
        """Calculate reply rate for this step."""
        if self.total_sent == 0:
            return 0.0
        return (self.total_replied / self.total_sent) * 100
