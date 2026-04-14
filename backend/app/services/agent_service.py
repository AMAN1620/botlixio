"""Agent service — business logic for agent CRUD and lifecycle."""

import uuid

from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.enums import AgentStatus, AgentTone
from app.models.user import User
from app.repositories.agent_repo import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate

# Free plan agent limit
FREE_PLAN_AGENT_LIMIT = 3

# System prompt templates per tone. {name} and {description} are interpolated at runtime.
_TONE_TEMPLATES: dict[AgentTone, str] = {
    AgentTone.PROFESSIONAL: (
        "You are {name}, a professional AI assistant. {description}\n"
        "Respond formally, accurately, and concisely. Use precise language, "
        "avoid slang, and always stay on topic. If you cannot answer a question "
        "based on the available knowledge, say so clearly rather than guessing."
    ),
    AgentTone.FRIENDLY: (
        "You are {name}, a friendly and helpful AI assistant. {description}\n"
        "Be warm, approachable, and conversational. Use a positive tone, "
        "acknowledge the user's question, and keep responses easy to understand. "
        "If you cannot answer, let them know kindly and suggest alternatives."
    ),
    AgentTone.CASUAL: (
        "You are {name}, a chill and helpful assistant. {description}\n"
        "Keep things relaxed and natural — use everyday language and contractions. "
        "Don't overthink it. If you don't know something, just say so and point "
        "them in the right direction."
    ),
    AgentTone.EMPATHETIC: (
        "You are {name}, a supportive and empathetic AI assistant. {description}\n"
        "Show understanding and patience. Acknowledge the user's situation before "
        "answering. Use a calm, reassuring tone. If you cannot help, express that "
        "you understand their frustration and guide them to the right resource."
    ),
}


def generate_system_prompt(name: str, description: str | None, tone: AgentTone) -> str:
    """Build a system prompt from the agent's tone template, name, and description."""
    template = _TONE_TEMPLATES[tone]
    desc_text = description or f"helping users with questions about {name}"
    return template.format(name=name, description=desc_text)


class AgentService:
    def __init__(self, agent_repo: AgentRepository) -> None:
        self._repo = agent_repo

    async def create_agent(self, *, user: User, data: AgentCreate) -> Agent:
        """Create a new agent, enforcing email verification and free plan limits."""
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required before creating agents.",
            )
        count = await self._repo.count_by_user(user.id)
        if count >= FREE_PLAN_AGENT_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Free plan allows up to {FREE_PLAN_AGENT_LIMIT} agents. Please upgrade.",
            )
        system_prompt = generate_system_prompt(data.name, data.description, data.tone)
        return await self._repo.create(
            user_id=user.id,
            name=data.name,
            description=data.description,
            tone=data.tone,
            system_prompt=system_prompt,
            welcome_message=data.welcome_message,
            fallback_message=data.fallback_message,
            primary_color=data.primary_color,
            model=data.model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )

    async def list_agents(self, *, user: User) -> list[Agent]:
        return await self._repo.get_by_user(user.id)

    async def get_agent(self, *, agent_id: uuid.UUID, user: User) -> Agent:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        if agent.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return agent

    async def update_agent(self, *, agent_id: uuid.UUID, user: User, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id=agent_id, user=user)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return agent
        # Regenerate system_prompt if name, description, or tone changed
        if {"name", "description", "tone"} & updates.keys():
            new_name = updates.get("name", agent.name)
            new_desc = updates.get("description", agent.description)
            new_tone = updates.get("tone", agent.tone)
            updates["system_prompt"] = generate_system_prompt(new_name, new_desc, new_tone)
        return await self._repo.update(agent, **updates)

    async def delete_agent(self, *, agent_id: uuid.UUID, user: User) -> None:
        agent = await self.get_agent(agent_id=agent_id, user=user)
        await self._repo.delete(agent)

    async def deploy_agent(self, *, agent_id: uuid.UUID, user: User) -> Agent:
        agent = await self.get_agent(agent_id=agent_id, user=user)
        if agent.status == AgentStatus.LIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent is already live")
        return await self._repo.update(agent, status=AgentStatus.LIVE)

    async def pause_agent(self, *, agent_id: uuid.UUID, user: User) -> Agent:
        agent = await self.get_agent(agent_id=agent_id, user=user)
        if agent.status != AgentStatus.LIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only live agents can be paused")
        return await self._repo.update(agent, status=AgentStatus.PAUSED)
