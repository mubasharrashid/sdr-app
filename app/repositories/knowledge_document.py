"""
KnowledgeDocument Repository - Database operations for knowledge_documents table.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime, timezone

from app.schemas.knowledge_document import KnowledgeDocumentCreateInternal, KnowledgeDocumentUpdate


class KnowledgeDocumentRepository:
    """Repository for knowledge document database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("knowledge_documents")
    
    async def create(self, doc: KnowledgeDocumentCreateInternal) -> Dict[str, Any]:
        """Create a new document."""
        data = doc.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, doc_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        result = self.table.select("*").eq("id", str(doc_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_knowledge_base(
        self,
        kb_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all documents for a knowledge base."""
        query = self.table.select("*", count="exact").eq("knowledge_base_id", str(kb_id))
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all documents for a tenant."""
        query = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id))
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def get_by_hash(self, content_hash: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by content hash (for deduplication)."""
        result = (
            self.table.select("*")
            .eq("content_hash", content_hash)
            .eq("tenant_id", str(tenant_id))
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def update(self, doc_id: UUID, doc: KnowledgeDocumentUpdate) -> Optional[Dict[str, Any]]:
        """Update a document."""
        data = doc.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(doc_id)
        
        result = self.table.update(data).eq("id", str(doc_id)).execute()
        return result.data[0] if result.data else None
    
    async def set_status(
        self, 
        doc_id: UUID, 
        status: str, 
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update document processing status."""
        data = {"status": status}
        if error:
            data["processing_error"] = error
        if status == "ready":
            data["processed_at"] = datetime.now(timezone.utc).isoformat()
        
        result = self.table.update(data).eq("id", str(doc_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_chunks(
        self, 
        doc_id: UUID, 
        chunk_count: int, 
        vector_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Update document chunk information."""
        data = {
            "chunk_count": chunk_count,
            "vector_ids": vector_ids,
            "status": "ready",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.table.update(data).eq("id", str(doc_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, doc_id: UUID) -> bool:
        """Delete a document."""
        result = self.table.delete().eq("id", str(doc_id)).execute()
        return len(result.data) > 0
    
    async def delete_by_knowledge_base(self, kb_id: UUID) -> int:
        """Delete all documents in a knowledge base."""
        result = self.table.delete().eq("knowledge_base_id", str(kb_id)).execute()
        return len(result.data)
    
    async def count_by_knowledge_base(self, kb_id: UUID, status: Optional[str] = None) -> int:
        """Count documents in a knowledge base."""
        query = self.table.select("*", count="exact").eq("knowledge_base_id", str(kb_id))
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.count if result.count else 0
    
    async def get_total_chunks_by_kb(self, kb_id: UUID) -> int:
        """Get total chunk count for a knowledge base."""
        result = (
            self.table.select("chunk_count")
            .eq("knowledge_base_id", str(kb_id))
            .eq("status", "ready")
            .execute()
        )
        return sum(doc.get("chunk_count", 0) for doc in result.data)
