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

    async def get_employees_directory(self):
        try:
            with get_db_session() as db:
                row = db.execute(
                    text("""
                        SELECT employee_id, display_name, employee_department, designation, tech_group, emp_location FROM employees;
                    """)
                ).mappings().all()
            employees = list(row)
            return {
                "status": "success",
                "employees": employees
            }
        except Exception as e:
            logger.error(f"Failed to fetch data: {str(e)}")
            raise

    async def get_employees_deployment_wise(self, deployment, page_number, page_size):
        try:
            offset = (page_number - 1) * page_size
            deployment_map = {
                "freepool": ["Free"],
                "internal": [
                    "Internal Budgeted",
                    "RandD Internal Budgeted",
                    "R and D Shadow"
                ],
                "budgetted": ["Budgeted"],
                "billable": ["Billable"],
                "client_backup": ["Client Backup"],
                "shadow": ["Shadow"]
            }
            db_values = deployment_map.get(deployment.value)
            with get_db_session() as db:
                emp = db.execute(
                    text(
                        """
                        SELECT 
                            e.*,

                            COALESCE(
                                json_agg(DISTINCT to_jsonb(ep))
                                FILTER (WHERE ep.employee_id IS NOT NULL),
                                '[]'::json
                            ) AS projects,

                            COUNT(*) OVER() AS total_count

                        FROM employees e

                        LEFT JOIN employee_projects ep 
                            ON e.employee_id = ep.employee_id

                        WHERE EXISTS (
                            SELECT 1 
                            FROM employee_projects ep2
                            WHERE ep2.employee_id = e.employee_id
                            AND ep2.deployment = ANY(:deployments)
                        )

                        GROUP BY e.employee_id

                        ORDER BY split_part(e.employee_id, '/', 2)::int
                        LIMIT :limit OFFSET :offset;
                        """), 
                        {
                            "deployments": db_values,
                            "limit": page_size,
                            "offset": offset
                        }
                    ).mappings().all()
                
            employees = [dict(row) for row in emp]
            total = employees[0]["total_count"] if employees else 0
            for emp in employees:
                emp.pop("total_count", None)

            return {
                "status": 200,
                "total_count": total, 
                "employees": employees,
            }
        except Exception as e:
            logger.error(f"Failed to fetch data from DB: {str(e)}")
            raise