"""Pydantic schemas for ICPs (Ideal Customer Profiles)."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class ICPBase(BaseModel):
    """Base schema for ICP."""
    
    icp_code: str = Field(..., max_length=50, description="Unique ICP code")
    name: str = Field(..., max_length=255, description="ICP display name")
    description: Optional[str] = None
    reference_person: Optional[str] = Field(None, max_length=255)
    
    # Targeting - Company
    target_industries: Optional[List[str]] = None
    target_company_sizes: Optional[List[str]] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    target_revenue_range: Optional[str] = None
    
    # Targeting - Geography
    target_countries: Optional[List[str]] = None
    target_regions: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    
    # Targeting - Personas
    target_titles: Optional[List[str]] = None
    target_seniorities: Optional[List[str]] = None
    target_departments: Optional[List[str]] = None
    
    # Targeting - Technographics
    target_technologies: Optional[List[str]] = None
    exclude_technologies: Optional[List[str]] = None
    
    # Targeting - Keywords
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    
    # Data Provider
    data_provider: Optional[str] = Field("apollo", max_length=50)
    provider_search_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Scoring
    scoring_weights: Optional[Dict[str, Any]] = Field(default_factory=dict)
    min_lead_score: Optional[int] = 0
    
    # Limits
    max_leads_to_fetch: Optional[int] = None
    daily_fetch_limit: Optional[int] = None
    
    # Status
    status: Optional[str] = "active"
    priority: Optional[int] = Field(5, ge=1, le=10)


class ICPCreate(ICPBase):
    """Schema for creating an ICP."""
    
    default_campaign_id: Optional[UUID] = None


class ICPCreateInternal(ICPCreate):
    """Internal schema with tenant_id for creation."""
    
    tenant_id: UUID


class ICPUpdate(BaseModel):
    """Schema for updating an ICP."""
    
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    reference_person: Optional[str] = None
    
    # Targeting
    target_industries: Optional[List[str]] = None
    target_company_sizes: Optional[List[str]] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    target_revenue_range: Optional[str] = None
    target_countries: Optional[List[str]] = None
    target_regions: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    target_titles: Optional[List[str]] = None
    target_seniorities: Optional[List[str]] = None
    target_departments: Optional[List[str]] = None
    target_technologies: Optional[List[str]] = None
    exclude_technologies: Optional[List[str]] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    
    # Provider
    data_provider: Optional[str] = None
    provider_search_params: Optional[Dict[str, Any]] = None
    
    # Scoring
    scoring_weights: Optional[Dict[str, Any]] = None
    min_lead_score: Optional[int] = None
    
    # Limits
    max_leads_to_fetch: Optional[int] = None
    daily_fetch_limit: Optional[int] = None
    
    # Status
    status: Optional[str] = None
    priority: Optional[int] = None
    default_campaign_id: Optional[UUID] = None


class ICPResponse(ICPBase):
    """Response schema for ICP."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    default_campaign_id: Optional[UUID] = None
    leads_fetched_total: int = 0
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    # Computed fields
    is_active: Optional[bool] = None
    is_at_limit: Optional[bool] = None
    remaining_leads: Optional[int] = None


class ICPSummary(BaseModel):
    """Summary schema for ICP lists."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    icp_code: str
    name: str
    status: str
    priority: int
    target_countries: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    leads_fetched_total: int = 0
    max_leads_to_fetch: Optional[int] = None
    created_at: datetime


class ICPListResponse(BaseModel):
    """List response for ICPs."""
    
    icps: List[ICPSummary]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# ICP Tracking Schemas
# ============================================================================

class ICPTrackingBase(BaseModel):
    """Base schema for ICP Tracking."""
    
    icp_id: Optional[str] = Field(None, max_length=100, description="Legacy ICP identifier")
    icp_name: Optional[str] = Field(None, max_length=255)
    data_provider: Optional[str] = Field("apollo", max_length=50)
    leads_per_page: Optional[int] = 100


class ICPTrackingCreate(ICPTrackingBase):
    """Schema for creating ICP tracking record."""
    
    icp_table_id: Optional[UUID] = None  # Link to icps table
    provider_search_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ICPTrackingCreateInternal(ICPTrackingCreate):
    """Internal schema with tenant_id."""
    
    tenant_id: Optional[UUID] = None


class ICPTrackingUpdate(BaseModel):
    """Schema for updating ICP tracking."""
    
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    total_leads_fetched: Optional[int] = None
    daily_leads_fetched: Optional[int] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    provider_search_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ICPTrackingProgress(BaseModel):
    """Schema for updating tracking progress."""
    
    current_page: int
    leads_fetched: int  # Leads fetched in this batch
    total_pages: Optional[int] = None


class ICPTrackingResponse(ICPTrackingBase):
    """Response schema for ICP tracking."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: Optional[UUID] = None
    icp_table_id: Optional[UUID] = None
    current_page: int = 1
    total_pages: Optional[int] = None
    total_leads_fetched: int = 0
    daily_leads_fetched: int = 0
    status: str = "active"
    error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    provider_search_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    last_fetched_at: Optional[datetime] = None
    last_daily_reset_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    progress_percent: Optional[float] = None
    has_more_pages: Optional[bool] = None
    has_error: Optional[bool] = None


class ICPTrackingListResponse(BaseModel):
    """List response for ICP tracking."""
    
    tracking_records: List[ICPTrackingResponse]
    total: int
