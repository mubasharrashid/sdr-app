"""API endpoints for Email Templates."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.email_template import EmailTemplateRepository
from app.repositories.tenant import TenantRepository
from app.repositories.icp import ICPRepository
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateCreateInternal,
    EmailTemplateUpdate,
    EmailTemplateResponse
)
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response

router = APIRouter(prefix="/email-templates", tags=["email-templates"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_email_template_repo(
    supabase: Client = Depends(get_supabase)
) -> EmailTemplateRepository:
    """Get EmailTemplateRepository instance."""
    return EmailTemplateRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def get_icp_repo(
    supabase: Client = Depends(get_supabase)
) -> ICPRepository:
    """Get ICPRepository instance."""
    return ICPRepository(supabase)


def _add_template_computed_fields(data: dict) -> dict:
    """Add computed fields to template data."""
    data["is_used"] = (data.get("times_used") or 0) > 0
    return data


# ============================================================================
# Email Template Endpoints
# ============================================================================

@router.post("/tenants/{tenant_id}", response_model=ApiResponse, status_code=201)
async def create_email_template(
    tenant_id: UUID,
    data: EmailTemplateCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    icp_repo: ICPRepository = Depends(get_icp_repo),
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo)
):
    """Create a new email template."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify ICP if provided
    if data.icp_person_id:
        icp = await icp_repo.get_by_id(data.icp_person_id)
        if not icp:
            raise HTTPException(status_code=404, detail="ICP not found")
        if str(icp.get("tenant_id")) != str(tenant_id):
            raise HTTPException(status_code=403, detail="ICP belongs to another tenant")
    
    create_data = EmailTemplateCreateInternal(
        tenant_id=str(tenant_id),
        **data.model_dump(exclude_none=True)
    )
    
    template = await email_template_repo.create(create_data)
    return success_response(
        data=_add_template_computed_fields(template), 
        message="Email template created successfully", 
        status_code=201
    )


@router.get("/tenants/{tenant_id}", response_model=ApiResponse)
async def list_email_templates(
    tenant_id: UUID,
    icp_person_id: Optional[UUID] = Query(None, description="Filter by ICP person ID"),
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo)
):
    """List email templates for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    skip = (page - 1) * pageSize
    items, total = await email_template_repo.get_by_tenant(
        tenant_id,
        icp_person_id=icp_person_id,
        template_type=template_type,
        is_active=is_active,
        skip=skip,
        limit=pageSize
    )
    return paginated_response(
        items=[_add_template_computed_fields(i) for i in items],
        total=total,
        page=page,
        page_size=pageSize,
        message="Email templates retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/{template_id}", response_model=ApiResponse)
async def get_email_template(
    tenant_id: UUID,
    template_id: UUID,
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo)
):
    """Get a specific email template."""
    template = await email_template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    if str(template.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Email template belongs to another tenant")
    
    return success_response(
        data=_add_template_computed_fields(template), 
        message="Email template retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/icp/{icp_person_id}/sequence/{email_sequence}", response_model=ApiResponse)
async def get_email_template_by_sequence(
    tenant_id: UUID,
    icp_person_id: UUID,
    email_sequence: int = Path(..., ge=1, description="Sequence step number"),
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Get email template by ICP person and sequence number."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify ICP exists
    icp = await icp_repo.get_by_id(icp_person_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    if str(icp.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="ICP belongs to another tenant")
    
    template = await email_template_repo.get_by_icp_and_sequence(
        tenant_id,
        icp_person_id,
        email_sequence
    )
    if not template:
        raise HTTPException(
            status_code=404, 
            detail=f"Email template not found for ICP {icp_person_id} at sequence {email_sequence}"
        )
    
    return success_response(
        data=_add_template_computed_fields(template), 
        message="Email template retrieved successfully"
    )


@router.patch("/tenants/{tenant_id}/{template_id}", response_model=ApiResponse)
async def update_email_template(
    tenant_id: UUID,
    template_id: UUID,
    data: EmailTemplateUpdate,
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo),
    icp_repo: ICPRepository = Depends(get_icp_repo)
):
    """Update an email template."""
    template = await email_template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    if str(template.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Email template belongs to another tenant")
    
    # Verify ICP if changing
    if data.icp_person_id:
        icp = await icp_repo.get_by_id(data.icp_person_id)
        if not icp:
            raise HTTPException(status_code=404, detail="ICP not found")
        if str(icp.get("tenant_id")) != str(tenant_id):
            raise HTTPException(status_code=403, detail="ICP belongs to another tenant")
    
    updated = await email_template_repo.update(template_id, data)
    return success_response(
        data=_add_template_computed_fields(updated), 
        message="Email template updated successfully"
    )


@router.delete("/tenants/{tenant_id}/{template_id}", response_model=ApiResponse)
async def delete_email_template(
    tenant_id: UUID,
    template_id: UUID,
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo)
):
    """Delete an email template."""
    template = await email_template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    if str(template.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Email template belongs to another tenant")
    
    await email_template_repo.delete(template_id)
    return success_response(data=None, message="Email template deleted successfully")


@router.post("/tenants/{tenant_id}/{template_id}/increment-usage", response_model=ApiResponse)
async def increment_template_usage(
    tenant_id: UUID,
    template_id: UUID,
    email_template_repo: EmailTemplateRepository = Depends(get_email_template_repo)
):
    """Increment usage counter for an email template."""
    template = await email_template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    if str(template.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Email template belongs to another tenant")
    
    updated = await email_template_repo.increment_usage(template_id)
    return success_response(
        data=_add_template_computed_fields(updated), 
        message="Template usage incremented successfully"
    )
