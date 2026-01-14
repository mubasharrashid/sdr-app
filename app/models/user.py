"""
User Model - User accounts for the multi-tenant platform.

Each user belongs to exactly one tenant and has role-based access control.
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base


class User(Base):
    """
    User accounts table.
    
    Each user belongs to exactly one tenant. Users have roles (owner, admin, member)
    that determine their access level within the tenant.
    """
    
    __tablename__ = "users"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant relationship
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    
    # Authentication
    email = Column(String(255), nullable=False, comment="User email address")
    password_hash = Column(String(255), nullable=False, comment="Bcrypt password hash")
    
    # Profile Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, comment="URL to user avatar image")
    phone = Column(String(50))
    job_title = Column(String(100))
    
    # Role & Permissions
    role = Column(
        String(20), 
        default="member",
        comment="User role: owner, admin, member"
    )
    permissions = Column(
        JSON, 
        default=list,
        comment="Array of specific permissions"
    )
    
    # Account Status
    status = Column(
        String(20), 
        default="active", 
        index=True,
        comment="Account status: active, inactive, suspended"
    )
    is_verified = Column(Boolean, default=False, comment="Email verification status")
    verified_at = Column(DateTime(timezone=True))
    
    # Security
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(45), comment="IPv4 or IPv6 address")
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), comment="Account lockout expiry")
    password_changed_at = Column(DateTime(timezone=True))
    
    # Preferences
    timezone = Column(String(50), comment="User's preferred timezone")
    locale = Column(String(10), default="en", comment="User's preferred language")
    preferences = Column(JSON, default=dict, comment="User-specific settings")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == "active"
    
    @property
    def is_owner(self) -> bool:
        """Check if user is tenant owner."""
        return self.role == "owner"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin or owner."""
        return self.role in ["owner", "admin"]
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) < self.locked_until
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.role == "owner":
            return True  # Owners have all permissions
        return permission in (self.permissions or [])
