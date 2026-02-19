import asyncio
import logging
import json
from .celery_app import celery_app
from ..services.embedding_cache_service import EmbeddingCacheService
from ..services.project_deadline_service import ProjectDeadlineService
from ..config.settings import settings
from ..services.hybrid_search_engine import HybridSearchEngine
import redis

logger = logging.getLogger(__name__)

@celery_app.task(
    name="rebuild_embedding_cache",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def rebuild_embedding_cache(self):
    """
    Heavy ML task – runs OUTSIDE FastAPI
    """
    try:
        logger.info("🚀 Celery: Starting post-upload cache rebuild")

        # Celery is sync → run async code properly
        asyncio.run(_async_cache_rebuild())

        logger.info("✅ Celery: Cache rebuild completed successfully")

    except Exception as e:
        logger.exception("❌ Celery: Cache rebuild failed")
        raise e
    
async def _async_cache_rebuild():
    embedding_service = EmbeddingCacheService()

    if not embedding_service.available:
        logger.warning("⚠️ Embedding service not available")
        return

    await embedding_service.invalidate_employee_cache()
    embedding_service.clear_query_cache()

    result = await embedding_service.rebuild_all_caches()

    if result.get("status") != "success":
        logger.warning(f"⚠️ Post-upload cache rebuild had issues: {result.get('message', 'Unknown error')}")
        raise RuntimeError(result.get("message", "Cache rebuild failed"))
    logger.info(f"✅ Post-upload unified cache rebuild completed: {result.get('employees_processed', 0)} employees")

@celery_app.task(
    name = "check_project_deadlines",
    bind = True,
    autoretry_for = (Exception,),
    retry_kwargs = {"max_retries": 3, "countdown": 30}
)
def check_project_deadlines(self):
    logger.info("Checking project deadlines...")
    asyncio.run(ProjectDeadlineService.process_project_deadlines())

@celery_app.task(
    name="save_ranked_search_cache",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 5},
)
def save_ranked_search_cache(self, cache_key: str, data: dict, ttl: int = 300):
    try:
        logger.info(f"💾 Celery: Saving ranked cache for key {cache_key}")
        hybrid_engine = HybridSearchEngine(gemini_api_key=settings.gemini_api_key)
        hybrid_engine.embedding_cache.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
        logger.info("✅ Celery: Ranked search cache saved")

    except Exception as e:
        logger.exception("❌ Celery: Failed to save ranked cache")
        raise e