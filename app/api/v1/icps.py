"""API endpoints for ICPs and ICP Tracking."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.icp import ICPRepository, ICPTrackingRepository
from app.repositories.tenant import TenantRepository
from app.schemas.icp import (
    ICPCreate, ICPCreateInternal, ICPUpdate, ICPResponse, ICPSummary, ICPListResponse,
    ICPTrackingCreate, ICPTrackingCreateInternal, ICPTrackingUpdate, 
    ICPTrackingProgress, ICPTrackingResponse, ICPTrackingListResponse
)

router = APIRouter(prefix="/icps", tags=["icps"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_icp_repo(supabase: Client = Depends(get_supabase)) -> ICPRepository:
    """Get ICPRepository instance."""
    return ICPRepository(supabase)


def get_tracking_repo(supabase: Client = Depends(get_supabase)) -> ICPTrackingRepository:
    """Get ICPTrackingRepository instance."""
    return ICPTrackingRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def _add_computed_fields(icp: dict) -> dict:
    """Add computed fields to ICP response."""
    if icp:
        icp["is_active"] = icp.get("status") == "active"
        
        max_leads = icp.get("max_leads_to_fetch")
        fetched = icp.get("leads_fetched_total") or 0
        
        if max_leads:
            icp["is_at_limit"] = fetched >= max_leads
            icp["remaining_leads"] = max(0, max_leads - fetched)
        else:
            icp["is_at_limit"] = False
            icp["remaining_leads"] = None
    return icp


def _add_tracking_computed_fields(tracking: dict) -> dict:
    """Add computed fields to tracking response."""
    if tracking:
        current = tracking.get("current_page") or 1
        total = tracking.get("total_pages")
        
        if total and total > 0:
            tracking["progress_percent"] = round((current / total) * 100, 2)
            tracking["has_more_pages"] = current < total
        else:
            tracking["progress_percent"] = None
            tracking["has_more_pages"] = True
        
        tracking["has_error"] = (
            tracking.get("status") == "failed" or 
            tracking.get("error_message") is not None
        )
    return tracking


# ============================================================================
# ICP Endpoints
# ============================================================================

@router.post("", response_model=ICPResponse, status_code=201)
async def create_icp(
    tenant_id: UUID,
    data: ICPCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Create a new ICP definition."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check for duplicate code
    existing = await icp_repo.get_by_code(tenant_id, data.icp_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"ICP with code '{data.icp_code}' already exists")
    
    internal_data = ICPCreateInternal(tenant_id=tenant_id, **data.model_dump())
    icp = await icp_repo.create(internal_data)
    
    return _add_computed_fields(icp)


@router.get("", response_model=ICPListResponse)
async def list_icps(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """List ICPs for a tenant."""
    skip = (page - 1) * page_size
    icps = await icp_repo.get_by_tenant(tenant_id, status=status, skip=skip, limit=page_size)
    total = await icp_repo.count_by_tenant(tenant_id)
    
    return ICPListResponse(
        icps=[ICPSummary(**icp) for icp in icps],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{icp_id}", response_model=ICPResponse)
async def get_icp(
    icp_id: UUID,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Get ICP by ID."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    return _add_computed_fields(icp)


@router.patch("/{icp_id}", response_model=ICPResponse)
async def update_icp(
    icp_id: UUID,
    data: ICPUpdate,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Update an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    updated = await icp_repo.update(icp_id, data)
    return _add_computed_fields(updated)


@router.delete("/{icp_id}", status_code=204)
async def delete_icp(
    icp_id: UUID,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Delete an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    await icp_repo.delete(icp_id)


@router.post("/{icp_id}/activate", response_model=ICPResponse)
async def activate_icp(
    icp_id: UUID,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Activate an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    updated = await icp_repo.activate(icp_id)
    return _add_computed_fields(updated)


@router.post("/{icp_id}/pause", response_model=ICPResponse)
async def pause_icp(
    icp_id: UUID,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Pause an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    updated = await icp_repo.pause(icp_id)
    return _add_computed_fields(updated)


@router.post("/{icp_id}/archive", response_model=ICPResponse)
async def archive_icp(
    icp_id: UUID,
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Archive an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    updated = await icp_repo.archive(icp_id)
    return _add_computed_fields(updated)


# ============================================================================
# ICP Tracking Endpoints
# ============================================================================

@router.get("/{icp_id}/tracking", response_model=ICPTrackingResponse)
async def get_icp_tracking(
    icp_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Get tracking record for an ICP."""
    tracking = await tracking_repo.get_by_icp_table_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    return _add_tracking_computed_fields(tracking)


@router.post("/{icp_id}/tracking", response_model=ICPTrackingResponse, status_code=201)
async def create_icp_tracking(
    icp_id: UUID,
    data: ICPTrackingCreate,
    icp_repo: ICPRepository = Depends(get_icp_repo),
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Create tracking record for an ICP."""
    icp = await icp_repo.get_by_id(icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    
    # Check if tracking already exists
    existing = await tracking_repo.get_by_icp_table_id(icp_id)
    if existing:
        raise HTTPException(status_code=400, detail="Tracking record already exists for this ICP")
    
    internal_data = ICPTrackingCreateInternal(
        tenant_id=icp.get("tenant_id"),
        icp_table_id=icp_id,
        icp_id=icp.get("icp_code"),
        icp_name=icp.get("name"),
        **data.model_dump(exclude_none=True)
    )
    tracking = await tracking_repo.create(internal_data)
    
    return _add_tracking_computed_fields(tracking)


@router.patch("/{icp_id}/tracking", response_model=ICPTrackingResponse)
async def update_icp_tracking(
    icp_id: UUID,
    data: ICPTrackingUpdate,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Update tracking record."""
    tracking = await tracking_repo.get_by_icp_table_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.update(tracking["id"], data)
    return _add_tracking_computed_fields(updated)


@router.post("/{icp_id}/tracking/progress", response_model=ICPTrackingResponse)
async def update_tracking_progress(
    icp_id: UUID,
    progress: ICPTrackingProgress,
    icp_repo: ICPRepository = Depends(get_icp_repo),
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Update tracking progress after fetching leads."""
    tracking = await tracking_repo.get_by_icp_table_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    # Update tracking progress
    updated = await tracking_repo.update_progress(tracking["id"], progress)
    
    # Also update ICP leads_fetched_total
    await icp_repo.increment_leads_fetched(icp_id, progress.leads_fetched)
    
    return _add_tracking_computed_fields(updated)


@router.post("/{icp_id}/tracking/pause", response_model=ICPTrackingResponse)
async def pause_tracking(
    icp_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Pause lead fetching."""
    tracking = await tracking_repo.get_by_icp_table_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.pause(tracking["id"])
    return _add_tracking_computed_fields(updated)


@router.post("/{icp_id}/tracking/resume", response_model=ICPTrackingResponse)
async def resume_tracking(
    icp_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Resume lead fetching."""
    tracking = await tracking_repo.get_by_icp_table_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.resume(tracking["id"])
    return _add_tracking_computed_fields(updated)


# ============================================================================
# Standalone Tracking Endpoints (for legacy/Excel ICPs)
# ============================================================================

tracking_router = APIRouter(prefix="/icp-tracking", tags=["icp-tracking"])


@tracking_router.get("", response_model=ICPTrackingListResponse)
async def list_tracking_records(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """List all tracking records."""
    if tenant_id:
        records = await tracking_repo.get_by_tenant(tenant_id, status=status)
    else:
        records = await tracking_repo.get_active() if status == "active" else []
    
    return ICPTrackingListResponse(
        tracking_records=[_add_tracking_computed_fields(r) for r in records],
        total=len(records)
    )


@tracking_router.post("", response_model=ICPTrackingResponse, status_code=201)
async def create_tracking_record(
    data: ICPTrackingCreate,
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID"),
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Create a standalone tracking record (for legacy/Excel ICPs)."""
    internal_data = ICPTrackingCreateInternal(
        tenant_id=tenant_id,
        **data.model_dump(exclude_none=True)
    )
    tracking = await tracking_repo.create(internal_data)
    return _add_tracking_computed_fields(tracking)


@tracking_router.get("/by-icp-id/{icp_id}", response_model=ICPTrackingResponse)
async def get_tracking_by_icp_id(
    icp_id: str,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Get tracking record by legacy ICP ID string."""
    tracking = await tracking_repo.get_by_icp_id(icp_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    return _add_tracking_computed_fields(tracking)


@tracking_router.get("/{tracking_id}", response_model=ICPTrackingResponse)
async def get_tracking_record(
    tracking_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Get tracking record by ID."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    return _add_tracking_computed_fields(tracking)


@tracking_router.patch("/{tracking_id}", response_model=ICPTrackingResponse)
async def update_tracking_record(
    tracking_id: UUID,
    data: ICPTrackingUpdate,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Update a tracking record."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.update(tracking_id, data)
    return _add_tracking_computed_fields(updated)


@tracking_router.post("/{tracking_id}/progress", response_model=ICPTrackingResponse)
async def update_tracking_record_progress(
    tracking_id: UUID,
    progress: ICPTrackingProgress,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Update progress for a tracking record."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.update_progress(tracking_id, progress)
    return _add_tracking_computed_fields(updated)


@tracking_router.post("/{tracking_id}/error", response_model=ICPTrackingResponse)
async def set_tracking_error(
    tracking_id: UUID,
    error_message: str,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Set error on tracking record."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.set_error(tracking_id, error_message)
    return _add_tracking_computed_fields(updated)


@tracking_router.post("/{tracking_id}/clear-error", response_model=ICPTrackingResponse)
async def clear_tracking_error(
    tracking_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Clear error and resume tracking."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    updated = await tracking_repo.clear_error(tracking_id)
    return _add_tracking_computed_fields(updated)


@tracking_router.delete("/{tracking_id}", status_code=204)
async def delete_tracking_record(
    tracking_id: UUID,
    tracking_repo: ICPTrackingRepository = Depends(get_tracking_repo)
):
    """Delete a tracking record."""
    tracking = await tracking_repo.get_by_id(tracking_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    await tracking_repo.delete(tracking_id)
