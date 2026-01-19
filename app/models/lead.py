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
    
    # Ghost tracking (AI conversation state)
    conversation_state = Column(String(30), default="in_sequence")  # in_sequence, engaged, awaiting_reply, ghosted
    ai_last_response_at = Column(TIMESTAMP(timezone=True), nullable=True)
    sequence_paused_at_step = Column(Integer, nullable=True)
    ghost_timeout_hours = Column(Integer, default=48)
    re_engagement_count = Column(Integer, default=0)
    max_re_engagements = Column(Integer, default=5)
    
    # BANT Qualification (Budget, Authority, Need, Timeline)
    bant_budget_score = Column(Integer, default=0)  # 0-3
    bant_authority_score = Column(Integer, default=0)  # 0-3
    bant_need_score = Column(Integer, default=0)  # 0-3
    bant_timeline_score = Column(Integer, default=0)  # 0-3
    bant_budget_details = Column(Text, nullable=True)
    bant_authority_details = Column(Text, nullable=True)
    bant_need_details = Column(Text, nullable=True)
    bant_timeline_details = Column(Text, nullable=True)
    bant_overall_score = Column(Integer, default=0)  # 0-12
    bant_qualification_status = Column(String(30), default="unqualified")  # unqualified, partially_qualified, qualified
    bant_sales_notes = Column(Text, nullable=True)
    bant_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
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
    
    @property
    def is_awaiting_reply(self) -> bool:
        """Check if waiting for lead's reply after AI response."""
        return self.conversation_state == "awaiting_reply"
    
    @property
    def is_in_sequence(self) -> bool:
        """Check if lead is in normal outreach sequence."""
        return self.conversation_state == "in_sequence"
    
    @property
    def can_re_engage(self) -> bool:
        """Check if lead can be re-engaged after ghosting."""
        return self.re_engagement_count < (self.max_re_engagements or 5)
    
    @property
    def is_bant_qualified(self) -> bool:
        """Check if lead is BANT qualified (score >= 8)."""
        return (self.bant_overall_score or 0) >= 8
    
    @property
    def bant_criteria_met(self) -> int:
        """Count how many BANT criteria have been identified (score > 0)."""
        count = 0
        if self.bant_budget_score and self.bant_budget_score > 0:
            count += 1
        if self.bant_authority_score and self.bant_authority_score > 0:
            count += 1
        if self.bant_need_score and self.bant_need_score > 0:
            count += 1
        if self.bant_timeline_score and self.bant_timeline_score > 0:
            count += 1
        return count
