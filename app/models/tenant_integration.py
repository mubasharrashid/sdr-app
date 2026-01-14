"""TenantIntegration model - Connected integrations per tenant."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base_class import Base


class TenantIntegration(Base):
    """Tenant-specific integration connection."""
    
    __tablename__ = "tenant_integrations"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    integration_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("integrations.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Connection status
    status = Column(String(20), default="pending", index=True)
    
    # OAuth tokens
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # API credentials
    credentials = Column(JSONB, default=dict)
    
    # OAuth metadata
    oauth_account_id = Column(Text, nullable=True)
    oauth_account_email = Column(Text, nullable=True)
    oauth_scopes = Column(ARRAY(Text), nullable=True)
    
    # Configuration
    settings = Column(JSONB, default=dict)
    
    # Usage tracking
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_sync_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Connected by
    connected_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Timestamps
    connected_at = Column(TIMESTAMP(timezone=True), nullable=True)
    disconnected_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_connected(self) -> bool:
        """Check if integration is connected."""
        return self.status == "connected"
    
    @property
    def is_expired(self) -> bool:
        """Check if OAuth token is expired."""
        if not self.token_expires_at:
            return False
        return self.token_expires_at < datetime.now(timezone.utc)
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires within 5 minutes)."""
        if not self.token_expires_at:
            return False
        from datetime import timedelta
        buffer = datetime.now(timezone.utc) + timedelta(minutes=5)
        return self.token_expires_at < buffer
    
    @property
    def has_error(self) -> bool:
        """Check if integration has error."""
        return self.status == "error" or self.error_count > 0
