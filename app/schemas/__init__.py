# Schemas package
from app.schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserUpdateAdmin,
    UserPasswordChange,
    UserResponse,
    UserListResponse,
    UserSummary,
)
from app.schemas.invitation import (
    InvitationBase,
    InvitationCreate,
    InvitationCreateInternal,
    InvitationAccept,
    InvitationResponse,
    InvitationResponseWithToken,
    InvitationListResponse,
    InvitationVerify,
)
from app.schemas.agent import (
    AgentBase,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentSummary,
    AgentListResponse,
)
from app.schemas.tenant_agent import (
    TenantAgentBase,
    TenantAgentCreate,
    TenantAgentCreateInternal,
    TenantAgentUpdate,
    TenantAgentResponse,
    TenantAgentWithAgent,
    TenantAgentListResponse,
    AssignAgentRequest,
)
from app.schemas.knowledge_base import (
    KnowledgeBaseBase,
    KnowledgeBaseCreate,
    KnowledgeBaseCreateInternal,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseSummary,
)
from app.schemas.knowledge_document import (
    KnowledgeDocumentBase,
    KnowledgeDocumentCreate,
    KnowledgeDocumentCreateInternal,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentSummary,
)

__all__ = [
    # Tenant schemas
    "TenantBase",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserCreateInternal",
    "UserUpdate",
    "UserUpdateAdmin",
    "UserPasswordChange",
    "UserResponse",
    "UserListResponse",
    "UserSummary",
    # Invitation schemas
    "InvitationBase",
    "InvitationCreate",
    "InvitationCreateInternal",
    "InvitationAccept",
    "InvitationResponse",
    "InvitationResponseWithToken",
    "InvitationListResponse",
    "InvitationVerify",
    # Agent schemas
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentSummary",
    "AgentListResponse",
    # TenantAgent schemas
    "TenantAgentBase",
    "TenantAgentCreate",
    "TenantAgentCreateInternal",
    "TenantAgentUpdate",
    "TenantAgentResponse",
    "TenantAgentWithAgent",
    "TenantAgentListResponse",
    "AssignAgentRequest",
    # KnowledgeBase schemas
    "KnowledgeBaseBase",
    "KnowledgeBaseCreate",
    "KnowledgeBaseCreateInternal",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseListResponse",
    "KnowledgeBaseSummary",
    # KnowledgeDocument schemas
    "KnowledgeDocumentBase",
    "KnowledgeDocumentCreate",
    "KnowledgeDocumentCreateInternal",
    "KnowledgeDocumentUpdate",
    "KnowledgeDocumentResponse",
    "KnowledgeDocumentListResponse",
    "KnowledgeDocumentSummary",
]
