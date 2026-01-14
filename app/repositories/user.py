"""
User Repository - Database operations for users table.

Uses Supabase REST API for CRUD operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime, timezone

from app.schemas.user import UserCreateInternal, UserUpdate, UserUpdateAdmin
from app.core.security import hash_password, verify_password


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("users")
    
    async def create(self, user: UserCreateInternal) -> Dict[str, Any]:
        """Create a new user."""
        data = user.model_dump(exclude_unset=True)
        # Convert UUID to string for JSON serialization
        if 'tenant_id' in data and data['tenant_id']:
            data['tenant_id'] = str(data['tenant_id'])
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        result = self.table.select("*").eq("id", str(user_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_email(self, email: str, tenant_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get user by email, optionally within a specific tenant."""
        query = self.table.select("*").eq("email", email)
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all users for a tenant with pagination and filtering."""
        query = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        if role:
            query = query.eq("role", role)
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def update(
        self, 
        user_id: UUID, 
        user: UserUpdate | UserUpdateAdmin
    ) -> Optional[Dict[str, Any]]:
        """Update a user."""
        data = user.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(user_id)
        
        result = self.table.update(data).eq("id", str(user_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_password(self, user_id: UUID, new_password_hash: str) -> bool:
        """Update user's password."""
        data = {
            "password_hash": new_password_hash,
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        result = self.table.update(data).eq("id", str(user_id)).execute()
        return len(result.data) > 0
    
    async def update_last_login(self, user_id: UUID, ip_address: Optional[str] = None) -> bool:
        """Update user's last login timestamp."""
        data = {
            "last_login_at": datetime.now(timezone.utc).isoformat(),
            "failed_login_attempts": 0,
        }
        if ip_address:
            data["last_login_ip"] = ip_address
        result = self.table.update(data).eq("id", str(user_id)).execute()
        return len(result.data) > 0
    
    async def increment_failed_login(self, user_id: UUID, lock_after: int = 5) -> Dict[str, Any]:
        """Increment failed login attempts and lock if threshold reached."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        attempts = (user.get("failed_login_attempts") or 0) + 1
        data = {"failed_login_attempts": attempts}
        
        # Lock account if too many failed attempts
        if attempts >= lock_after:
            from datetime import timedelta
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            data["locked_until"] = lock_until.isoformat()
        
        result = self.table.update(data).eq("id", str(user_id)).execute()
        return result.data[0] if result.data else None
    
    async def verify_email(self, user_id: UUID) -> bool:
        """Mark user's email as verified."""
        data = {
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.table.update(data).eq("id", str(user_id)).execute()
        return len(result.data) > 0
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        result = self.table.delete().eq("id", str(user_id)).execute()
        return len(result.data) > 0
    
    async def exists_by_email(self, email: str, tenant_id: UUID, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a user with the given email exists in the tenant."""
        query = self.table.select("id").eq("email", email).eq("tenant_id", str(tenant_id))
        if exclude_id:
            query = query.neq("id", str(exclude_id))
        result = query.execute()
        return len(result.data) > 0
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count users in a tenant."""
        result = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count if result.count else 0
    
    async def count_by_role(self, tenant_id: UUID, role: str) -> int:
        """Count users by role in a tenant."""
        result = (
            self.table.select("*", count="exact")
            .eq("tenant_id", str(tenant_id))
            .eq("role", role)
            .execute()
        )
        return result.count if result.count else 0
    
    async def get_tenant_owner(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the owner of a tenant."""
        result = (
            self.table.select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("role", "owner")
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
