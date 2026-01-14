"""
Tenant Repository - Database operations for tenants table.

Uses Supabase REST API for CRUD operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime

from app.schemas.tenant import TenantCreate, TenantUpdate, TenantUpdateAdmin


class TenantRepository:
    """Repository for tenant database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("tenants")
    
    async def create(self, tenant: TenantCreate) -> Dict[str, Any]:
        """Create a new tenant."""
        data = tenant.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        result = self.table.select("*").eq("id", str(tenant_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get tenant by slug."""
        result = self.table.select("*").eq("slug", slug).execute()
        return result.data[0] if result.data else None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all tenants with pagination and filtering."""
        query = self.table.select("*", count="exact")
        
        if status:
            query = query.eq("status", status)
        if plan:
            query = query.eq("plan", plan)
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def update(
        self, 
        tenant_id: UUID, 
        tenant: TenantUpdate | TenantUpdateAdmin
    ) -> Optional[Dict[str, Any]]:
        """Update a tenant."""
        data = tenant.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(tenant_id)
        
        result = self.table.update(data).eq("id", str(tenant_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, tenant_id: UUID) -> bool:
        """Delete a tenant."""
        result = self.table.delete().eq("id", str(tenant_id)).execute()
        return len(result.data) > 0
    
    async def exists_by_slug(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a tenant with the given slug exists."""
        query = self.table.select("id").eq("slug", slug)
        if exclude_id:
            query = query.neq("id", str(exclude_id))
        result = query.execute()
        return len(result.data) > 0
    
    async def count_by_status(self, status: str) -> int:
        """Count tenants by status."""
        result = self.table.select("*", count="exact").eq("status", status).execute()
        return result.count if result.count else 0
    
    async def count_by_plan(self, plan: str) -> int:
        """Count tenants by plan."""
        result = self.table.select("*", count="exact").eq("plan", plan).execute()
        return result.count if result.count else 0
