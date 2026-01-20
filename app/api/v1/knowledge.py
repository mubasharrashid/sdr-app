"""
Knowledge Base & Document API Endpoints.

RESTful endpoints for managing knowledge bases and documents for RAG.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from typing import Optional
from uuid import UUID
from supabase import create_client, Client
import hashlib

from app.core.config import settings
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseCreateInternal,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)
from app.schemas.knowledge_document import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentCreateInternal,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
)
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.knowledge_document import KnowledgeDocumentRepository
from app.repositories.tenant import TenantRepository
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response


router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_kb_repo(supabase: Client = Depends(get_supabase)) -> KnowledgeBaseRepository:
    """Get knowledge base repository."""
    return KnowledgeBaseRepository(supabase)


def get_doc_repo(supabase: Client = Depends(get_supabase)) -> KnowledgeDocumentRepository:
    """Get knowledge document repository."""
    return KnowledgeDocumentRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(supabase)


def _add_kb_computed_fields(data: dict) -> dict:
    """Add computed fields to knowledge base data."""
    data["is_active"] = data.get("status") == "active"
    return data


def _add_doc_computed_fields(data: dict) -> dict:
    """Add computed fields to document data."""
    data["is_ready"] = data.get("status") == "ready"
    file_size = data.get("file_size") or 0
    data["file_size_kb"] = round(file_size / 1024, 2) if file_size else 0
    return data


# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================

@router.post("/bases", response_model=ApiResponse, status_code=201)
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    repo: KnowledgeBaseRepository = Depends(get_kb_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    Create a new knowledge base.
    
    - **name**: Display name
    - **kb_type**: Type (general, product, faq, competitor, industry)
    - **agent_id**: Optional - restrict to specific agent
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(kb.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Create internal object
    internal_kb = KnowledgeBaseCreateInternal(
        tenant_id=str(kb.tenant_id),
        agent_id=str(kb.agent_id) if kb.agent_id else None,
        name=kb.name,
        description=kb.description,
        kb_type=kb.kb_type,
        embedding_model=kb.embedding_model,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        settings=kb.settings,
    )
    
    result = await repo.create(internal_kb)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create knowledge base")
    
    return success_response(data=_add_kb_computed_fields(result), message="Knowledge base created successfully", status_code=201)


@router.get("/bases/tenant/{tenant_id}", response_model=ApiResponse)
async def list_knowledge_bases(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    kb_type: Optional[str] = Query(None),
    agent_id: Optional[UUID] = Query(None),
    repo: KnowledgeBaseRepository = Depends(get_kb_repo),
):
    """
    List knowledge bases for a tenant.
    """
    skip = (page - 1) * pageSize
    kbs, total = await repo.get_by_tenant(
        tenant_id=tenant_id,
        skip=skip,
        limit=pageSize,
        status=status,
        kb_type=kb_type,
        agent_id=agent_id,
    )
    
    return paginated_response(
        items=[_add_kb_computed_fields(kb) for kb in kbs],
        total=total,
        page=page,
        page_size=pageSize,
        message="Knowledge bases retrieved successfully"
    )


@router.get("/bases/{kb_id}", response_model=ApiResponse)
async def get_knowledge_base(
    kb_id: UUID,
    repo: KnowledgeBaseRepository = Depends(get_kb_repo),
):
    """
    Get a knowledge base by ID.
    """
    kb = await repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return success_response(data=_add_kb_computed_fields(kb), message="Knowledge base retrieved successfully")


@router.patch("/bases/{kb_id}", response_model=ApiResponse)
async def update_knowledge_base(
    kb_id: UUID,
    update: KnowledgeBaseUpdate,
    repo: KnowledgeBaseRepository = Depends(get_kb_repo),
):
    """
    Update a knowledge base.
    """
    existing = await repo.get_by_id(kb_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    result = await repo.update(kb_id, update)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update knowledge base")
    
    return success_response(data=_add_kb_computed_fields(result), message="Knowledge base updated successfully")


@router.delete("/bases/{kb_id}", response_model=ApiResponse)
async def delete_knowledge_base(
    kb_id: UUID,
    repo: KnowledgeBaseRepository = Depends(get_kb_repo),
    doc_repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    Delete a knowledge base and all its documents.
    """
    existing = await repo.get_by_id(kb_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Delete all documents first
    await doc_repo.delete_by_knowledge_base(kb_id)
    
    # Delete knowledge base
    success = await repo.delete(kb_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")
    
    return success_response(data=None, message="Knowledge base deleted successfully")


# ============================================================================
# KNOWLEDGE DOCUMENT ENDPOINTS
# ============================================================================

@router.post("/documents", response_model=ApiResponse, status_code=201)
async def create_document(
    doc: KnowledgeDocumentCreate,
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
    kb_repo: KnowledgeBaseRepository = Depends(get_kb_repo),
):
    """
    Create a new document in a knowledge base.
    
    Note: This creates the document record. Actual file upload and 
    processing is handled separately.
    """
    # Verify knowledge base exists
    kb = await kb_repo.get_by_id(doc.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Generate content hash if content provided
    content_hash = None
    if doc.content_text:
        content_hash = hashlib.sha256(doc.content_text.encode()).hexdigest()
        
        # Check for duplicates
        existing = await repo.get_by_hash(content_hash, doc.tenant_id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Document with identical content already exists"
            )
    
    internal_doc = KnowledgeDocumentCreateInternal(
        knowledge_base_id=str(doc.knowledge_base_id),
        tenant_id=str(doc.tenant_id),
        name=doc.name,
        description=doc.description,
        file_type=doc.file_type,
        file_size=doc.file_size,
        file_url=doc.file_url,
        original_filename=doc.original_filename,
        content_text=doc.content_text,
        content_hash=content_hash,
        uploaded_by=str(doc.uploaded_by) if doc.uploaded_by else None,
        metadata=doc.metadata,
    )
    
    result = await repo.create(internal_doc)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create document")
    
    return success_response(data=_add_doc_computed_fields(result), message="Document created successfully", status_code=201)


@router.get("/documents/kb/{kb_id}", response_model=ApiResponse)
async def list_documents(
    kb_id: UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    List documents in a knowledge base.
    """
    skip = (page - 1) * pageSize
    docs, total = await repo.get_by_knowledge_base(
        kb_id=kb_id,
        skip=skip,
        limit=pageSize,
        status=status,
    )
    
    return paginated_response(
        items=[_add_doc_computed_fields(d) for d in docs],
        total=total,
        page=page,
        page_size=pageSize,
        message="Documents retrieved successfully"
    )


@router.get("/documents/{doc_id}", response_model=ApiResponse)
async def get_document(
    doc_id: UUID,
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    Get a document by ID.
    """
    doc = await repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return success_response(data=_add_doc_computed_fields(doc), message="Document retrieved successfully")


@router.patch("/documents/{doc_id}", response_model=ApiResponse)
async def update_document(
    doc_id: UUID,
    update: KnowledgeDocumentUpdate,
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    Update a document.
    """
    existing = await repo.get_by_id(doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = await repo.update(doc_id, update)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update document")
    
    return success_response(data=_add_doc_computed_fields(result), message="Document updated successfully")


@router.post("/documents/{doc_id}/process", response_model=ApiResponse)
async def process_document(
    doc_id: UUID,
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    Trigger document processing (chunking and vectorization).
    
    Note: In production, this would queue a background job.
    """
    doc = await repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.get("status") == "processing":
        raise HTTPException(status_code=400, detail="Document is already processing")
    
    # Set status to processing
    result = await repo.set_status(doc_id, "processing")
    
    # In production: queue background job here
    # For now, just return with processing status
    
    return success_response(data=_add_doc_computed_fields(result), message="Document processing started")


@router.delete("/documents/{doc_id}", response_model=ApiResponse)
async def delete_document(
    doc_id: UUID,
    repo: KnowledgeDocumentRepository = Depends(get_doc_repo),
):
    """
    Delete a document.
    """
    existing = await repo.get_by_id(doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # In production: also delete vectors from Pinecone
    
    success = await repo.delete(doc_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    return success_response(data=None, message="Document deleted successfully")
