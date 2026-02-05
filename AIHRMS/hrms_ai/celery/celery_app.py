from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

celery_app = Celery(
    "hrms_ai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# celery_app.conf.beat_schedule = {
#     "check-project-deadlines-daily": {
#         "task": "check_project_deadlines",
#         "schedule": crontab(hour=10, minute=0)
#     }
# }

celery_app.conf.beat_schedule = {
    "check-project-deadlines-daily": {
        "task": "check_project_deadlines",
        "schedule": timedelta(minutes=1)
    }
}

celery_app.autodiscover_tasks(["hrms_ai.celery"])