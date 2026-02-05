from datetime import date, datetime
from ..core.database import get_db_session
from ..services.redis_broker import RedisMessageBroker
from sqlalchemy import text

class ProjectDeadlineService:

    @staticmethod
    async def process_project_deadlines():
        today = date.today()

        projects = ProjectDeadlineService._fetch_project_effective_end_dates()

        for project in projects:
            project_name = project["project_name"]
            end_date = project["project_committed_end_date"]

            if not end_date:
                continue

            days_left = (end_date - today).days

            if 0 < days_left <= 30:
                message = f"Project '{project_name}' will end in {days_left} days"

            elif days_left < 0:
                message = f"Project '{project_name}' has passed the end date"

            else:
                continue

            redis = RedisMessageBroker()

            redis.publish(message={
                "type": "PROJECT_DEADLINE",
                "project": project_name,
                "message": message,
                "datetime": datetime.now().isoformat()
            })

    def _fetch_project_effective_end_dates():
        with get_db_session() as db:
            rows = db.execute(
                text("""
                    SELECT
                        project_name,
                        COALESCE(project_extended_end_date, project_committed_end_date) AS effective_end_date
                    FROM employee_projects
                """)
            ).fetchall()

        return [
            {
                "project_name": row.project_name,
                "end_date": row.effective_end_date
            }
            for row in rows
        ]
