import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.config import settings

router = APIRouter(prefix="/api/events", tags=["events"])
logger = logging.getLogger(__name__)


async def event_generator():
    """SSE generator that subscribes to Redis property_events channel."""
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe("property_updates")

    try:
        yield "data: {\"type\": \"connected\"}\n\n"
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                yield f"data: {data}\n\n"
            else:
                # Send keepalive every 30s
                yield ": keepalive\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe("property_updates")
        await pubsub.aclose()
        await r.aclose()


@router.get("/stream")
async def event_stream():
    """SSE endpoint for real-time property update notifications."""
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
