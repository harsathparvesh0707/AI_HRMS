from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from ..config.settings import settings

celery_app = Celery(
    "AIHRMS.hrms_ai",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check-project-deadlines-daily": {
        "task": "check_project_deadlines",
        "schedule": crontab(hour=10, minute=0)
    }
}

# celery_app.conf.beat_schedule = {
#     "check-project-deadlines-daily": {
#         "task": "AIHRMS.hrms_ai.celery.tasks.check_project_deadlines",
#         "schedule": timedelta(minutes=1)
#     }
# }

celery_app.autodiscover_tasks(["AIHRMS.hrms_ai.celery"])