"""Repository for Integration CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID

from app.schemas.integration import IntegrationCreate, IntegrationUpdate


class IntegrationRepository:
    """Repository for Integration operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "integrations"
    
    async def create(self, data: IntegrationCreate) -> dict:
        """Create a new integration."""
        insert_data = data.model_dump(exclude_none=True)
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, integration_id: UUID) -> Optional[dict]:
        """Get integration by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(integration_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_slug(self, slug: str) -> Optional[dict]:
        """Get integration by slug."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("slug", slug)\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_all(
        self, 
        active_only: bool = True,
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get all integrations with pagination."""
        query = self.client.table(self.table).select("*", count="exact")
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.order("name").range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_by_category(
        self, 
        category: str,
        active_only: bool = True
    ) -> List[dict]:
        """Get integrations by category."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("category", category)
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.order("name").execute()
        return result.data
    
    async def update(
        self, 
        integration_id: UUID, 
        data: IntegrationUpdate
    ) -> Optional[dict]:
        """Update an integration."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(integration_id)
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(integration_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, integration_id: UUID) -> bool:
        """Delete an integration."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(integration_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def exists_by_slug(self, slug: str) -> bool:
        """Check if integration exists by slug."""
        result = self.client.table(self.table)\
            .select("id")\
            .eq("slug", slug)\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        result = self.client.table(self.table)\
            .select("category")\
            .eq("is_active", True)\
            .execute()
        
        categories = set()
        for item in result.data:
            categories.add(item["category"])
        return sorted(list(categories))
