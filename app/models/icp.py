"""SQLAlchemy model for ICPs (Ideal Customer Profiles)."""
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, 
    CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class ICP(Base):
    """ICP (Ideal Customer Profile) model."""
    
    __tablename__ = "icps"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant (multi-tenancy)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # ICP Identification
    icp_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Reference Person
    reference_person = Column(String(255))
    
    # Targeting Criteria - Company
    target_industries = Column(ARRAY(Text))
    target_company_sizes = Column(ARRAY(Text))
    min_employees = Column(Integer)
    max_employees = Column(Integer)
    target_revenue_range = Column(String(100))
    
    # Targeting Criteria - Geography
    target_countries = Column(ARRAY(Text))
    target_regions = Column(ARRAY(Text))
    target_cities = Column(ARRAY(Text))
    
    # Targeting Criteria - Personas
    target_titles = Column(ARRAY(Text))
    target_seniorities = Column(ARRAY(Text))
    target_departments = Column(ARRAY(Text))
    
    # Targeting Criteria - Technographics
    target_technologies = Column(ARRAY(Text))
    exclude_technologies = Column(ARRAY(Text))
    
    # Targeting Criteria - Keywords
    include_keywords = Column(ARRAY(Text))
    exclude_keywords = Column(ARRAY(Text))
    
    # Data Provider Settings
    data_provider = Column(String(50), default="apollo")
    provider_search_params = Column(JSONB, default={})
    
    # Lead Scoring
    scoring_weights = Column(JSONB, default={})
    min_lead_score = Column(Integer, default=0)
    
    # Campaign Association
    default_campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"))
    
    # Limits & Quotas
    max_leads_to_fetch = Column(Integer)
    daily_fetch_limit = Column(Integer)
    leads_fetched_total = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="active")
    priority = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="icps")
    default_campaign = relationship("Campaign", foreign_keys=[default_campaign_id])
    tracking_records = relationship("ICPTracking", back_populates="icp", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "icp_code", name="unique_tenant_icp_code"),
        CheckConstraint("status IN ('draft', 'active', 'paused', 'completed', 'archived')", name="icps_status_check"),
        CheckConstraint("priority BETWEEN 1 AND 10", name="icps_priority_check"),
        Index("idx_icps_tenant", "tenant_id"),
        Index("idx_icps_status", "status"),
        Index("idx_icps_code", "icp_code"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if ICP is active."""
        return self.status == "active"
    
    @property
    def is_at_limit(self) -> bool:
        """Check if ICP has reached its lead limit."""
        if not self.max_leads_to_fetch:
            return False
        return (self.leads_fetched_total or 0) >= self.max_leads_to_fetch
    
    @property
    def remaining_leads(self) -> int | None:
        """Get remaining leads to fetch."""
        if not self.max_leads_to_fetch:
            return None
        return max(0, self.max_leads_to_fetch - (self.leads_fetched_total or 0))
    
    @property
    def target_criteria_summary(self) -> dict:
        """Get a summary of targeting criteria."""
        return {
            "industries": self.target_industries or [],
            "countries": self.target_countries or [],
            "titles": self.target_titles or [],
            "company_size": f"{self.min_employees or 0}-{self.max_employees or 'any'}"
        }
    
    def __repr__(self) -> str:
        return f"<ICP(id={self.id}, code={self.icp_code}, name={self.name})>"
