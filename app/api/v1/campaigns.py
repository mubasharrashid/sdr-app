"""API endpoints for Campaigns and Campaign Sequences."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.campaign import CampaignRepository
from app.repositories.campaign_sequence import CampaignSequenceRepository
from app.repositories.tenant import TenantRepository
from app.repositories.agent import AgentRepository
from app.schemas.campaign import (
    CampaignCreate,
    CampaignCreateInternal,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse
)
from app.schemas.campaign_sequence import (
    CampaignSequenceCreate,
    CampaignSequenceCreateInternal,
    CampaignSequenceUpdate,
    CampaignSequenceResponse,
    CampaignSequenceListResponse
)
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_campaign_repo(
    supabase: Client = Depends(get_supabase)
) -> CampaignRepository:
    """Get CampaignRepository instance."""
    return CampaignRepository(supabase)


def get_sequence_repo(
    supabase: Client = Depends(get_supabase)
) -> CampaignSequenceRepository:
    """Get CampaignSequenceRepository instance."""
    return CampaignSequenceRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def get_agent_repo(
    supabase: Client = Depends(get_supabase)
) -> AgentRepository:
    """Get AgentRepository instance."""
    return AgentRepository(supabase)


def _add_campaign_computed_fields(data: dict) -> dict:
    """Add computed fields to campaign data."""
    data["is_active"] = data.get("status") == "active"
    
    emails_sent = data.get("emails_sent", 0) or 0
    emails_opened = data.get("emails_opened", 0) or 0
    emails_replied = data.get("emails_replied", 0) or 0
    total_leads = data.get("total_leads", 0) or 0
    leads_converted = data.get("leads_converted", 0) or 0
    
    data["open_rate"] = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0.0
    data["reply_rate"] = (emails_replied / emails_sent * 100) if emails_sent > 0 else 0.0
    data["conversion_rate"] = (leads_converted / total_leads * 100) if total_leads > 0 else 0.0
    
    return data


def _add_sequence_computed_fields(data: dict) -> dict:
    """Add computed fields to sequence data."""
    delay_days = data.get("delay_days", 0) or 0
    delay_hours = data.get("delay_hours", 0) or 0
    delay_minutes = data.get("delay_minutes", 0) or 0
    data["total_delay_minutes"] = delay_days * 24 * 60 + delay_hours * 60 + delay_minutes
    
    step_type = data.get("step_type", "")
    data["is_email_step"] = step_type == "email"
    data["is_call_step"] = step_type == "call"
    data["is_linkedin_step"] = step_type in ("linkedin_message", "linkedin_connect")
    
    total_sent = data.get("total_sent", 0) or 0
    total_opened = data.get("total_opened", 0) or 0
    total_replied = data.get("total_replied", 0) or 0
    
    data["open_rate"] = (total_opened / total_sent * 100) if total_sent > 0 else 0.0
    data["reply_rate"] = (total_replied / total_sent * 100) if total_sent > 0 else 0.0
    
    return data


# ============================================================================
# Campaign Endpoints
# ============================================================================

@router.post("/tenants/{tenant_id}", response_model=ApiResponse)
async def create_campaign(
    tenant_id: UUID,
    data: CampaignCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Create a new campaign."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify agent if provided
    if data.agent_id:
        agent = await agent_repo.get_by_id(data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    create_data = CampaignCreateInternal(
        tenant_id=str(tenant_id),
        **data.model_dump(exclude_none=True)
    )
    
    campaign = await campaign_repo.create(create_data)
    return success_response(data=_add_campaign_computed_fields(campaign), message="Campaign created successfully", status_code=201)


@router.get("/tenants/{tenant_id}", response_model=ApiResponse)
async def list_campaigns(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    campaign_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """List campaigns for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    skip = (page - 1) * pageSize
    items, total = await campaign_repo.get_by_tenant(
        tenant_id, 
        status=status,
        campaign_type=campaign_type,
        skip=skip, 
        limit=pageSize
    )
    return paginated_response(
        items=[_add_campaign_computed_fields(i) for i in items],
        total=total,
        page=page,
        page_size=pageSize,
        message="Campaigns retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/{campaign_id}", response_model=ApiResponse)
async def get_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Get a specific campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    return success_response(data=_add_campaign_computed_fields(campaign), message="Campaign retrieved successfully")


@router.patch("/tenants/{tenant_id}/{campaign_id}", response_model=ApiResponse)
async def update_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    data: CampaignUpdate,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Update a campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    # Verify agent if changing
    if data.agent_id:
        agent = await agent_repo.get_by_id(data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    updated = await campaign_repo.update(campaign_id, data)
    return success_response(data=_add_campaign_computed_fields(updated), message="Campaign updated successfully")


@router.post("/tenants/{tenant_id}/{campaign_id}/start", response_model=ApiResponse)
async def start_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Start a campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    if campaign.get("status") not in ("draft", "paused", "scheduled"):
        raise HTTPException(status_code=400, detail="Campaign cannot be started from current status")
    
    started = await campaign_repo.start(campaign_id)
    return success_response(data=_add_campaign_computed_fields(started), message="Campaign started successfully")


@router.post("/tenants/{tenant_id}/{campaign_id}/pause", response_model=ApiResponse)
async def pause_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Pause a campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    if campaign.get("status") != "active":
        raise HTTPException(status_code=400, detail="Only active campaigns can be paused")
    
    paused = await campaign_repo.pause(campaign_id)
    return success_response(data=_add_campaign_computed_fields(paused), message="Campaign paused successfully")


@router.post("/tenants/{tenant_id}/{campaign_id}/resume", response_model=ApiResponse)
async def resume_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Resume a paused campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    if campaign.get("status") != "paused":
        raise HTTPException(status_code=400, detail="Only paused campaigns can be resumed")
    
    resumed = await campaign_repo.resume(campaign_id)
    return success_response(data=_add_campaign_computed_fields(resumed), message="Campaign resumed successfully")


@router.post("/tenants/{tenant_id}/{campaign_id}/complete", response_model=ApiResponse)
async def complete_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo)
):
    """Complete a campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    completed = await campaign_repo.complete(campaign_id)
    return success_response(data=_add_campaign_computed_fields(completed), message="Campaign completed successfully")


@router.delete("/tenants/{tenant_id}/{campaign_id}", response_model=ApiResponse)
async def delete_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo),
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """Delete a campaign and its sequences."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    # Delete sequences first (cascade should handle this, but being explicit)
    await sequence_repo.delete_by_campaign(campaign_id)
    await campaign_repo.delete(campaign_id)
    
    return success_response(data=None, message="Campaign deleted successfully")


# ============================================================================
# Campaign Sequence Endpoints
# ============================================================================

@router.post("/tenants/{tenant_id}/{campaign_id}/sequences", response_model=ApiResponse)
async def create_sequence_step(
    tenant_id: UUID,
    campaign_id: UUID,
    data: CampaignSequenceCreate,
    campaign_repo: CampaignRepository = Depends(get_campaign_repo),
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """Create a new sequence step."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    # Check for step number conflict
    existing = await sequence_repo.get_step(campaign_id, data.step_number)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Step {data.step_number} already exists. Use a different step number."
        )
    
    create_data = CampaignSequenceCreateInternal(
        campaign_id=str(campaign_id),
        tenant_id=str(tenant_id),
        **data.model_dump(exclude_none=True)
    )
    
    sequence = await sequence_repo.create(create_data)
    return success_response(data=_add_sequence_computed_fields(sequence), message="Sequence step created successfully", status_code=201)


@router.get("/tenants/{tenant_id}/{campaign_id}/sequences", response_model=ApiResponse)
async def list_sequence_steps(
    tenant_id: UUID,
    campaign_id: UUID,
    active_only: bool = Query(False, description="Only show active steps"),
    campaign_repo: CampaignRepository = Depends(get_campaign_repo),
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """List all sequence steps for a campaign."""
    campaign = await campaign_repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Campaign belongs to another tenant")
    
    items = await sequence_repo.get_by_campaign(campaign_id, active_only=active_only)
    processed_items = [_add_sequence_computed_fields(i) for i in items]
    return success_response(data={"items": processed_items, "total": len(processed_items)}, message="Sequence steps retrieved successfully")


@router.get("/tenants/{tenant_id}/{campaign_id}/sequences/{sequence_id}", response_model=ApiResponse)
async def get_sequence_step(
    tenant_id: UUID,
    campaign_id: UUID,
    sequence_id: UUID,
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """Get a specific sequence step."""
    sequence = await sequence_repo.get_by_id(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence step not found")
    
    if str(sequence.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another tenant")
    
    if str(sequence.get("campaign_id")) != str(campaign_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another campaign")
    
    return success_response(data=_add_sequence_computed_fields(sequence), message="Sequence step retrieved successfully")


@router.patch("/tenants/{tenant_id}/{campaign_id}/sequences/{sequence_id}", response_model=ApiResponse)
async def update_sequence_step(
    tenant_id: UUID,
    campaign_id: UUID,
    sequence_id: UUID,
    data: CampaignSequenceUpdate,
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """Update a sequence step."""
    sequence = await sequence_repo.get_by_id(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence step not found")
    
    if str(sequence.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another tenant")
    
    if str(sequence.get("campaign_id")) != str(campaign_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another campaign")
    
    updated = await sequence_repo.update(sequence_id, data)
    return success_response(data=_add_sequence_computed_fields(updated), message="Sequence step updated successfully")


@router.delete("/tenants/{tenant_id}/{campaign_id}/sequences/{sequence_id}", response_model=ApiResponse)
async def delete_sequence_step(
    tenant_id: UUID,
    campaign_id: UUID,
    sequence_id: UUID,
    sequence_repo: CampaignSequenceRepository = Depends(get_sequence_repo)
):
    """Delete a sequence step."""
    sequence = await sequence_repo.get_by_id(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence step not found")
    
    if str(sequence.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another tenant")
    
    if str(sequence.get("campaign_id")) != str(campaign_id):
        raise HTTPException(status_code=403, detail="Sequence belongs to another campaign")
    
    await sequence_repo.delete(sequence_id)
    return success_response(data=None, message="Sequence step deleted successfully")
