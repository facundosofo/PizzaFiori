import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.infrastructure.logging import get_logger, sanitize_headers

BINARY_CONTENT_TYPES = ("image/", "application/octet-stream", "application/pdf", "multipart/form-data")


def _is_binary(content_type: str) -> bool:
    return any(t in content_type for t in BINARY_CONTENT_TYPES)


def _decode_body(raw: bytes, content_type: str, max_size: int) -> str | None:
    """Decodifica el body a string. Retorna None si es binario o vacío."""
    if not raw:
        return None
    if _is_binary(content_type):
        return f"<binary {len(raw)} bytes>"
    try:
        decoded = raw.decode("utf-8")
        if len(decoded) > max_size:
            return decoded[:max_size] + f"... <truncated, total {len(decoded)} chars>"
        return decoded
    except UnicodeDecodeError:
        return f"<binary {len(raw)} bytes>"


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware que loguea request y response como eventos JSON estructurados."""

    def __init__(
        self,
        app,
        logger=None,
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_size: int = 50_000,
    ):
        super().__init__(app)
        self.logger = logger or get_logger("http.external")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Bindear el correlation_id al contexto de la corrutina.
        # Todos los logs emitidos durante este request (servicios, repos, etc.)
        # van a incluir request_id automáticamente via merge_contextvars.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=correlation_id)

        await self._log_request(request, correlation_id)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response = await self._log_response(response, correlation_id, duration_ms)
        return response

    async def _log_request(self, request: Request, correlation_id: str) -> None:
        body_bytes = await request.body()
        content_type = request.headers.get("content-type", "")

        log_data = {
            "event": "http.request",
            "request_id": correlation_id,
            "http": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query": str(request.url.query) or None,
                "headers": sanitize_headers(dict(request.headers)),
            },
        }

        if self.log_request_body:
            log_data["http"]["body"] = _decode_body(body_bytes, content_type, self.max_body_size)

        self.logger.debug(**log_data)

    async def _log_response(self, response: Response, correlation_id: str, duration_ms: float) -> Response:
        content_type = response.headers.get("content-type", "")

        log_data = {
            "event": "http.response",
            "request_id": correlation_id,
            "http": {
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "headers": sanitize_headers(dict(response.headers)),
            },
        }

        if self.log_response_body:
            if isinstance(response, StreamingResponse):
                log_data["http"]["body"] = "<streaming>"
            else:
                resp_body = getattr(response, "body", None)
                if resp_body:
                    log_data["http"]["body"] = _decode_body(resp_body, content_type, self.max_body_size)

        log_fn = self.logger.warning if response.status_code >= 400 else self.logger.debug
        log_fn(**log_data)

        return response