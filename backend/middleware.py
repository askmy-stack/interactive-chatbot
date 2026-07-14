"""Auth, CORS, and client identification middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.config import settings

ASK_CLIENT_HEADER = "X-ASK-Client"
VALID_CLIENTS = frozenset({"standalone-web", "external-app", "cli"})

# Paths that never require API key auth
PUBLIC_PATHS = frozenset({"/health", "/health/providers", "/docs", "/openapi.json", "/redoc"})


def _path_is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/health")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Optional bearer auth when ASK_API_KEY is configured."""

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable[Response]]) -> Response:
        if not settings.ask_api_key or _path_is_public(request.url.path):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth == f"Bearer {settings.ask_api_key}":
            return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})


def require_ops_auth(request: Request) -> None:
    """Require a valid API key for ops endpoints (backup/restore), regardless of
    whether ASK_API_KEY-based auth is otherwise optional for the rest of the API.

    Ops endpoints can read/overwrite files on disk, so they fail closed: if no
    key is configured at all, the endpoints are disabled rather than left open.
    """
    if not settings.ask_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ops endpoints require ASK_API_KEY to be configured",
        )

    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {settings.ask_api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


class ClientHeaderMiddleware(BaseHTTPMiddleware):
    """Attach validated X-ASK-Client to request state."""

    async def dispatch(self, request: Request, call_next: Callable[..., Awaitable[Response]]) -> Response:
        raw = request.headers.get(ASK_CLIENT_HEADER, "external-app")
        request.state.ask_client = raw if raw in VALID_CLIENTS else "external-app"
        return await call_next(request)


def configure_cors(app) -> None:
    origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if settings.ask_external_app_origin:
        origins.append(settings.ask_external_app_origin.rstrip("/"))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
