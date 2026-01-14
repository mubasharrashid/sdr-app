"""Repository for ApiKey CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
import secrets
import hashlib

from app.schemas.api_key import (
    ApiKeyCreateInternal,
    ApiKeyUpdate,
    ApiKeyRevoke
)


def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (full_key, key_prefix, key_hash)
    """
    # Generate a secure random key
    key = f"sk_{secrets.token_urlsafe(32)}"
    prefix = key[:10]  # First 10 chars for identification
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    return key, prefix, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


class ApiKeyRepository:
    """Repository for ApiKey operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "api_keys"
    
    async def create(self, data: ApiKeyCreateInternal) -> dict:
        """Create a new API key."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        for field in ["tenant_id", "created_by"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        # Convert datetime
        if "expires_at" in insert_data and insert_data["expires_at"]:
            insert_data["expires_at"] = insert_data["expires_at"].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, key_id: UUID) -> Optional[dict]:
        """Get API key by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(key_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_hash(self, key_hash: str) -> Optional[dict]:
        """Get API key by its hash (for authentication)."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("key_hash", key_hash)\
            .eq("is_active", True)\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_prefix(self, prefix: str) -> Optional[dict]:
        """Get API key by prefix."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("key_prefix", prefix)\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        include_revoked: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all API keys for a tenant."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if not include_revoked:
            query = query.is_("revoked_at", "null")
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def update(
        self, 
        key_id: UUID, 
        data: ApiKeyUpdate
    ) -> Optional[dict]:
        """Update an API key."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(key_id)
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(key_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def revoke(
        self, 
        key_id: UUID,
        revoked_by: UUID,
        reason: Optional[str] = None
    ) -> Optional[dict]:
        """Revoke an API key."""
        update_data = {
            "is_active": False,
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "revoked_by": str(revoked_by),
            "revoke_reason": reason
        }
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(key_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def update_last_used(self, key_id: UUID) -> Optional[dict]:
        """Update last_used_at and increment usage_count."""
        # Get current count
        current = await self.get_by_id(key_id)
        usage_count = (current.get("usage_count", 0) or 0) + 1 if current else 1
        
        update_data = {
            "last_used_at": datetime.now(timezone.utc).isoformat(),
            "usage_count": usage_count
        }
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(key_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, key_id: UUID) -> bool:
        """Delete an API key (prefer revoke instead)."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(key_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def verify_key(self, api_key: str) -> Optional[dict]:
        """
        Verify an API key and return the key record if valid.
        Also updates last_used_at.
        """
        key_hash = hash_api_key(api_key)
        key_record = await self.get_by_hash(key_hash)
        
        if not key_record:
            return None
        
        # Check if expired
        expires_at = key_record.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expires < datetime.now(timezone.utc):
                    return None
            except:
                pass
        
        # Check if revoked
        if key_record.get("revoked_at"):
            return None
        
        # Update usage
        await self.update_last_used(key_record["id"])
        
        return key_record
    
    async def count_active(self, tenant_id: UUID) -> int:
        """Count active API keys for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .eq("is_active", True)\
            .is_("revoked_at", "null")\
            .execute()
        return result.count or 0
