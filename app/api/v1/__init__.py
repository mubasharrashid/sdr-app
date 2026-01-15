# API v1 package
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.agents import router as agents_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.executions import router as executions_router
from app.api.v1.audit import router as audit_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.leads import router as leads_router

__all__ = [
    "tenants_router", 
    "users_router", 
    "invitations_router", 
    "agents_router", 
    "knowledge_router",
    "integrations_router",
    "workflows_router",
    "executions_router",
    "audit_router",
    "api_keys_router",
    "campaigns_router",
    "leads_router",
]
