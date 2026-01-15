"""SQLAlchemy model for ICP Tracking."""
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, 
    CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class ICPTracking(Base):
    """ICP Tracking model for lead fetching progress."""
    
    __tablename__ = "icp_tracking"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant (multi-tenancy) - nullable for backward compatibility
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    
    # ICP Reference (optional - for icps table link)
    icp_table_id = Column(UUID(as_uuid=True), ForeignKey("icps.id", ondelete="SET NULL"))
    
    # Legacy ICP identification (for Excel-defined ICPs)
    icp_id = Column(String(100))  # e.g., "ICP-UAE-PWR-UTIL-01"
    icp_name = Column(String(255))
    
    # Pagination Tracking
    current_page = Column(Integer, default=1)
    total_pages = Column(Integer)
    leads_per_page = Column(Integer, default=100)
    
    # Progress Tracking
    total_leads_fetched = Column(Integer, default=0)
    daily_leads_fetched = Column(Integer, default=0)
    last_daily_reset_at = Column(DateTime(timezone=True))
    
    # Data Provider
    data_provider = Column(String(50), default="apollo")
    provider_search_id = Column(String(255))  # External job/search ID
    
    # Status
    status = Column(String(20), default="active")
    error_message = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    # Timestamps
    last_fetched_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="icp_tracking_records")
    icp = relationship("ICP", back_populates="tracking_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'completed', 'failed')", name="icp_tracking_status_check"),
        Index("idx_icp_tracking_tenant", "tenant_id"),
        Index("idx_icp_tracking_icp_table", "icp_table_id"),
        Index("idx_icp_tracking_status", "status"),
        Index("idx_icp_tracking_icp_id", "icp_id"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if tracking is active."""
        return self.status == "active"
    
    @property
    def is_completed(self) -> bool:
        """Check if tracking is completed."""
        return self.status == "completed"
    
    @property
    def has_error(self) -> bool:
        """Check if tracking has an error."""
        return self.status == "failed" or self.error_message is not None
    
    @property
    def progress_percent(self) -> float | None:
        """Calculate progress percentage."""
        if not self.total_pages or self.total_pages == 0:
            return None
        return round((self.current_page / self.total_pages) * 100, 2)
    
    @property
    def has_more_pages(self) -> bool:
        """Check if there are more pages to fetch."""
        if not self.total_pages:
            return True  # Unknown, assume yes
        return self.current_page < self.total_pages
    
    @property
    def display_name(self) -> str:
        """Get display name (from icp table or legacy fields)."""
        if self.icp:
            return self.icp.name
        return self.icp_name or self.icp_id or "Unknown ICP"
    
    def __repr__(self) -> str:
        return f"<ICPTracking(id={self.id}, icp={self.icp_id}, page={self.current_page})>"
