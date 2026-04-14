"""
Botlixio — FastAPI application factory.

Middleware, CORS, and router registration all happen here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import auth as auth_router
from app.api.v1 import agents as agents_router
from app.api.v1 import knowledge as knowledge_router
from app.api.v1 import chat as chat_router
from app.api.v1.channels import router as channels_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Botlixio API",
        description="AI Agent Builder SaaS — REST API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check — always available
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": "botlixio-api"}

    # API routers
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(agents_router.router, prefix="/api/v1")
    app.include_router(knowledge_router.router, prefix="/api/v1")
    app.include_router(chat_router.router, prefix="/api/v1")
    app.include_router(channels_router, prefix="/api/v1")

    return app


app = create_app()
