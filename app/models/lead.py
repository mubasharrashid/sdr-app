"""Lead model - Lead/prospect records."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Lead(Base):
    """Lead/prospect record."""
    
    __tablename__ = "leads"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Company information
    company_name = Column(String(255), nullable=True)
    company_domain = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Location
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Social profiles
    linkedin_url = Column(Text, nullable=True)
    twitter_url = Column(Text, nullable=True)
    
    # Lead source
    source = Column(String(100), nullable=True, index=True)
    source_id = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), default="new", index=True)
    
    # Scoring
    lead_score = Column(Integer, default=0, index=True)
    engagement_score = Column(Integer, default=0)
    
    # Outreach status
    current_sequence_step = Column(Integer, default=0)
    last_contacted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_replied_at = Column(TIMESTAMP(timezone=True), nullable=True)
    next_followup_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    
    # Email tracking
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    
    # Call tracking
    calls_made = Column(Integer, default=0)
    calls_connected = Column(Integer, default=0)
    voicemails_left = Column(Integer, default=0)
    
    # Meeting tracking
    meetings_booked = Column(Integer, default=0)
    meetings_completed = Column(Integer, default=0)
    
    # AI enrichment
    enrichment_data = Column(JSONB, default=dict)
    enriched_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # AI personalization
    personalization_context = Column(JSONB, default=dict)
    ai_notes = Column(Text, nullable=True)
    
    # Custom fields
    custom_fields = Column(JSONB, default=dict)
    tags = Column(ARRAY(Text), nullable=True)
    
    # CRM sync
    crm_id = Column(String(255), nullable=True)
    crm_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Opt-out
    is_unsubscribed = Column(Boolean, default=False)
    unsubscribed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    do_not_contact = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        if self.full_name:
            return self.full_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.email or self.phone or "Unknown"
    
    @property
    def is_contactable(self) -> bool:
        """Check if lead can be contacted."""
        return not self.is_unsubscribed and not self.do_not_contact
    
    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_opened / self.emails_sent) * 100
