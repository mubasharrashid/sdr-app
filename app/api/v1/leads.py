"""API endpoints for Leads and related entities."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import csv
import io

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.lead import LeadRepository
from app.repositories.call_task import CallTaskRepository
from app.repositories.email_reply import EmailReplyRepository
from app.repositories.meeting import MeetingRepository
from app.repositories.lead_ai_conversation import LeadAIConversationRepository
from app.repositories.outreach_activity_log import OutreachActivityLogRepository
from app.repositories.tenant import TenantRepository
from app.schemas.lead import (
    LeadCreate, LeadCreateInternal, LeadUpdate, LeadResponse, LeadListResponse, LeadStats
)
from app.schemas.call_task import (
    CallTaskCreate, CallTaskCreateInternal, CallTaskUpdate, CallTaskComplete,
    CallTaskResponse, CallTaskListResponse
)
from app.schemas.email_reply import EmailReplyResponse, EmailReplyListResponse
from app.schemas.meeting import (
    MeetingCreate, MeetingCreateInternal, MeetingUpdate, MeetingComplete,
    MeetingResponse, MeetingListResponse
)
from app.schemas.lead_ai_conversation import LeadAIConversationResponse, LeadAIConversationListResponse
from app.schemas.outreach_activity_log import OutreachActivityLogResponse, OutreachActivityLogListResponse
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response

router = APIRouter(prefix="/leads", tags=["leads"])


def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_lead_repo(supabase: Client = Depends(get_supabase)) -> LeadRepository:
    return LeadRepository(supabase)


def get_call_task_repo(supabase: Client = Depends(get_supabase)) -> CallTaskRepository:
    return CallTaskRepository(supabase)


def get_email_reply_repo(supabase: Client = Depends(get_supabase)) -> EmailReplyRepository:
    return EmailReplyRepository(supabase)


def get_meeting_repo(supabase: Client = Depends(get_supabase)) -> MeetingRepository:
    return MeetingRepository(supabase)


def get_conversation_repo(supabase: Client = Depends(get_supabase)) -> LeadAIConversationRepository:
    return LeadAIConversationRepository(supabase)


def get_activity_repo(supabase: Client = Depends(get_supabase)) -> OutreachActivityLogRepository:
    return OutreachActivityLogRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    return TenantRepository(supabase)


def _add_lead_computed_fields(data: dict) -> dict:
    data["display_name"] = data.get("full_name") or data.get("email") or data.get("phone") or "Unknown"
    data["is_contactable"] = not data.get("is_unsubscribed", False) and not data.get("do_not_contact", False)
    emails_sent = data.get("emails_sent", 0) or 0
    emails_opened = data.get("emails_opened", 0) or 0
    data["open_rate"] = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0.0
    return data


def _add_call_computed_fields(data: dict) -> dict:
    data["is_completed"] = data.get("status") == "completed"
    duration = data.get("call_duration_seconds")
    data["is_successful"] = data["is_completed"] and duration and duration > 0
    data["cost_dollars"] = (data.get("cost_cents", 0) or 0) / 100
    return data


def _add_meeting_computed_fields(data: dict) -> dict:
    data["is_upcoming"] = data.get("status") in ("scheduled", "confirmed")
    data["is_completed"] = data.get("status") == "completed"
    data["was_successful"] = data["is_completed"] and data.get("outcome") == "positive"
    return data


# ============================================================================
# Lead Endpoints
# ============================================================================


@router.post("/tenants/{tenant_id}", response_model=ApiResponse)
async def create_lead(
    tenant_id: UUID, data: LeadCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Create a new lead."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check email uniqueness
    if data.email:
        existing = await lead_repo.get_by_email(tenant_id, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Lead with this email already exists")
    
    create_data = LeadCreateInternal(tenant_id=str(tenant_id), **data.model_dump(exclude_none=True))
    lead = await lead_repo.create(create_data)
    return success_response(data=_add_lead_computed_fields(lead), message="Lead created successfully", status_code=201)


@router.post("/tenants/{tenant_id}/import", response_model=ApiResponse)
async def import_leads(
    tenant_id: UUID,
    file: UploadFile = File(..., description="CSV file containing leads"),
    source: str = Query("manual", description="Lead source (e.g., manual, import, apollo, linkedin)"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo),
):
    """
    Import leads from a CSV file for a tenant.

    Expected CSV headers:
    - Full Name
    - First Name 
    - Last Name 
    - Email
    - Phone
    - Linkedin URL
    - Status
    - Reference Person
    - Organization Name
    - Person Title

    Notes:
    - `tenant_id` comes from the path.
    - `source` is provided as a query parameter (defaults to "manual").
    - Duplicates by email (within the same tenant) are skipped.
    - Rows without both email and phone are skipped (DB constraint).
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Read and decode CSV content
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read or decode CSV file")

    reader = csv.DictReader(io.StringIO(text))

    total_rows = 0
    imported_count = 0
    skipped_count = 0
    row_errors = []

    for row in reader:
        total_rows += 1
        row_number = total_rows + 1  # +1 for header row

        # Extract fields from CSV (note some headers have trailing spaces)
        full_name = (row.get("Full Name") or "").strip() or None
        first_name = (row.get("First Name ") or "").strip() or None
        last_name = (row.get("Last Name ") or "").strip() or None
        email = (row.get("Email") or "").strip() or None
        phone = (row.get("Phone") or "").strip() or None
        linkedin_url = (row.get("Linkedin URL") or "").strip() or None
        status = (row.get("Status") or "").strip() or None
        reference_person = (row.get("Reference Person") or "").strip() or None
        organization_name = (row.get("Organization Name") or "").strip() or None
        person_title = (row.get("Person Title") or "").strip() or None

        # Skip rows without contact info (DB constraint: email OR phone required)
        if not email and not phone:
            skipped_count += 1
            row_errors.append(
                {
                    "row": row_number,
                    "reason": "Missing both email and phone; at least one is required",
                }
            )
            continue

        # Check for duplicate email within tenant
        if email:
            existing = await lead_repo.get_by_email(tenant_id, email)
            if existing:
                skipped_count += 1
                row_errors.append(
                    {
                        "row": row_number,
                        "reason": "Lead with this email already exists",
                        "email": email,
                    }
                )
                continue

        # Build custom_fields and core fields
        custom_fields = {}
        if reference_person:
            # Store reference person in custom_fields to keep schema flexible
            custom_fields["reference_person"] = reference_person

        create_data = LeadCreateInternal(
            tenant_id=str(tenant_id),
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            company_name=organization_name,
            job_title=person_title,
            linkedin_url=linkedin_url,
            source=source,
            status=status or "new",
            custom_fields=custom_fields,
        )

        try:
            lead = await lead_repo.create(create_data)
            imported_count += 1
        except Exception as exc:
            skipped_count += 1
            row_errors.append(
                {
                    "row": row_number,
                    "reason": "Failed to create lead",
                    "error": str(exc),
                }
            )

    summary = {
        "totalRows": total_rows,
        "imported": imported_count,
        "skipped": skipped_count,
        "rowErrors": row_errors,
    }

    return success_response(
        data=summary,
        message="Leads imported successfully" if imported_count else "No leads were imported",
    )


@router.get("/tenants/{tenant_id}/stats", response_model=ApiResponse)
async def lead_stats(
    tenant_id: UUID,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Get lead statistics for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    stats = await lead_repo.get_stats(tenant_id)
    return success_response(data=stats, message="Lead statistics retrieved successfully")


@router.get("/tenants/{tenant_id}", response_model=ApiResponse)
async def list_leads(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    campaign_id: Optional[UUID] = Query(None, description="Filter by campaign ID"),
    source: Optional[str] = Query(None, description="Filter by lead source (e.g., apollo, linkedin, website, import)"),
    start_date: Optional[datetime] = Query(None, description="Filter leads created on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter leads created on or before this date"),
    has_calls_made: Optional[bool] = Query(None, description="Filter leads that have calls made (true) or no calls (false)"),
    has_emails_sent: Optional[bool] = Query(None, description="Filter leads that have emails sent (true) or no emails (false)"),
    has_emails_replied: Optional[bool] = Query(None, description="Filter leads that have email replies (true) or no replies (false)"),
    has_meetings_booked: Optional[bool] = Query(None, description="Filter leads that have meetings booked (true) or no meetings (false)"),
    has_been_contacted: Optional[bool] = Query(None, description="Filter leads that have been contacted via calls or emails (true) or not contacted (false)"),
    q: Optional[str] = Query(None, description="Search by name, email, or company"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """
    List leads for a tenant with optional filters.
    
    Filter options:
    - status: Filter by lead status
    - campaign_id: Filter by campaign
    - source: Filter by lead source (apollo, linkedin, website, import, referral, etc.)
    - start_date/end_date: Filter by creation date range
    - Activity filters: Filter by interaction history (calls, emails, replies, meetings)
    - q: Search by name, email, or company
    """
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    skip = (page - 1) * pageSize
    items, total = await lead_repo.get_by_tenant(
        tenant_id, 
        status, 
        campaign_id, 
        skip, 
        pageSize,
        has_calls_made=has_calls_made,
        has_emails_sent=has_emails_sent,
        has_emails_replied=has_emails_replied,
        has_meetings_booked=has_meetings_booked,
        has_been_contacted=has_been_contacted,
        source=source,
        start_date=start_date,
        end_date=end_date,
        search_query=q
    )
    return paginated_response(
        items=[_add_lead_computed_fields(i) for i in items],
        total=total,
        page=page,
        page_size=pageSize,
        message="Leads retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/search", response_model=ApiResponse)
async def search_leads(
    tenant_id: UUID,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Search leads by name, email, or company."""
    skip = (page - 1) * pageSize
    items, total = await lead_repo.search(tenant_id, q, skip, pageSize)
    return paginated_response(
        items=[_add_lead_computed_fields(i) for i in items],
        total=total,
        page=page,
        page_size=pageSize,
        message="Leads retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/{lead_id}", response_model=ApiResponse)
async def get_lead(
    tenant_id: UUID, lead_id: UUID,
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Get a specific lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Lead belongs to another tenant")
    return success_response(data=_add_lead_computed_fields(lead), message="Lead retrieved successfully")


@router.patch("/tenants/{tenant_id}/{lead_id}", response_model=ApiResponse)
async def update_lead(
    tenant_id: UUID, lead_id: UUID, data: LeadUpdate,
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Update a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Lead belongs to another tenant")
    
    updated = await lead_repo.update(lead_id, data)
    return success_response(data=_add_lead_computed_fields(updated), message="Lead updated successfully")


@router.delete("/tenants/{tenant_id}/{lead_id}", response_model=ApiResponse)
async def delete_lead(
    tenant_id: UUID, lead_id: UUID,
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Delete a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Lead belongs to another tenant")
    
    await lead_repo.delete(lead_id)
    return success_response(data=None, message="Lead deleted successfully")


# ============================================================================
# Call Task Endpoints
# ============================================================================

@router.post("/tenants/{tenant_id}/{lead_id}/calls", response_model=ApiResponse)
async def create_call_task(
    tenant_id: UUID, lead_id: UUID, data: CallTaskCreate,
    lead_repo: LeadRepository = Depends(get_lead_repo),
    call_repo: CallTaskRepository = Depends(get_call_task_repo)
):
    """Create a call task for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Lead belongs to another tenant")
    
    create_data = CallTaskCreateInternal(
        tenant_id=str(tenant_id), lead_id=str(lead_id),
        **data.model_dump(exclude={"lead_id"}, exclude_none=True)
    )
    call = await call_repo.create(create_data)
    return success_response(data=_add_call_computed_fields(call), message="Call task created successfully", status_code=201)


@router.get("/tenants/{tenant_id}/{lead_id}/calls", response_model=ApiResponse)
async def list_lead_calls(
    tenant_id: UUID, lead_id: UUID,
    lead_repo: LeadRepository = Depends(get_lead_repo),
    call_repo: CallTaskRepository = Depends(get_call_task_repo)
):
    """List call tasks for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    calls = await call_repo.get_by_lead(lead_id)
    processed_calls = [_add_call_computed_fields(c) for c in calls]
    return success_response(data={"items": processed_calls, "total": len(processed_calls)}, message="Call tasks retrieved successfully")


# ============================================================================
# Meeting Endpoints
# ============================================================================

@router.post("/tenants/{tenant_id}/{lead_id}/meetings", response_model=ApiResponse)
async def create_meeting(
    tenant_id: UUID, lead_id: UUID, data: MeetingCreate,
    lead_repo: LeadRepository = Depends(get_lead_repo),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    """Create a meeting for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if str(lead.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Lead belongs to another tenant")
    
    create_data = MeetingCreateInternal(
        tenant_id=str(tenant_id), lead_id=str(lead_id),
        **data.model_dump(exclude={"lead_id"}, exclude_none=True)
    )
    meeting = await meeting_repo.create(create_data)
    
    # Update lead metrics
    await lead_repo.increment_metric(lead_id, "meetings_booked")
    
    return success_response(data=_add_meeting_computed_fields(meeting), message="Meeting created successfully", status_code=201)


@router.get("/tenants/{tenant_id}/{lead_id}/meetings", response_model=ApiResponse)
async def list_lead_meetings(
    tenant_id: UUID, lead_id: UUID,
    lead_repo: LeadRepository = Depends(get_lead_repo),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    """List meetings for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    meetings = await meeting_repo.get_by_lead(lead_id)
    processed_meetings = [_add_meeting_computed_fields(m) for m in meetings]
    return success_response(data={"items": processed_meetings, "total": len(processed_meetings)}, message="Meetings retrieved successfully")


# ============================================================================
# Conversation History Endpoints
# ============================================================================

@router.get("/tenants/{tenant_id}/{lead_id}/conversations", response_model=ApiResponse)
async def list_lead_conversations(
    tenant_id: UUID, lead_id: UUID,
    channel: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    lead_repo: LeadRepository = Depends(get_lead_repo),
    conv_repo: LeadAIConversationRepository = Depends(get_conversation_repo)
):
    """Get AI conversation history for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    items, total = await conv_repo.get_by_lead(lead_id, channel, skip, limit)
    
    # Add computed fields
    for item in items:
        item["is_from_ai"] = item.get("role") == "assistant"
        item["is_from_lead"] = item.get("role") == "user"
        item["total_tokens"] = (item.get("prompt_tokens") or 0) + (item.get("completion_tokens") or 0)
    
    return success_response(data={"items": items, "total": total}, message="Conversations retrieved successfully")


# ============================================================================
# Activity Timeline Endpoints
# ============================================================================

@router.get("/tenants/{tenant_id}/{lead_id}/activities", response_model=ApiResponse)
async def list_lead_activities(
    tenant_id: UUID, lead_id: UUID,
    activity_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    lead_repo: LeadRepository = Depends(get_lead_repo),
    activity_repo: OutreachActivityLogRepository = Depends(get_activity_repo)
):
    """Get activity timeline for a lead."""
    lead = await lead_repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    items, total = await activity_repo.get_by_lead(lead_id, activity_type, skip, limit)
    
    # Add computed fields
    for item in items:
        item["is_email_activity"] = item.get("channel") == "email" or (item.get("activity_type") or "").startswith("email_")
        item["is_call_activity"] = item.get("channel") == "phone" or (item.get("activity_type") or "").startswith("call_")
        positive_types = ["email_replied", "email_clicked", "call_connected", "meeting_booked", "linkedin_reply"]
        item["is_positive_engagement"] = item.get("activity_type") in positive_types
    
    return success_response(data={"items": items, "total": total}, message="Activities retrieved successfully")
