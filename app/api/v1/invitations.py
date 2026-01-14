"""
Invitation API Endpoints.

RESTful endpoints for user invitation management.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from uuid import UUID
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.security import hash_password
from app.schemas.invitation import (
    InvitationCreate,
    InvitationCreateInternal,
    InvitationAccept,
    InvitationResponse,
    InvitationResponseWithToken,
    InvitationListResponse,
    InvitationVerify,
)
from app.schemas.user import UserCreateInternal
from app.repositories.invitation import InvitationRepository, generate_invitation_token
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository


router = APIRouter(prefix="/invitations", tags=["Invitations"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_invitation_repo(supabase: Client = Depends(get_supabase)) -> InvitationRepository:
    """Get invitation repository."""
    return InvitationRepository(supabase)


def get_user_repo(supabase: Client = Depends(get_supabase)) -> UserRepository:
    """Get user repository."""
    return UserRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to invitation data."""
    expires_at = data.get("expires_at")
    status = data.get("status")
    
    # Check if expired
    is_expired = status == "expired"
    if not is_expired and expires_at:
        if isinstance(expires_at, str):
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        else:
            expires_dt = expires_at
        is_expired = datetime.now(timezone.utc) > expires_dt
    
    data["is_expired"] = is_expired
    data["is_valid"] = status == "pending" and not is_expired
    
    return data


@router.post("", response_model=InvitationResponseWithToken, status_code=201)
async def create_invitation(
    invitation: InvitationCreate,
    repo: InvitationRepository = Depends(get_invitation_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Create a new invitation to join a tenant.
    
    - **tenant_id**: Tenant to invite user to
    - **email**: Email of the person to invite
    - **role**: Role to assign (member, admin, owner)
    - **expires_in_days**: Days until invitation expires (default 7)
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(invitation.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user already exists in tenant
    existing_user = await user_repo.get_by_email(invitation.email, invitation.tenant_id)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User with email '{invitation.email}' already exists in this tenant"
        )
    
    # Check if pending invitation already exists
    if await repo.exists_pending_for_email(invitation.email, invitation.tenant_id):
        raise HTTPException(
            status_code=400,
            detail=f"Pending invitation for '{invitation.email}' already exists"
        )
    
    # Generate token and expiration
    token = generate_invitation_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=invitation.expires_in_days)
    
    # Create internal invitation
    internal_invitation = InvitationCreateInternal(
        tenant_id=str(invitation.tenant_id),
        email=invitation.email,
        role=invitation.role,
        token=token,
        invited_by=str(invitation.invited_by) if invitation.invited_by else None,
        expires_at=expires_at.isoformat(),
        message=invitation.message,
    )
    
    result = await repo.create(internal_invitation)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create invitation")
    
    return _add_computed_fields(result)


@router.get("/tenant/{tenant_id}", response_model=InvitationListResponse)
async def list_invitations_by_tenant(
    tenant_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    repo: InvitationRepository = Depends(get_invitation_repo),
):
    """
    List all invitations for a tenant with pagination.
    """
    skip = (page - 1) * page_size
    invitations, total = await repo.get_by_tenant(
        tenant_id=tenant_id,
        skip=skip,
        limit=page_size,
        status=status,
    )
    
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return InvitationListResponse(
        items=[_add_computed_fields(i) for i in invitations],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/verify/{token}", response_model=InvitationVerify)
async def verify_invitation(
    token: str,
    repo: InvitationRepository = Depends(get_invitation_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Verify an invitation token and get details.
    
    Used by frontend to show invitation details before acceptance.
    """
    invitation = await repo.get_by_token(token)
    
    if not invitation:
        return InvitationVerify(valid=False)
    
    # Check status and expiration
    status = invitation.get("status")
    expires_at = invitation.get("expires_at")
    
    is_expired = status == "expired"
    if not is_expired and expires_at:
        if isinstance(expires_at, str):
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        else:
            expires_dt = expires_at
        is_expired = datetime.now(timezone.utc) > expires_dt
    
    is_valid = status == "pending" and not is_expired
    
    if not is_valid:
        return InvitationVerify(valid=False)
    
    # Get tenant name
    tenant = await tenant_repo.get_by_id(invitation.get("tenant_id"))
    tenant_name = tenant.get("name") if tenant else None
    
    return InvitationVerify(
        valid=True,
        email=invitation.get("email"),
        role=invitation.get("role"),
        tenant_name=tenant_name,
        expires_at=expires_at,
        message=invitation.get("message"),
    )


@router.post("/accept", response_model=dict)
async def accept_invitation(
    acceptance: InvitationAccept,
    repo: InvitationRepository = Depends(get_invitation_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Accept an invitation and create user account.
    
    - **token**: Invitation token
    - **password**: Password for the new account
    - **first_name**: First name
    - **last_name**: Last name
    """
    # Get invitation by token
    invitation = await repo.get_by_token(acceptance.token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Verify invitation is valid
    invitation_with_computed = _add_computed_fields(invitation.copy())
    if not invitation_with_computed.get("is_valid"):
        if invitation_with_computed.get("is_expired"):
            raise HTTPException(status_code=400, detail="Invitation has expired")
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")
    
    tenant_id = invitation.get("tenant_id")
    email = invitation.get("email")
    role = invitation.get("role")
    
    # Verify tenant still exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no longer exists")
    
    # Check tenant user limit
    user_count = await user_repo.count_by_tenant(tenant_id)
    if user_count >= tenant.get("max_users", 5):
        raise HTTPException(
            status_code=400,
            detail="Tenant has reached maximum user limit"
        )
    
    # Create user account
    user_data = UserCreateInternal(
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password(acceptance.password),
        first_name=acceptance.first_name,
        last_name=acceptance.last_name,
        role=role,
        is_verified=True,  # Email verified by accepting invitation
    )
    
    new_user = await user_repo.create(user_data)
    if not new_user:
        raise HTTPException(status_code=500, detail="Failed to create user account")
    
    # Mark invitation as accepted
    await repo.accept(invitation.get("id"), new_user.get("id"))
    
    return {
        "message": "Invitation accepted successfully",
        "user_id": new_user.get("id"),
        "email": email,
        "tenant_id": tenant_id,
    }


@router.get("/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    invitation_id: UUID,
    repo: InvitationRepository = Depends(get_invitation_repo),
):
    """
    Get an invitation by ID.
    """
    invitation = await repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return _add_computed_fields(invitation)


@router.post("/{invitation_id}/cancel", response_model=InvitationResponse)
async def cancel_invitation(
    invitation_id: UUID,
    repo: InvitationRepository = Depends(get_invitation_repo),
):
    """
    Cancel a pending invitation.
    """
    invitation = await repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending invitations")
    
    result = await repo.cancel(invitation_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to cancel invitation")
    
    return _add_computed_fields(result)


@router.post("/{invitation_id}/resend", response_model=InvitationResponseWithToken)
async def resend_invitation(
    invitation_id: UUID,
    expires_in_days: int = Query(7, ge=1, le=30),
    repo: InvitationRepository = Depends(get_invitation_repo),
):
    """
    Resend an invitation with a new token and expiration.
    """
    invitation = await repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.get("status") == "accepted":
        raise HTTPException(status_code=400, detail="Cannot resend accepted invitation")
    
    result = await repo.resend(invitation_id, expires_in_days)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to resend invitation")
    
    return _add_computed_fields(result)


@router.delete("/{invitation_id}", status_code=204)
async def delete_invitation(
    invitation_id: UUID,
    repo: InvitationRepository = Depends(get_invitation_repo),
):
    """
    Delete an invitation.
    """
    invitation = await repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    success = await repo.delete(invitation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete invitation")
    
    return None
