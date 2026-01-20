"""
User API Endpoints.

RESTful endpoints for user management within tenants.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from uuid import UUID
from supabase import create_client, Client

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.schemas.user import (
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserUpdateAdmin,
    UserPasswordChange,
    UserResponse,
    UserListResponse,
)
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response


router = APIRouter(prefix="/users", tags=["Users"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_user_repo(supabase: Client = Depends(get_supabase)) -> UserRepository:
    """Get user repository."""
    return UserRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to user data."""
    data["full_name"] = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    data["is_active"] = data.get("status") == "active"
    data["is_admin"] = data.get("role") in ["owner", "admin"]
    return data


@router.post("", response_model=ApiResponse, status_code=201)
async def create_user(
    user: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Create a new user within a tenant.
    
    - **tenant_id**: ID of the tenant this user belongs to
    - **email**: User's email address (unique within tenant)
    - **password**: User password (min 8 chars, must contain letter and number)
    - **role**: User role (owner, admin, member)
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if email already exists in tenant
    if await repo.exists_by_email(user.email, user.tenant_id):
        raise HTTPException(
            status_code=400,
            detail=f"User with email '{user.email}' already exists in this tenant"
        )
    
    # Check tenant user limit
    user_count = await repo.count_by_tenant(user.tenant_id)
    if user_count >= tenant.get("max_users", 5):
        raise HTTPException(
            status_code=400,
            detail=f"Tenant has reached maximum user limit ({tenant.get('max_users', 5)})"
        )
    
    # Create internal user with hashed password
    internal_user = UserCreateInternal(
        tenant_id=user.tenant_id,
        email=user.email,
        password_hash=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        job_title=user.job_title,
        role=user.role,
        timezone=user.timezone,
        locale=user.locale,
    )
    
    result = await repo.create(internal_user)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    return success_response(data=_add_computed_fields(result), message="User created successfully", status_code=201)


@router.get("/tenant/{tenant_id}", response_model=ApiResponse)
async def list_users_by_tenant(
    tenant_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    repo: UserRepository = Depends(get_user_repo),
):
    """
    List all users in a tenant with pagination and optional filters.
    """
    skip = (page - 1) * pageSize
    users, total = await repo.get_by_tenant(
        tenant_id=tenant_id,
        skip=skip,
        limit=pageSize,
        status=status,
        role=role,
    )
    
    return paginated_response(
        items=[_add_computed_fields(u) for u in users],
        total=total,
        page=page,
        page_size=pageSize,
        message="Users retrieved successfully"
    )


@router.get("/{user_id}", response_model=ApiResponse)
async def get_user(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Get a user by ID.
    """
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return success_response(data=_add_computed_fields(user), message="User retrieved successfully")


@router.get("/email/{email}", response_model=ApiResponse)
async def get_user_by_email(
    email: str,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Get a user by email address.
    """
    user = await repo.get_by_email(email, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return success_response(data=_add_computed_fields(user), message="User retrieved successfully")


@router.patch("/{user_id}", response_model=ApiResponse)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Update a user's profile information.
    """
    existing = await repo.get_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await repo.update(user_id, user)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update user")
    
    return success_response(data=_add_computed_fields(result), message="User updated successfully")


@router.patch("/{user_id}/admin", response_model=ApiResponse)
async def update_user_admin(
    user_id: UUID,
    user: UserUpdateAdmin,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Update a user with admin privileges (role, status, permissions).
    
    ⚠️ This endpoint should be protected with admin authentication.
    """
    existing = await repo.get_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await repo.update(user_id, user)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update user")
    
    return success_response(data=_add_computed_fields(result), message="User updated successfully")


@router.post("/{user_id}/change-password", response_model=ApiResponse)
async def change_password(
    user_id: UUID,
    password_data: UserPasswordChange,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Change a user's password.
    
    Requires the current password for verification.
    """
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_hash = hash_password(password_data.new_password)
    success = await repo.update_password(user_id, new_hash)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to change password")
    
    return success_response(data=None, message="Password changed successfully")


@router.post("/{user_id}/verify-email", response_model=ApiResponse)
async def verify_email(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Mark a user's email as verified.
    
    ⚠️ In production, this would be triggered by an email verification link.
    """
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = await repo.verify_email(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to verify email")
    
    return success_response(data=None, message="Email verified successfully")


@router.delete("/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Delete a user.
    
    ⚠️ Warning: This will permanently delete the user.
    """
    existing = await repo.get_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting tenant owner
    if existing.get("role") == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete tenant owner. Transfer ownership first."
        )
    
    success = await repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    
    return success_response(data=None, message="User deleted successfully")
