from sqlalchemy import text
import logging
from ..core.database import get_db_session
logger = logging.getLogger(__name__)

class DashboardService:

    def __init__(self):
        pass

    async def get_project_distribution(self, top_n: int = 4):
        try:
            with get_db_session() as db:

                # 1️⃣ Total employees
                total_employees = db.execute(
                    text("SELECT COUNT(DISTINCT employee_id) FROM employees")
                ).scalar()

                # 2️⃣ Project-wise counts
                rows = db.execute(
                    text("""
                        SELECT
                            project_name,
                            COUNT(DISTINCT employee_id) AS employee_count
                        FROM employee_projects
                        GROUP BY project_name
                        ORDER BY employee_count DESC
                    """)
                ).mappings().all()

                top_projects = []
                top_sum = 0

                for row in rows[:top_n]:
                    count = row["employee_count"]
                    top_projects.append({
                        "project": row["project_name"],
                        "employee_count": count
                    })
                    top_sum += count

                top_projects.append({
                    "project": "Others",
                    "employee_count": max(total_employees - top_sum, 0)
                })

                return {
                    "status": "success",
                    "total_employees": total_employees,
                    "projects": top_projects
                }

        except Exception as e:
            logger.error("Failed to fetch project analytics distribution data")
            raise

    async def get_department_distribution(self):
        """
        Returns:
        - all departments
        - employee count per department (ascending order)
        """
        try:
            with get_db_session() as db:
                rows = db.execute(
                    text("""
                        SELECT
                            employee_department,
                            COUNT(DISTINCT employee_id) AS employee_count
                        FROM employees
                        WHERE employee_department IS NOT NULL
                        GROUP BY employee_department
                        ORDER BY employee_count DESC
                    """)
                ).mappings().all()

                departments = [{"department": row["employee_department"], "employee_count": row["employee_count"]} for row in rows]

                return {
                    "status": "success",
                    "departments": departments
                }

        except Exception as e:
            logger.error(f"Failed to fetch department analytics data: {str(e)}")
            raise

    async def get_dashboard_count_details(self):
        try:
            with get_db_session() as db:
                row = db.execute(
                    text("""
                        SELECT
                            (SELECT COUNT(*) FROM employees) AS total_employee_count,

                            (SELECT COUNT(DISTINCT project_name) FROM employee_projects) AS total_project_count,

                            (SELECT COUNT(DISTINCT employee_id) FROM employee_projects WHERE project_name ILIKE '%FREE') AS freepool_employee_count;
                    """)
                ).mappings().first()
            counts = {"freepool_count": row["freepool_employee_count"], "project_count": row["total_project_count"], "employee_count": row["total_employee_count"]}
            return counts
        except Exception as e:
            logger.error(f"Failed to fetch counts: {str(e)}")
            raise