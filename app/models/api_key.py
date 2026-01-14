"""ApiKey model - API key management."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, INET
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timezone

from app.db.base_class import Base


class ApiKey(Base):
    """API key for external access."""
    
    __tablename__ = "api_keys"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Ownership
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    created_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Key identification
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Key data
    key_prefix = Column(String(10), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, index=True)
    
    # Permissions
    scopes = Column(ARRAY(Text), default=["read"])
    allowed_ips = Column(ARRAY(INET), nullable=True)
    
    # Rate limiting
    rate_limit = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Expiration
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    
    # Usage tracking
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Revocation
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoked_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    revoke_reason = Column(Text, nullable=True)
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now(timezone.utc)
    
    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked."""
        return self.revoked_at is not None
    
    @property
    def is_valid(self) -> bool:
        """Check if key is valid for use."""
        return self.is_active and not self.is_expired and not self.is_revoked
    
    @property
    def has_scope(self) -> callable:
        """Return function to check scope."""
        def check(scope: str) -> bool:
            return scope in (self.scopes or [])
        return check
