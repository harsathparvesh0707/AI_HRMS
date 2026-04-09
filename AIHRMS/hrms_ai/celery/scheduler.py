from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def run_project_suggestion():
    from ..services.project_requirements_service import ProjectRequirementSuggestion

    try:
        logger.info("🚀 Running scheduled project suggestion task")

        service = ProjectRequirementSuggestion()
        await service.process_requirement_suggestion()

        logger.info("✅ Task completed successfully")

    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")


async def run_freepool_suggestion():
    from ..services.freepool_suggestion_service import FreepoolProjectSuggestionService

    try:
        logger.info("🚀 Running scheduled freepool employee suggestion task")

        service = FreepoolProjectSuggestionService()
        await service.get_suggestions()
        logger.info("✅ Freepool task completed successfully")
    except Exception as e:
        logger.error(f"❌ Task Failed {str(e)}")


def job_wrapper():
    """Sync wrapper for async function"""
    try:
        asyncio.run(run_project_suggestion())
        asyncio.run(run_freepool_suggestion())
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")


def start_scheduler():
    scheduler.add_job(
        job_wrapper,
        # IntervalTrigger(minutes=5),  # ⏰ Daily 9 AM
        CronTrigger(hour=0, minute=0),
        id="project_suggestion_job",
        replace_existing=True
    )

    scheduler.start()
    logger.info("📅 Scheduler started")