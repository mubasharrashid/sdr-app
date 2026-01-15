"""Campaign model - Marketing and outreach campaigns."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Time, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Campaign(Base):
    """Marketing and outreach campaign."""
    
    __tablename__ = "campaigns"
    
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
        index=True
    )
    
    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Type and channel
    campaign_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(20), default="draft", index=True)
    
    # Scheduling
    scheduled_start_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    scheduled_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    timezone = Column(String(50), default="UTC")
    
    # Sending schedule
    sending_days = Column(ARRAY(Text), default=["monday", "tuesday", "wednesday", "thursday", "friday"])
    sending_start_time = Column(Time, default="09:00")
    sending_end_time = Column(Time, default="17:00")
    
    # Rate limiting
    daily_limit = Column(Integer, default=100)
    hourly_limit = Column(Integer, default=20)
    
    # Target audience
    target_criteria = Column(JSONB, default=dict)
    
    # Metrics
    total_leads = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_responded = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    calls_made = Column(Integer, default=0)
    calls_connected = Column(Integer, default=0)
    meetings_booked = Column(Integer, default=0)
    
    # Settings
    settings = Column(JSONB, default=dict)
    
    # AI settings
    use_ai_personalization = Column(Boolean, default=True)
    ai_tone = Column(String(50), default="professional")
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_active(self) -> bool:
        """Check if campaign is active."""
        return self.status == "active"
    
    @property
    def is_draft(self) -> bool:
        """Check if campaign is draft."""
        return self.status == "draft"
    
    @property
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return self.status == "completed"
    
    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_opened / self.emails_sent) * 100
    
    @property
    def reply_rate(self) -> float:
        """Calculate email reply rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_replied / self.emails_sent) * 100
    
    @property
    def conversion_rate(self) -> float:
        """Calculate lead conversion rate."""
        if self.total_leads == 0:
            return 0.0
        return (self.leads_converted / self.total_leads) * 100
