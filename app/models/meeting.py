"""Meeting model - Meeting bookings and tracking."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Meeting(Base):
    """Meeting booking and tracking."""
    
    __tablename__ = "meetings"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    booked_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Meeting details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    meeting_type = Column(String(50), nullable=True)
    
    # Scheduling
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    timezone = Column(String(50), default="UTC")
    
    # Location/Link
    location = Column(String(255), nullable=True)
    meeting_url = Column(Text, nullable=True)
    meeting_platform = Column(String(50), nullable=True)
    
    # Attendees
    attendees = Column(JSONB, default=list)
    
    # Status
    status = Column(String(30), default="scheduled", index=True)
    
    # Calendar sync
    calendar_event_id = Column(String(255), nullable=True, index=True)
    calendar_provider = Column(String(50), nullable=True)
    
    # Booking source
    booking_source = Column(String(50), nullable=True)
    
    # Pre-meeting
    prep_notes = Column(Text, nullable=True)
    ai_prep_summary = Column(Text, nullable=True)
    
    # Post-meeting
    meeting_notes = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=True)
    next_steps = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    
    # Recording
    recording_url = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    
    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    cancelled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_upcoming(self) -> bool:
        """Check if meeting is upcoming."""
        return self.status in ("scheduled", "confirmed")
    
    @property
    def is_completed(self) -> bool:
        """Check if meeting is completed."""
        return self.status == "completed"
    
    @property
    def was_successful(self) -> bool:
        """Check if meeting was successful."""
        return self.status == "completed" and self.outcome == "positive"
