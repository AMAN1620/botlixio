"""Agent API routes — /api/v1/agents"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.agent_repo import AgentRepository
from app.schemas.agent import AgentCreate, AgentListResponse, AgentResponse, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(AgentRepository(db))


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = await svc.create_agent(user=current_user, data=data)
    return AgentResponse.model_validate(agent)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentListResponse:
    agents = await svc.list_agents(user=current_user)
    return AgentListResponse(
        data=[AgentResponse.model_validate(a) for a in agents],
        total=len(agents),
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = await svc.get_agent(agent_id=agent_id, user=current_user)
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = await svc.update_agent(agent_id=agent_id, user=current_user, data=data)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> None:
    await svc.delete_agent(agent_id=agent_id, user=current_user)


@router.post("/{agent_id}/deploy", response_model=AgentResponse)
async def deploy_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = await svc.deploy_agent(agent_id=agent_id, user=current_user)
    return AgentResponse.model_validate(agent)


@router.post("/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = await svc.pause_agent(agent_id=agent_id, user=current_user)
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}/embed-code")
async def get_embed_code(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: AgentService = Depends(_get_service),
) -> dict:
    agent = await svc.get_agent(agent_id=agent_id, user=current_user)
    snippet = f"""<!-- Botlixio Widget -->
<script>
  window.BotlixioAgentId = "{agent.id}";
  window.BotlixioApiUrl = "http://localhost:8000";
</script>
<script src="http://localhost:3000/widget.js" async></script>"""
    return {"agent_id": str(agent.id), "agent_name": agent.name, "snippet": snippet}
