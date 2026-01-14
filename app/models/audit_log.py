"""AuditLog model - System-wide audit trail."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, INET
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class AuditLog(Base):
    """System-wide audit log entry."""
    
    __tablename__ = "audit_logs"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Context
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Change tracking
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    changed_fields = Column(ARRAY(Text), nullable=True)
    
    # Request context
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # API context
    endpoint = Column(String(255), nullable=True)
    http_method = Column(String(10), nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Severity
    severity = Column(String(20), default="info", index=True)
    
    # Timestamp (immutable - no updated_at)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    
    @property
    def is_error(self) -> bool:
        """Check if log is error or critical."""
        return self.severity in ("error", "critical")
    
    @property
    def is_system_level(self) -> bool:
        """Check if log is system-level (no tenant)."""
        return self.tenant_id is None
