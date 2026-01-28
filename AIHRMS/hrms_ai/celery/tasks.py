import asyncio
import logging
from .celery_app import celery_app
from ..services.embedding_cache_service import EmbeddingCacheService

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