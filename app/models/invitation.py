"""
Invitation Model - User invitation system for multi-tenant platform.

Allows existing users to invite new users to their tenant with role assignment.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone, timedelta

from app.db.base_class import Base


class Invitation(Base):
    """
    User invitations table.
    
    Allows tenant admins/owners to invite new users. Invitations have:
    - Unique secure token for acceptance
    - Expiration time (default 7 days)
    - Role assignment on acceptance
    """
    
    __tablename__ = "invitations"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant relationship
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant the invitation belongs to"
    )
    
    # Invitation details
    email = Column(String(255), nullable=False, comment="Email address of invitee")
    role = Column(
        String(20), 
        default="member",
        comment="Role assigned on acceptance: owner, admin, member"
    )
    
    # Secure token
    token = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Unique token for secure acceptance"
    )
    
    # Inviter information
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="User who sent the invitation"
    )
    
    # Status tracking
    status = Column(
        String(20), 
        default="pending", 
        index=True,
        comment="Status: pending, accepted, expired, cancelled"
    )
    
    # Expiration
    expires_at = Column(
        DateTime(timezone=True), 
        nullable=False,
        comment="When the invitation expires"
    )
    
    # Acceptance tracking
    accepted_at = Column(DateTime(timezone=True), comment="When invitation was accepted")
    accepted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="User created from this invitation"
    )
    
    # Optional message
    message = Column(Text, comment="Optional message from inviter")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="invitations")
    # inviter = relationship("User", foreign_keys=[invited_by])
    # accepted_user = relationship("User", foreign_keys=[accepted_by])
    
    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email='{self.email}', status='{self.status}')>"
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == "pending"
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        if self.status == "expired":
            return True
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return True
        return False
    
    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid (pending and not expired)."""
        return self.is_pending and not self.is_expired
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiration (negative if expired)."""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days
    
    @staticmethod
    def generate_expiry(days: int = 7) -> datetime:
        """Generate expiration timestamp."""
        return datetime.now(timezone.utc) + timedelta(days=days)
