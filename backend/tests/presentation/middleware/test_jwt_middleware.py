from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import PlainTextResponse

import app.presentation.middleware.jwt_middleware as jwt_middleware_module
from app.presentation.middleware.jwt_middleware import JWTMiddleware


def _make_request(path: str, method: str = "GET", headers: dict[str, str] | None = None) -> Request:
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode(), value.encode()))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, _receive)


@pytest.mark.asyncio
async def test_dispatch_allows_options_without_auth(monkeypatch):
    middleware = JWTMiddleware(FastAPI(), logger=MagicMock())
    request = _make_request("/stock", method="OPTIONS")
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_rejects_missing_token_on_protected_route(monkeypatch):
    middleware = JWTMiddleware(FastAPI(), logger=MagicMock())
    request = _make_request("/stock", headers={"accept": "application/json"})
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    monkeypatch.setattr(jwt_middleware_module.JWTService, "extract_bearer_token", lambda _header: None)

    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(request, call_next)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authentication token"


@pytest.mark.asyncio
async def test_dispatch_allows_html_request_without_token(monkeypatch):
    middleware = JWTMiddleware(FastAPI(), logger=MagicMock())
    request = _make_request("/stock", headers={"accept": "text/html"})
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    monkeypatch.setattr(jwt_middleware_module.JWTService, "extract_bearer_token", lambda _header: None)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_accepts_valid_token_and_populates_request_user(monkeypatch):
    logger = MagicMock()
    middleware = JWTMiddleware(FastAPI(), logger=logger)
    request = _make_request("/users", headers={"authorization": "Bearer token"})
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    monkeypatch.setattr(jwt_middleware_module.JWTService, "extract_bearer_token", lambda _header: "token")
    monkeypatch.setattr(
        jwt_middleware_module.JWTService,
        "decode_token",
        lambda _token: {"sub": "7", "username": "facu", "role": "ADMIN"},
    )

    fake_uow = AsyncMock()
    fake_uow.__aenter__ = AsyncMock(return_value=fake_uow)
    fake_uow.__aexit__ = AsyncMock(return_value=None)
    fake_uow.users = SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(id=7)))
    monkeypatch.setattr(jwt_middleware_module, "SqlAlchemyUnitOfWork", lambda: fake_uow)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    assert request.state.current_user["id"] == 7
    assert request.state.current_user["username"] == "facu"
    assert request.state.current_user["role"] == "ADMIN"
    call_next.assert_awaited_once()
    logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_rejects_invalid_token(monkeypatch):
    middleware = JWTMiddleware(FastAPI(), logger=MagicMock())
    request = _make_request("/users", headers={"authorization": "Bearer bad-token"})
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    monkeypatch.setattr(jwt_middleware_module.JWTService, "extract_bearer_token", lambda _header: "bad-token")

    def _decode_raises(_token):
        raise ValueError("Token inválido")

    monkeypatch.setattr(jwt_middleware_module.JWTService, "decode_token", _decode_raises)

    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(request, call_next)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido"


@pytest.mark.asyncio
async def test_dispatch_rejects_when_token_user_not_found(monkeypatch):
    middleware = JWTMiddleware(FastAPI(), logger=MagicMock())
    request = _make_request("/users", headers={"authorization": "Bearer token"})
    call_next = AsyncMock(return_value=PlainTextResponse("ok", status_code=200))

    monkeypatch.setattr(jwt_middleware_module.JWTService, "extract_bearer_token", lambda _header: "token")
    monkeypatch.setattr(
        jwt_middleware_module.JWTService,
        "decode_token",
        lambda _token: {"sub": "99", "username": "ghost", "role": "USER"},
    )

    fake_uow = AsyncMock()
    fake_uow.__aenter__ = AsyncMock(return_value=fake_uow)
    fake_uow.__aexit__ = AsyncMock(return_value=None)
    fake_uow.users = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    monkeypatch.setattr(jwt_middleware_module, "SqlAlchemyUnitOfWork", lambda: fake_uow)

    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(request, call_next)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


def test_is_public_route_for_known_public_paths():
    assert JWTMiddleware._is_public_route("/docs") is True
    assert JWTMiddleware._is_public_route("/uploads/productos/foto.jpg") is True


def test_is_public_route_for_api_prefixes_and_spa_routes():
    assert JWTMiddleware._is_public_route("/stock") is False
    assert JWTMiddleware._is_public_route("/stock/movements") is False
    assert JWTMiddleware._is_public_route("/mi-pagina-react") is True
