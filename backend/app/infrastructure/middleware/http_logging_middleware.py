import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.logging import get_logger


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware que loguea request y response usando structlog."""

    def __init__(self, app, logger=None, log_response_body: bool = True, max_body_size: int = 50_000):
        super().__init__(app)
        self.logger = logger or get_logger("http.external")
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generar correlation ID único por request
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # --- LOGUEAR REQUEST ---
        body_bytes = await request.body()
        headers_str = "\n".join([f"  {k}: {v}" for k, v in request.headers.items()])
        content_type = request.headers.get("content-type", "")

        request_log = f"Request recibido: {request.method} {request.url} \nHEADERS:\n{headers_str}"
        
        # Solo intentar decodificar si es texto (JSON, form-urlencoded, etc.)
        if body_bytes:
            if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
                request_log += f"\nBODY: <binary data, {len(body_bytes)} bytes>"
            else:
                try:
                    body_str = body_bytes.decode("utf-8")
                    request_log += f"\nBODY:\n{body_str}"
                except UnicodeDecodeError:
                    request_log += f"\nBODY: <binary data, {len(body_bytes)} bytes>"

        self.logger.debug(
            event=request_log,
            request_id=correlation_id,
        )

        # --- PROCESAR REQUEST ---
        response: Response = await call_next(request)

        # Capturar el body del response
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk
        
        # Crear un async generator para reconstruir el iterator
        async def body_generator():
            yield resp_body
        
        response.body_iterator = body_generator()

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # --- LOGUEAR RESPONSE ---
        response_headers = "\n".join([f"  {k}: {v}" for k, v in response.headers.items()])
        response_content_type = response.headers.get("content-type", "")
        
        response_log = f"Response enviado: status_code={response.status_code} duration_ms={duration_ms}ms\nHEADERS:\n{response_headers}"
        
        if self.log_response_body and resp_body:
            if any(t in response_content_type for t in ["image/", "application/octet-stream", "application/pdf"]):
                response_log += f"\nBODY: <binary data, {len(resp_body)} bytes>"
            else:
                try:
                    response_body = resp_body.decode("utf-8")
                    if len(response_body) > self.max_body_size:
                        response_log += f"\nBODY (truncado {len(response_body)} caracteres):\n{response_body[:self.max_body_size]}..."
                    else:
                        response_log += f"\nBODY:\n{response_body}"
                except UnicodeDecodeError:
                    response_log += f"\nBODY: <binary data, {len(resp_body)} bytes>"
        
        self.logger.debug(
            event=response_log,
            request_id=correlation_id,
        )

        return response
