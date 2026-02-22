import hashlib
import logging
from urllib.parse import urlparse

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.config import settings

router = APIRouter(prefix="/api/images", tags=["images"])
logger = logging.getLogger(__name__)

ALLOWED_HOSTS = {
    "d18-a.sdn.cz",        # sreality
    "d18-a.sdn.szn.cz",
    "img.bezrealitky.cz",
    "api.bezrealitky.cz",
    "sta-reality2.1gr.cz",  # idnes
}

# Cache TTL: 24 hours
CACHE_TTL = 86400


@router.get("/proxy")
async def proxy_image(url: str = Query(..., description="Image URL to proxy")):
    """Proxy and cache property images to avoid mixed content and CORS issues."""
    parsed = urlparse(url)
    if not parsed.scheme in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme")

    # Only allow known real estate image hosts
    host = parsed.hostname or ""
    if not any(host.endswith(allowed) for allowed in ALLOWED_HOSTS):
        raise HTTPException(status_code=403, detail="Host not allowed")

    cache_key = f"img:{hashlib.md5(url.encode()).hexdigest()}"

    # Try Redis cache first
    try:
        r = aioredis.from_url(settings.redis_url)
        cached = await r.get(cache_key)
        if cached:
            content_type = await r.get(f"{cache_key}:ct") or b"image/jpeg"
            await r.aclose()
            return Response(
                content=cached,
                media_type=content_type.decode() if isinstance(content_type, bytes) else content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
        await r.aclose()
    except Exception:
        pass

    # Fetch from origin
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {e}")

    content_type = resp.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL does not point to an image")

    body = resp.content

    # Cache in Redis (fire and forget, don't block response)
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.setex(cache_key, CACHE_TTL, body)
        await r.setex(f"{cache_key}:ct", CACHE_TTL, content_type)
        await r.aclose()
    except Exception:
        pass

    return Response(
        content=body,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
