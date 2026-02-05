import json
import redis.asyncio as aioredis
import redis
from typing import Callable, Awaitable
from ..config.settings import settings


class RedisMessageBroker:
    """
    Redis-based message broker supporting:
    - Sync publish (Celery)
    - Async subscribe (FastAPI)
    """

    def __init__(
        self,
        host: str = settings.redis_host,
        port: int = settings.redis_port,
        db: int = 0,
        channel: str = "ws_notifications",
    ):
        self.channel = channel

        # Sync client → Celery
        self.sync_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

        # Async client → FastAPI
        self.async_client = aioredis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

    # ----------------------------
    # PUBLISH (Celery-safe)
    # ----------------------------
    def publish(self, message: dict):
        """
        Publish message to Redis (sync).
        Used inside Celery workers.
        """
        self.sync_client.publish(self.channel, json.dumps(message))

    # ----------------------------
    # SUBSCRIBE (FastAPI-safe)
    # ----------------------------
    async def subscribe(
        self,
        handler: Callable[[dict], Awaitable[None]],
    ):
        """
        Subscribe to Redis channel and handle messages asynchronously.
        Used inside FastAPI startup.
        """
        pubsub = self.async_client.pubsub()
        await pubsub.subscribe(self.channel)

        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue

            data = json.loads(msg["data"])
            await handler(data)

    async def close(self):
        await self.async_client.close()
