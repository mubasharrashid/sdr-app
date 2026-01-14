"""API endpoints for Integrations."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.integration import IntegrationRepository
from app.repositories.tenant_integration import TenantIntegrationRepository
from app.repositories.tenant import TenantRepository
from app.schemas.integration import (
    IntegrationResponse,
    IntegrationSummary,
    IntegrationListResponse
)
from app.schemas.tenant_integration import (
    TenantIntegrationConnect,
    TenantIntegrationUpdate,
    TenantIntegrationCreateInternal,
    TenantIntegrationUpdateInternal,
    TenantIntegrationResponse,
    TenantIntegrationWithDetails,
    TenantIntegrationListResponse
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_integration_repo(
    supabase: Client = Depends(get_supabase)
) -> IntegrationRepository:
    """Get IntegrationRepository instance."""
    return IntegrationRepository(supabase)


def get_tenant_integration_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantIntegrationRepository:
    """Get TenantIntegrationRepository instance."""
    return TenantIntegrationRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def _add_integration_computed_fields(data: dict) -> dict:
    """Add computed fields to integration data."""
    data["is_oauth"] = data.get("auth_type") == "oauth2"
    data["is_api_key"] = data.get("auth_type") == "api_key"
    return data


def _add_connection_computed_fields(data: dict) -> dict:
    """Add computed fields to tenant integration data."""
    from datetime import datetime, timezone
    
    data["is_connected"] = data.get("status") == "connected"
    
    # Check if expired
    token_expires = data.get("token_expires_at")
    if token_expires:
        if isinstance(token_expires, str):
            from datetime import datetime
            try:
                expires_dt = datetime.fromisoformat(token_expires.replace("Z", "+00:00"))
                data["is_expired"] = expires_dt < datetime.now(timezone.utc)
            except:
                data["is_expired"] = False
        else:
            data["is_expired"] = token_expires < datetime.now(timezone.utc)
    else:
        data["is_expired"] = False
    
    data["has_error"] = data.get("status") == "error" or (data.get("error_count", 0) or 0) > 0
    return data


# ============================================================================
# Available Integrations (Master List)
# ============================================================================

@router.get("/available", response_model=IntegrationListResponse)
async def list_available_integrations(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only show active integrations"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: IntegrationRepository = Depends(get_integration_repo)
):
    """List all available integrations."""
    if category:
        items = await repo.get_by_category(category, active_only=active_only)
        return IntegrationListResponse(items=[_add_integration_computed_fields(i) for i in items], total=len(items))
    
    items, total = await repo.get_all(active_only=active_only, skip=skip, limit=limit)
    return IntegrationListResponse(
        items=[_add_integration_computed_fields(i) for i in items],
        total=total
    )


@router.get("/available/categories", response_model=List[str])
async def list_integration_categories(
    repo: IntegrationRepository = Depends(get_integration_repo)
):
    """List all integration categories."""
    return await repo.get_categories()


@router.get("/available/{integration_id}", response_model=IntegrationResponse)
async def get_available_integration(
    integration_id: UUID,
    repo: IntegrationRepository = Depends(get_integration_repo)
):
    """Get a specific integration by ID."""
    integration = await repo.get_by_id(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _add_integration_computed_fields(integration)


@router.get("/available/slug/{slug}", response_model=IntegrationResponse)
async def get_integration_by_slug(
    slug: str,
    repo: IntegrationRepository = Depends(get_integration_repo)
):
    """Get integration by slug."""
    integration = await repo.get_by_slug(slug)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _add_integration_computed_fields(integration)


# ============================================================================
# Tenant Integrations (Connections)
# ============================================================================

@router.post("/tenants/{tenant_id}/connect", response_model=TenantIntegrationResponse)
async def connect_integration(
    tenant_id: UUID,
    data: TenantIntegrationConnect,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    integration_repo: IntegrationRepository = Depends(get_integration_repo),
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo)
):
    """Connect an integration for a tenant."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify integration exists
    integration = await integration_repo.get_by_id(data.integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Check if already connected
    existing = await connection_repo.get_by_tenant_and_integration(
        tenant_id, data.integration_id
    )
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Integration already connected for this tenant"
        )
    
    # Create connection
    create_data = TenantIntegrationCreateInternal(
        tenant_id=str(tenant_id),
        integration_id=str(data.integration_id),
        status="connected" if data.credentials else "pending",
        credentials=data.credentials or {},
        settings=data.settings or {}
    )
    
    # For API key integrations, mark as connected immediately
    if integration.get("auth_type") == "api_key" and data.credentials:
        from datetime import datetime, timezone
        create_data.connected_at = datetime.now(timezone.utc)
    
    connection = await connection_repo.create(create_data)
    return _add_connection_computed_fields(connection)


@router.get("/tenants/{tenant_id}", response_model=TenantIntegrationListResponse)
async def list_tenant_integrations(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo)
):
    """List all integrations connected by a tenant."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    items, total = await connection_repo.get_by_tenant(
        tenant_id, status=status, skip=skip, limit=limit
    )
    return TenantIntegrationListResponse(
        items=[_add_connection_computed_fields(i) for i in items],
        total=total
    )


@router.get("/tenants/{tenant_id}/{connection_id}", response_model=TenantIntegrationWithDetails)
async def get_tenant_integration(
    tenant_id: UUID,
    connection_id: UUID,
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo),
    integration_repo: IntegrationRepository = Depends(get_integration_repo)
):
    """Get a specific integration connection."""
    connection = await connection_repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if str(connection.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Connection belongs to another tenant")
    
    # Get integration details
    integration = await integration_repo.get_by_id(connection["integration_id"])
    
    result = _add_connection_computed_fields(connection)
    result["integration"] = _add_integration_computed_fields(integration) if integration else None
    return result


@router.patch("/tenants/{tenant_id}/{connection_id}", response_model=TenantIntegrationResponse)
async def update_tenant_integration(
    tenant_id: UUID,
    connection_id: UUID,
    data: TenantIntegrationUpdate,
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo)
):
    """Update integration settings."""
    connection = await connection_repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if str(connection.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Connection belongs to another tenant")
    
    update_data = TenantIntegrationUpdateInternal(
        settings=data.settings,
        credentials=data.credentials
    )
    
    updated = await connection_repo.update(connection_id, update_data)
    return _add_connection_computed_fields(updated)


@router.post("/tenants/{tenant_id}/{connection_id}/disconnect", response_model=TenantIntegrationResponse)
async def disconnect_integration(
    tenant_id: UUID,
    connection_id: UUID,
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo)
):
    """Disconnect an integration."""
    connection = await connection_repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if str(connection.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Connection belongs to another tenant")
    
    disconnected = await connection_repo.disconnect(connection_id)
    return _add_connection_computed_fields(disconnected)


@router.delete("/tenants/{tenant_id}/{connection_id}")
async def delete_tenant_integration(
    tenant_id: UUID,
    connection_id: UUID,
    connection_repo: TenantIntegrationRepository = Depends(get_tenant_integration_repo)
):
    """Delete an integration connection."""
    connection = await connection_repo.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if str(connection.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Connection belongs to another tenant")
    
    await connection_repo.delete(connection_id)
    return {"message": "Integration connection deleted"}
