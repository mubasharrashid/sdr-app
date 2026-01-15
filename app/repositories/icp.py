"""Repository for ICPs and ICP Tracking."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.schemas.icp import (
    ICPCreateInternal, ICPUpdate, ICPTrackingCreateInternal, 
    ICPTrackingUpdate, ICPTrackingProgress
)


class ICPRepository:
    """Repository for ICP CRUD operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "icps"
    
    async def create(self, data: ICPCreateInternal) -> Dict[str, Any]:
        """Create a new ICP."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        if "tenant_id" in insert_data:
            insert_data["tenant_id"] = str(insert_data["tenant_id"])
        if "default_campaign_id" in insert_data:
            insert_data["default_campaign_id"] = str(insert_data["default_campaign_id"])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, icp_id: UUID) -> Optional[Dict[str, Any]]:
        """Get ICP by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_code(self, tenant_id: UUID, icp_code: str) -> Optional[Dict[str, Any]]:
        """Get ICP by code within tenant."""
        result = self.client.table(self.table).select("*")\
            .eq("tenant_id", str(tenant_id))\
            .eq("icp_code", icp_code)\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all ICPs for a tenant."""
        query = self.client.table(self.table).select("*").eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("priority").order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        return result.data
    
    async def get_active(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get all active ICPs for a tenant."""
        return await self.get_by_tenant(tenant_id, status="active", limit=100)
    
    async def update(self, icp_id: UUID, data: ICPUpdate) -> Optional[Dict[str, Any]]:
        """Update an ICP."""
        update_data = data.model_dump(exclude_none=True)
        
        if "default_campaign_id" in update_data:
            update_data["default_campaign_id"] = str(update_data["default_campaign_id"])
        
        if not update_data:
            return await self.get_by_id(icp_id)
        
        result = self.client.table(self.table).update(update_data).eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, icp_id: UUID) -> bool:
        """Delete an ICP."""
        result = self.client.table(self.table).delete().eq("id", str(icp_id)).execute()
        return len(result.data) > 0
    
    async def activate(self, icp_id: UUID) -> Optional[Dict[str, Any]]:
        """Activate an ICP."""
        result = self.client.table(self.table).update({"status": "active"}).eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def pause(self, icp_id: UUID) -> Optional[Dict[str, Any]]:
        """Pause an ICP."""
        result = self.client.table(self.table).update({"status": "paused"}).eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def archive(self, icp_id: UUID) -> Optional[Dict[str, Any]]:
        """Archive an ICP."""
        result = self.client.table(self.table).update({"status": "archived"}).eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def increment_leads_fetched(self, icp_id: UUID, count: int = 1) -> Optional[Dict[str, Any]]:
        """Increment the leads fetched counter."""
        icp = await self.get_by_id(icp_id)
        if not icp:
            return None
        
        new_count = (icp.get("leads_fetched_total") or 0) + count
        result = self.client.table(self.table).update({
            "leads_fetched_total": new_count,
            "last_used_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", str(icp_id)).execute()
        return result.data[0] if result.data else None
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count ICPs for a tenant."""
        result = self.client.table(self.table).select("id", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count or 0


class ICPTrackingRepository:
    """Repository for ICP Tracking CRUD operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "icp_tracking"
    
    async def create(self, data: ICPTrackingCreateInternal) -> Dict[str, Any]:
        """Create a new tracking record."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        if "tenant_id" in insert_data and insert_data["tenant_id"]:
            insert_data["tenant_id"] = str(insert_data["tenant_id"])
        if "icp_table_id" in insert_data and insert_data["icp_table_id"]:
            insert_data["icp_table_id"] = str(insert_data["icp_table_id"])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, tracking_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tracking record by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_icp_id(self, icp_id: str) -> Optional[Dict[str, Any]]:
        """Get tracking record by legacy ICP ID string."""
        result = self.client.table(self.table).select("*").eq("icp_id", icp_id).execute()
        return result.data[0] if result.data else None
    
    async def get_by_icp_table_id(self, icp_table_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tracking record by ICP table reference."""
        result = self.client.table(self.table).select("*").eq("icp_table_id", str(icp_table_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all tracking records for a tenant."""
        query = self.client.table(self.table).select("*").eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("updated_at", desc=True)
        result = query.execute()
        return result.data
    
    async def get_active(self, tenant_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all active tracking records."""
        query = self.client.table(self.table).select("*").eq("status", "active")
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.execute()
        return result.data
    
    async def update(self, tracking_id: UUID, data: ICPTrackingUpdate) -> Optional[Dict[str, Any]]:
        """Update a tracking record."""
        update_data = data.model_dump(exclude_none=True)
        
        if not update_data:
            return await self.get_by_id(tracking_id)
        
        result = self.client.table(self.table).update(update_data).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_progress(self, tracking_id: UUID, progress: ICPTrackingProgress) -> Optional[Dict[str, Any]]:
        """Update tracking progress after a fetch batch."""
        record = await self.get_by_id(tracking_id)
        if not record:
            return None
        
        update_data = {
            "current_page": progress.current_page,
            "total_leads_fetched": (record.get("total_leads_fetched") or 0) + progress.leads_fetched,
            "daily_leads_fetched": (record.get("daily_leads_fetched") or 0) + progress.leads_fetched,
            "last_fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        if progress.total_pages:
            update_data["total_pages"] = progress.total_pages
        
        # Check if completed
        if progress.total_pages and progress.current_page >= progress.total_pages:
            update_data["status"] = "completed"
        
        result = self.client.table(self.table).update(update_data).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def set_error(self, tracking_id: UUID, error_message: str) -> Optional[Dict[str, Any]]:
        """Set error on tracking record."""
        result = self.client.table(self.table).update({
            "status": "failed",
            "error_message": error_message,
            "last_error_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def clear_error(self, tracking_id: UUID) -> Optional[Dict[str, Any]]:
        """Clear error and resume tracking."""
        result = self.client.table(self.table).update({
            "status": "active",
            "error_message": None,
            "last_error_at": None
        }).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def pause(self, tracking_id: UUID) -> Optional[Dict[str, Any]]:
        """Pause tracking."""
        result = self.client.table(self.table).update({"status": "paused"}).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def resume(self, tracking_id: UUID) -> Optional[Dict[str, Any]]:
        """Resume tracking."""
        result = self.client.table(self.table).update({"status": "active"}).eq("id", str(tracking_id)).execute()
        return result.data[0] if result.data else None
    
    async def reset_daily_counts(self) -> int:
        """Reset daily counts for all tracking records (called by daily job)."""
        # Get records that need reset (last reset more than 24 hours ago)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        result = self.client.table(self.table).update({
            "daily_leads_fetched": 0,
            "last_daily_reset_at": datetime.now(timezone.utc).isoformat()
        }).or_(
            f"last_daily_reset_at.is.null,last_daily_reset_at.lt.{yesterday}"
        ).execute()
        
        return len(result.data)
    
    async def delete(self, tracking_id: UUID) -> bool:
        """Delete a tracking record."""
        result = self.client.table(self.table).delete().eq("id", str(tracking_id)).execute()
        return len(result.data) > 0
    
    async def get_or_create(
        self, 
        icp_id: str, 
        icp_name: str,
        tenant_id: Optional[UUID] = None,
        icp_table_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get existing tracking record or create new one."""
        existing = await self.get_by_icp_id(icp_id)
        if existing:
            return existing
        
        data = ICPTrackingCreateInternal(
            icp_id=icp_id,
            icp_name=icp_name,
            tenant_id=tenant_id,
            icp_table_id=icp_table_id
        )
        return await self.create(data)
