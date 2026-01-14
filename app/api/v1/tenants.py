"""
Tenant API Endpoints.

RESTful endpoints for tenant management.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from uuid import UUID
from supabase import create_client, Client

from app.core.config import settings
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantUpdateAdmin,
    TenantResponse,
    TenantListResponse,
)
from app.repositories.tenant import TenantRepository
from app.repositories.agent import AgentRepository


router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(supabase)


def get_agent_repo(supabase: Client = Depends(get_supabase)) -> AgentRepository:
    """Get agent repository."""
    return AgentRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to tenant data."""
    data["is_active"] = data.get("status") == "active"
    data["is_on_paid_plan"] = data.get("plan") in ["starter", "pro", "enterprise"]
    data["has_agent_assigned"] = data.get("assigned_agent_id") is not None
    return data


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant: TenantCreate,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Create a new tenant.
    
    - **name**: Company display name
    - **slug**: URL-safe unique identifier (lowercase, hyphens allowed)
    - **plan**: Subscription tier (free, starter, pro, enterprise)
    """
    # Check if slug already exists
    if await repo.exists_by_slug(tenant.slug):
        raise HTTPException(
            status_code=400,
            detail=f"Tenant with slug '{tenant.slug}' already exists"
        )
    
    result = await repo.create(tenant)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create tenant")
    
    return _add_computed_fields(result)


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    plan: Optional[str] = Query(None, description="Filter by plan"),
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    List all tenants with pagination and optional filters.
    """
    skip = (page - 1) * page_size
    tenants, total = await repo.get_all(
        skip=skip,
        limit=page_size,
        status=status,
        plan=plan,
    )
    
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return TenantListResponse(
        items=[_add_computed_fields(t) for t in tenants],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Get a tenant by ID.
    """
    tenant = await repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return _add_computed_fields(tenant)


@router.get("/slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Get a tenant by slug.
    """
    tenant = await repo.get_by_slug(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return _add_computed_fields(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant: TenantUpdate,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Update a tenant.
    """
    # Check if tenant exists
    existing = await repo.get_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    result = await repo.update(tenant_id, tenant)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update tenant")
    
    return _add_computed_fields(result)


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: UUID,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Delete a tenant.
    
    ⚠️ Warning: This will permanently delete the tenant and all associated data.
    """
    # Check if tenant exists
    existing = await repo.get_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    success = await repo.delete(tenant_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete tenant")
    
    return None


# ============================================================================
# AGENT ASSIGNMENT ENDPOINTS (Admin Only)
# ============================================================================

@router.post("/{tenant_id}/assign-agent", response_model=TenantResponse)
async def assign_agent_to_tenant(
    tenant_id: UUID,
    agent_id: UUID = Query(..., description="ID of the agent to assign"),
    repo: TenantRepository = Depends(get_tenant_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    """
    Assign an AI agent to a tenant.
    
    ⚠️ Admin only endpoint.
    
    - **agent_id**: UUID of the agent to assign
    """
    # Check if tenant exists
    existing = await repo.get_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Validate agent exists
    agent = await agent_repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.get("is_active"):
        raise HTTPException(status_code=400, detail="Agent is not active")
    
    # Update tenant with assigned agent
    result = await repo.assign_agent(tenant_id, agent_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to assign agent")
    
    return _add_computed_fields(result)


@router.delete("/{tenant_id}/unassign-agent", response_model=TenantResponse)
async def unassign_agent_from_tenant(
    tenant_id: UUID,
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Remove agent assignment from a tenant.
    
    ⚠️ Admin only endpoint.
    """
    # Check if tenant exists
    existing = await repo.get_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if not existing.get("assigned_agent_id"):
        raise HTTPException(status_code=400, detail="Tenant has no agent assigned")
    
    # Update tenant to remove agent
    result = await repo.assign_agent(tenant_id, None)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to unassign agent")
    
    return _add_computed_fields(result)
