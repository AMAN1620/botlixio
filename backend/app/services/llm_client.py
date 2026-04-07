"""LLM client — thin async wrapper around OpenAI chat completions."""

from openai import AsyncOpenAI

from app.core.config import get_settings


async def chat_completion(
    *,
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Call OpenAI chat completion and return the assistant message content.
    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
