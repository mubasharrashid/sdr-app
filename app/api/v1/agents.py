"""
Agent API Endpoints.

RESTful endpoints for agent management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from supabase import create_client, Client

from app.core.config import settings
from app.schemas.agent import (
    AgentResponse,
    AgentListResponse,
    AgentSummary,
)
from app.repositories.agent import AgentRepository
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response


router = APIRouter(prefix="/agents", tags=["Agents"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_agent_repo(supabase: Client = Depends(get_supabase)) -> AgentRepository:
    """Get agent repository."""
    return AgentRepository(supabase)


@router.get("", response_model=ApiResponse)
async def list_agents(
    active_only: bool = True,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """
    List all available AI agents.
    
    Returns Jules (Marketing), Joy (Sales), and George (Customer Success).
    """
    agents = await repo.get_all(active_only=active_only)
    
    return success_response(data={"items": agents, "total": len(agents)}, message="Agents retrieved successfully")


@router.get("/{agent_id}", response_model=ApiResponse)
async def get_agent(
    agent_id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """
    Get an agent by ID.
    """
    agent = await repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return success_response(data=agent, message="Agent retrieved successfully")


@router.get("/slug/{slug}", response_model=ApiResponse)
async def get_agent_by_slug(
    slug: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """
    Get an agent by slug (jules, joy, george).
    """
    agent = await repo.get_by_slug(slug)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return success_response(data=agent, message="Agent retrieved successfully")


@router.get("/category/{category}", response_model=ApiResponse)
async def get_agents_by_category(
    category: str,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """
    Get agents by category (marketing, sales, customer_success).
    """
    agents = await repo.get_by_category(category)
    return success_response(data={"items": agents, "total": len(agents)}, message="Agents retrieved successfully")
