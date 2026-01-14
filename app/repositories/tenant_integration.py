"""Repository for TenantIntegration CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.tenant_integration import (
    TenantIntegrationCreateInternal,
    TenantIntegrationUpdate,
    TenantIntegrationUpdateInternal
)


class TenantIntegrationRepository:
    """Repository for TenantIntegration operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "tenant_integrations"
    
    async def create(self, data: TenantIntegrationCreateInternal) -> dict:
        """Create a new tenant integration connection."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        for field in ["tenant_id", "integration_id", "connected_by"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        # Convert datetime to ISO format
        for field in ["token_expires_at", "connected_at"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = insert_data[field].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, connection_id: UUID) -> Optional[dict]:
        """Get tenant integration by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant_and_integration(
        self, 
        tenant_id: UUID, 
        integration_id: UUID
    ) -> Optional[dict]:
        """Get connection by tenant and integration."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("tenant_id", str(tenant_id))\
            .eq("integration_id", str(integration_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get all integrations for a tenant."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_connected_for_tenant(self, tenant_id: UUID) -> List[dict]:
        """Get all connected integrations for a tenant."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("tenant_id", str(tenant_id))\
            .eq("status", "connected")\
            .execute()
        return result.data
    
    async def update(
        self, 
        connection_id: UUID, 
        data: TenantIntegrationUpdateInternal
    ) -> Optional[dict]:
        """Update a tenant integration."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(connection_id)
        
        # Convert datetime fields
        for field in ["token_expires_at", "last_used_at", "last_sync_at", "disconnected_at"]:
            if field in update_data and update_data[field] is not None:
                update_data[field] = update_data[field].isoformat()
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def connect(
        self,
        connection_id: UUID,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        oauth_account_id: Optional[str] = None,
        oauth_account_email: Optional[str] = None
    ) -> Optional[dict]:
        """Mark integration as connected with OAuth tokens."""
        update_data = {
            "status": "connected",
            "access_token": access_token,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "error_message": None,
            "error_count": 0
        }
        
        if refresh_token:
            update_data["refresh_token"] = refresh_token
        if token_expires_at:
            update_data["token_expires_at"] = token_expires_at.isoformat()
        if oauth_account_id:
            update_data["oauth_account_id"] = oauth_account_id
        if oauth_account_email:
            update_data["oauth_account_email"] = oauth_account_email
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def disconnect(self, connection_id: UUID) -> Optional[dict]:
        """Disconnect an integration."""
        update_data = {
            "status": "disconnected",
            "access_token": None,
            "refresh_token": None,
            "token_expires_at": None,
            "disconnected_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def set_error(
        self, 
        connection_id: UUID, 
        error_message: str
    ) -> Optional[dict]:
        """Set error status on integration."""
        # First get current error count
        current = await self.get_by_id(connection_id)
        error_count = (current.get("error_count", 0) or 0) + 1 if current else 1
        
        update_data = {
            "status": "error",
            "error_message": error_message,
            "error_count": error_count
        }
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def refresh_tokens(
        self,
        connection_id: UUID,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> Optional[dict]:
        """Update tokens after refresh."""
        update_data = {
            "access_token": access_token,
            "status": "connected",
            "error_message": None,
            "error_count": 0
        }
        
        if refresh_token:
            update_data["refresh_token"] = refresh_token
        if token_expires_at:
            update_data["token_expires_at"] = token_expires_at.isoformat()
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def update_last_used(self, connection_id: UUID) -> Optional[dict]:
        """Update last_used_at timestamp."""
        result = self.client.table(self.table)\
            .update({"last_used_at": datetime.now(timezone.utc).isoformat()})\
            .eq("id", str(connection_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, connection_id: UUID) -> bool:
        """Delete a tenant integration connection."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(connection_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def exists(self, tenant_id: UUID, integration_id: UUID) -> bool:
        """Check if connection exists."""
        result = self.client.table(self.table)\
            .select("id")\
            .eq("tenant_id", str(tenant_id))\
            .eq("integration_id", str(integration_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count integrations for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .eq("status", "connected")\
            .execute()
        return result.count or 0
