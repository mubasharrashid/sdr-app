"""API endpoints for API Keys."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.api_key import (
    ApiKeyRepository, 
    generate_api_key, 
    hash_api_key
)
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreateInternal,
    ApiKeyUpdate,
    ApiKeyRevoke,
    ApiKeyResponse,
    ApiKeyResponseWithSecret,
    ApiKeyListResponse
)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_api_key_repo(
    supabase: Client = Depends(get_supabase)
) -> ApiKeyRepository:
    """Get ApiKeyRepository instance."""
    return ApiKeyRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def get_user_repo(
    supabase: Client = Depends(get_supabase)
) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to API key data."""
    from datetime import datetime, timezone
    
    # Check expired
    expires_at = data.get("expires_at")
    if expires_at:
        try:
            if isinstance(expires_at, str):
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            else:
                expires = expires_at
            data["is_expired"] = expires < datetime.now(timezone.utc)
        except:
            data["is_expired"] = False
    else:
        data["is_expired"] = False
    
    data["is_revoked"] = data.get("revoked_at") is not None
    data["is_valid"] = data.get("is_active", False) and not data["is_expired"] and not data["is_revoked"]
    
    return data


@router.post("/tenants/{tenant_id}", response_model=ApiKeyResponseWithSecret)
async def create_api_key(
    tenant_id: UUID,
    data: ApiKeyCreate,
    created_by: UUID,  # In production, get from auth context
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """
    Create a new API key.
    
    Note: The actual key is only returned once on creation.
    Store it securely - it cannot be retrieved again.
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify user exists and belongs to tenant
    user = await user_repo.get_by_id(created_by)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="User does not belong to this tenant")
    
    # Generate the key
    key, prefix, key_hash = generate_api_key()
    
    create_data = ApiKeyCreateInternal(
        tenant_id=str(tenant_id),
        created_by=str(created_by),
        key_prefix=prefix,
        key_hash=key_hash,
        **data.model_dump(exclude_none=True)
    )
    
    api_key = await api_key_repo.create(create_data)
    
    # Add the actual key to response (only time it's shown)
    result = _add_computed_fields(api_key)
    result["key"] = key
    
    return result


@router.get("/tenants/{tenant_id}", response_model=ApiKeyListResponse)
async def list_api_keys(
    tenant_id: UUID,
    include_revoked: bool = Query(False, description="Include revoked keys"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """List all API keys for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    items, total = await api_key_repo.get_by_tenant(
        tenant_id, 
        include_revoked=include_revoked,
        skip=skip, 
        limit=limit
    )
    return ApiKeyListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )


@router.get("/tenants/{tenant_id}/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    tenant_id: UUID,
    key_id: UUID,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """Get a specific API key."""
    api_key = await api_key_repo.get_by_id(key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if str(api_key.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="API key belongs to another tenant")
    
    return _add_computed_fields(api_key)


@router.patch("/tenants/{tenant_id}/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    tenant_id: UUID,
    key_id: UUID,
    data: ApiKeyUpdate,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """Update an API key."""
    api_key = await api_key_repo.get_by_id(key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if str(api_key.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="API key belongs to another tenant")
    
    if api_key.get("revoked_at"):
        raise HTTPException(status_code=400, detail="Cannot update a revoked key")
    
    updated = await api_key_repo.update(key_id, data)
    return _add_computed_fields(updated)


@router.post("/tenants/{tenant_id}/{key_id}/revoke", response_model=ApiKeyResponse)
async def revoke_api_key(
    tenant_id: UUID,
    key_id: UUID,
    revoked_by: UUID,  # In production, get from auth context
    data: Optional[ApiKeyRevoke] = None,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """Revoke an API key."""
    api_key = await api_key_repo.get_by_id(key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if str(api_key.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="API key belongs to another tenant")
    
    if api_key.get("revoked_at"):
        raise HTTPException(status_code=400, detail="Key is already revoked")
    
    reason = data.reason if data else None
    revoked = await api_key_repo.revoke(key_id, revoked_by, reason)
    return _add_computed_fields(revoked)


@router.delete("/tenants/{tenant_id}/{key_id}")
async def delete_api_key(
    tenant_id: UUID,
    key_id: UUID,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """Delete an API key permanently."""
    api_key = await api_key_repo.get_by_id(key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if str(api_key.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="API key belongs to another tenant")
    
    await api_key_repo.delete(key_id)
    return {"message": "API key deleted"}


# ============================================================================
# Key Verification (for middleware/authentication)
# ============================================================================

@router.post("/verify")
async def verify_api_key(
    api_key: str,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo)
):
    """
    Verify an API key.
    
    Returns the key info if valid, 401 if invalid.
    This endpoint is used by API authentication middleware.
    """
    key_record = await api_key_repo.verify_key(api_key)
    
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "valid": True,
        "tenant_id": key_record["tenant_id"],
        "scopes": key_record.get("scopes", ["read"]),
        "rate_limit": key_record.get("rate_limit", 1000)
    }
