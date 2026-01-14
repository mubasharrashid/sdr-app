"""API endpoints for Audit Logs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.audit_log import AuditLogRepository
from app.repositories.tenant import TenantRepository
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilter
)

router = APIRouter(prefix="/audit", tags=["audit"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_audit_repo(
    supabase: Client = Depends(get_supabase)
) -> AuditLogRepository:
    """Get AuditLogRepository instance."""
    return AuditLogRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to audit log data."""
    data["is_error"] = data.get("severity") in ("error", "critical")
    data["is_system_level"] = data.get("tenant_id") is None
    return data


@router.get("/tenants/{tenant_id}", response_model=AuditLogListResponse)
async def list_tenant_audit_logs(
    tenant_id: UUID,
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """List audit logs for a tenant."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    filters = AuditLogFilter(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        severity=severity,
        start_date=start_date,
        end_date=end_date
    )
    
    items, total = await audit_repo.get_by_tenant(
        tenant_id, 
        filters=filters,
        skip=skip, 
        limit=limit
    )
    return AuditLogListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )


@router.get("/tenants/{tenant_id}/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    tenant_id: UUID,
    log_id: UUID,
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """Get a specific audit log entry."""
    log = await audit_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    if log.get("tenant_id") and str(log.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Log belongs to another tenant")
    
    return _add_computed_fields(log)


@router.get("/tenants/{tenant_id}/errors", response_model=AuditLogListResponse)
async def list_error_logs(
    tenant_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """List error and critical logs for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    items, total = await audit_repo.get_errors(tenant_id, skip=skip, limit=limit)
    return AuditLogListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )


@router.get("/resources/{resource_type}/{resource_id}", response_model=AuditLogListResponse)
async def list_resource_audit_logs(
    resource_type: str,
    resource_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """List audit logs for a specific resource."""
    items, total = await audit_repo.get_by_resource(
        resource_type, resource_id, skip=skip, limit=limit
    )
    return AuditLogListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )


@router.get("/users/{user_id}", response_model=AuditLogListResponse)
async def list_user_audit_logs(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """List audit logs for a specific user."""
    items, total = await audit_repo.get_by_user(user_id, skip=skip, limit=limit)
    return AuditLogListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )
