"""
Invitation Repository - Database operations for invitations table.

Uses Supabase REST API for CRUD operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime, timezone
import secrets

from app.schemas.invitation import InvitationCreateInternal


def generate_invitation_token() -> str:
    """Generate a secure random token for invitation."""
    return secrets.token_urlsafe(32)


class InvitationRepository:
    """Repository for invitation database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("invitations")
    
    async def create(self, invitation: InvitationCreateInternal) -> Dict[str, Any]:
        """Create a new invitation."""
        data = invitation.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, invitation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get invitation by ID."""
        result = self.table.select("*").eq("id", str(invitation_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get invitation by token."""
        result = self.table.select("*").eq("token", token).execute()
        return result.data[0] if result.data else None
    
    async def get_by_email(self, email: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get pending invitation by email within a tenant."""
        result = (
            self.table.select("*")
            .eq("email", email)
            .eq("tenant_id", str(tenant_id))
            .eq("status", "pending")
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all invitations for a tenant with pagination and filtering."""
        query = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def accept(
        self, 
        invitation_id: UUID, 
        accepted_by: UUID
    ) -> Optional[Dict[str, Any]]:
        """Mark invitation as accepted."""
        data = {
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "accepted_by": str(accepted_by),
        }
        result = self.table.update(data).eq("id", str(invitation_id)).execute()
        return result.data[0] if result.data else None
    
    async def cancel(self, invitation_id: UUID) -> Optional[Dict[str, Any]]:
        """Cancel an invitation."""
        data = {"status": "cancelled"}
        result = self.table.update(data).eq("id", str(invitation_id)).execute()
        return result.data[0] if result.data else None
    
    async def expire(self, invitation_id: UUID) -> Optional[Dict[str, Any]]:
        """Mark invitation as expired."""
        data = {"status": "expired"}
        result = self.table.update(data).eq("id", str(invitation_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, invitation_id: UUID) -> bool:
        """Delete an invitation."""
        result = self.table.delete().eq("id", str(invitation_id)).execute()
        return len(result.data) > 0
    
    async def exists_pending_for_email(self, email: str, tenant_id: UUID) -> bool:
        """Check if a pending invitation exists for this email in the tenant."""
        result = (
            self.table.select("id")
            .eq("email", email)
            .eq("tenant_id", str(tenant_id))
            .eq("status", "pending")
            .execute()
        )
        return len(result.data) > 0
    
    async def count_by_tenant(self, tenant_id: UUID, status: Optional[str] = None) -> int:
        """Count invitations for a tenant."""
        query = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id))
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.count if result.count else 0
    
    async def expire_old_invitations(self, tenant_id: Optional[UUID] = None) -> int:
        """Expire all invitations past their expiration date."""
        now = datetime.now(timezone.utc).isoformat()
        query = (
            self.table.update({"status": "expired"})
            .eq("status", "pending")
            .lt("expires_at", now)
        )
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.execute()
        return len(result.data)
    
    async def resend(self, invitation_id: UUID, expires_in_days: int = 7) -> Optional[Dict[str, Any]]:
        """Resend invitation with new token and expiration."""
        from datetime import timedelta
        new_token = generate_invitation_token()
        new_expiry = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        data = {
            "token": new_token,
            "expires_at": new_expiry.isoformat(),
            "status": "pending",
        }
        result = self.table.update(data).eq("id", str(invitation_id)).execute()
        return result.data[0] if result.data else None
