import json
import redis.asyncio as redis
from app.config import get_settings


async def get_redis():
    """Get Redis connection using configured URL."""
    settings = get_settings()
    return await redis.from_url(settings.redis_url)


async def get_cached_ranking(dsp_id: str, date: str) -> list | None:
    key = f"ranking:{dsp_id}:{date}"
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def set_cached_ranking(dsp_id: str, date: str, data: list, ttl: int = 86400):
    key = f"ranking:{dsp_id}:{date}"
    val = json.dumps(data)
    r = await get_redis()
    await r.setex(key, ttl, val)


async def get_cached_brief(outlet_id: str, date: str) -> str | None:
    key = f"brief:{outlet_id}:{date}"
    r = await get_redis()
    data = await r.get(key)
    return data.decode('utf-8') if data else None


async def set_cached_brief(outlet_id: str, date: str, brief: str, ttl: int = 86400):
    key = f"brief:{outlet_id}:{date}"
    r = await get_redis()
    await r.setex(key, ttl, brief)


async def get_semantic_cache(query_hash: str) -> str | None:
    key = f"semantic:{query_hash}"
    r = await get_redis()
    data = await r.get(key)
    return data.decode('utf-8') if data else None


async def set_semantic_cache(query_hash: str, response: str, ttl: int = 43200):
    key = f"semantic:{query_hash}"
    r = await get_redis()
    await r.setex(key, ttl, response)
