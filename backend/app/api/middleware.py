"""HTTP middleware for request tracing, security headers, and size enforcement."""

import re
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.logging_config import request_id_ctx

# Strict regex pattern for safe, alphanumeric request IDs
SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Maximum permitted payload size in bytes (4 KB)
MAX_BODY_SIZE_BYTES = 4096


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates a safe request identifier across request lifecycle."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        header_req_id = request.headers.get("X-Request-ID")
        if header_req_id and SAFE_REQUEST_ID_REGEX.match(header_req_id):
            req_id = header_req_id
        else:
            req_id = uuid.uuid4().hex

        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces strict security response headers for API hardening."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces strict payload body size limits (4 KB) to protect against resource exhaustion."""

    def __init__(self, app: Any, max_body_size: int = MAX_BODY_SIZE_BYTES) -> None:
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check Content-Length header first if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large. Maximum allowed size is 4 KB."},
                    )
            except ValueError:
                pass

        # For requests with a body, buffer and enforce max size
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if len(body) > self.max_body_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Payload too large. Maximum allowed size is 4 KB."},
                )

        return await call_next(request)
