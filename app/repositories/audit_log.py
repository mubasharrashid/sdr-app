"""Repository for AuditLog CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from app.schemas.audit_log import AuditLogCreate, AuditLogFilter


class AuditLogRepository:
    """Repository for AuditLog operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "audit_logs"
    
    async def create(self, data: AuditLogCreate) -> dict:
        """Create a new audit log entry."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        for field in ["tenant_id", "user_id", "resource_id"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, log_id: UUID) -> Optional[dict]:
        """Get audit log by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(log_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        filters: Optional[AuditLogFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get audit logs for a tenant with optional filters."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if filters:
            if filters.action:
                query = query.eq("action", filters.action)
            if filters.resource_type:
                query = query.eq("resource_type", filters.resource_type)
            if filters.resource_id:
                query = query.eq("resource_id", str(filters.resource_id))
            if filters.user_id:
                query = query.eq("user_id", str(filters.user_id))
            if filters.severity:
                query = query.eq("severity", filters.severity)
            if filters.start_date:
                query = query.gte("created_at", filters.start_date.isoformat())
            if filters.end_date:
                query = query.lte("created_at", filters.end_date.isoformat())
            if filters.ip_address:
                query = query.eq("ip_address", filters.ip_address)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_by_resource(
        self, 
        resource_type: str,
        resource_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get audit logs for a specific resource."""
        result = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("resource_type", resource_type)\
            .eq("resource_id", str(resource_id))\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_by_user(
        self, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get audit logs for a specific user."""
        result = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("user_id", str(user_id))\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_errors(
        self, 
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get error and critical logs."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .in_("severity", ["error", "critical"])
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_system_logs(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get system-level logs (no tenant)."""
        result = self.client.table(self.table)\
            .select("*", count="exact")\
            .is_("tenant_id", "null")\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def count_by_action(
        self, 
        tenant_id: UUID,
        action: str
    ) -> int:
        """Count logs by action."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .eq("action", action)\
            .execute()
        return result.count or 0
    
    # Note: Audit logs are immutable - no update or delete methods
    # For compliance, logs should never be modified or deleted


# Helper function for logging
async def log_action(
    client,
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    metadata: Optional[dict] = None,
    severity: str = "info",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
) -> dict:
    """Convenience function to create an audit log."""
    repo = AuditLogRepository(client)
    
    changed_fields = None
    if old_values and new_values:
        changed_fields = [k for k in new_values.keys() if old_values.get(k) != new_values.get(k)]
    
    data = AuditLogCreate(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=str(tenant_id) if tenant_id else None,
        user_id=str(user_id) if user_id else None,
        old_values=old_values,
        new_values=new_values,
        changed_fields=changed_fields,
        metadata=metadata or {},
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )
    
    return await repo.create(data)
