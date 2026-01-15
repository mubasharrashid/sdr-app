"""
Tenant Model - Multi-tenant foundation for B2B SaaS platform.

Each tenant represents a client company using the AI Agent Platform.
All other tables reference this table via tenant_id for data isolation.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base


class Tenant(Base):
    """
    Multi-tenant foundation table.
    
    Represents a client company that uses the AI Agent Platform.
    All tenant-scoped data references this table for Row-Level Security.
    """
    
    __tablename__ = "tenants"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Information
    name = Column(String(255), nullable=False, comment="Company display name")
    slug = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="URL-safe unique identifier (e.g., acme-corp)"
    )
    logo_url = Column(Text, comment="URL to company logo")
    primary_color = Column(String(7), comment="Brand color in hex format (#FF5733)")
    
    # Contact Information
    email = Column(String(255), comment="Primary contact email")
    phone = Column(String(50), comment="Primary phone number")
    website = Column(String(255), comment="Company website URL")
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    timezone = Column(String(50), default="UTC", comment="IANA timezone identifier")
    
    # Subscription & Billing
    plan = Column(
        String(50), 
        default="free", 
        index=True,
        comment="Subscription tier: free, starter, pro, enterprise"
    )
    plan_started_at = Column(DateTime(timezone=True))
    plan_expires_at = Column(DateTime(timezone=True))
    billing_email = Column(String(255), comment="Email for invoices and billing")
    stripe_customer_id = Column(String(255), comment="Stripe customer ID for payments")
    
    # Usage Limits
    max_users = Column(Integer, default=5, comment="Maximum allowed users")
    max_leads = Column(Integer, default=1000, comment="Maximum leads in database")
    max_emails_per_day = Column(Integer, default=100, comment="Daily email sending limit")
    max_calls_per_day = Column(Integer, default=50, comment="Daily AI call limit")
    
    # Status & Settings
    status = Column(
        String(20), 
        default="active", 
        index=True,
        comment="Account status: active, suspended, cancelled"
    )
    suspended_reason = Column(Text, comment="Reason for suspension if applicable")
    settings = Column(
        JSON, 
        default=dict,
        comment="Flexible JSON for tenant-specific configuration"
    )
    
    
    # Timestamps
    onboarded_at = Column(DateTime(timezone=True), comment="When onboarding completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships (will be populated as we add more models)
    # users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    # invitations = relationship("Invitation", back_populates="tenant", cascade="all, delete-orphan")
    icps = relationship("ICP", back_populates="tenant", cascade="all, delete-orphan")
    icp_tracking_records = relationship("ICPTracking", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant account is active."""
        return self.status == "active"
    
    @property
    def is_suspended(self) -> bool:
        """Check if tenant account is suspended."""
        return self.status == "suspended"
    
    @property
    def is_on_paid_plan(self) -> bool:
        """Check if tenant is on a paid subscription plan."""
        return self.plan in ["starter", "pro", "enterprise"]
    
    @property
    def is_enterprise(self) -> bool:
        """Check if tenant is on enterprise plan."""
        return self.plan == "enterprise"
    
    def can_add_users(self, current_count: int) -> bool:
        """Check if tenant can add more users."""
        return current_count < self.max_users
    
    def can_add_leads(self, current_count: int) -> bool:
        """Check if tenant can add more leads."""
        return current_count < self.max_leads
