"""FastMCP middleware that logs every request and response at DEBUG level."""

import logging
import time
from typing import Any

import pydantic_core
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

logger = logging.getLogger("ludus_mcp.mcp_requests")

MAX_PAYLOAD_LENGTH = 2000


def _serialize(value: Any) -> str:
    payload = pydantic_core.to_json(value, fallback=str).decode()
    if len(payload) > MAX_PAYLOAD_LENGTH:
        return payload[:MAX_PAYLOAD_LENGTH] + "...(truncated)"
    return payload


class RequestResponseLoggingMiddleware(Middleware):
    """Logs the payload of every incoming MCP message and its outgoing result/error."""

    async def on_message(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        method = context.method or "unknown"
        logger.debug(f"--> {context.type} {method}: {_serialize(context.message)}")

        start = time.perf_counter()
        try:
            result = await call_next(context)
        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.debug(f"<-- {context.type} {method} error after {duration_ms}ms: {e}")
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.debug(f"<-- {context.type} {method} ({duration_ms}ms): {_serialize(result)}")
        return result
