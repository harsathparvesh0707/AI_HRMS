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
                    text("SELECT COUNT(*) FROM employees")
                ).scalar()

                # 2️⃣ Project-wise counts
                rows = db.execute(
                    text("""
                        SELECT
                            p.project_name,
                            COUNT(DISTINCT ep.employee_id) AS employee_count
                        FROM projects p
                        LEFT JOIN employee_projects ep
                            ON p.project_name = ep.project_name
                        GROUP BY p.project_name
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
                            e.employee_department,
                            COUNT(*) AS employee_count
                        FROM employees e
                        WHERE e.employee_department IS NOT NULL
                         AND TRIM(e.employee_department) <> ''
                        GROUP BY e.employee_department
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

                            (SELECT COUNT(DISTINCT employee_id) FROM employee_projects WHERE LOWER(deployment) LIKE '%free%') AS freepool_employee_count;
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
                                json_agg(
                                    DISTINCT jsonb_build_object(
                                        'project_name', p.project_name,
                                        'customer', p.customer,
                                        'project_department', p.project_department,
                                        'project_industry', p.project_industry,
                                        'project_status', p.project_status,
                                        'project_category', p.project_category,
                                        'pm', p.pm,
                                        'role', ep.role,
                                        'deployment', ep.deployment,
                                        'occupancy', ep.occupancy,
                                        'project_joined_date', ep.project_joined_date,
                                        'project_extended_end_date', p.project_extended_end_date,
                                        'project_committed_end_date', p.project_committed_end_date
                                    )
                                ) FILTER (WHERE ep.employee_id IS NOT NULL),
                                '[]'::json
                            ) AS projects,

                            COUNT(*) OVER() AS total_count

                        FROM employees e

                        LEFT JOIN employee_projects ep 
                            ON e.employee_id = ep.employee_id

                        LEFT JOIN projects p 
                            ON ep.project_name = p.project_name

                        WHERE EXISTS (
                            SELECT 1 
                            FROM employee_projects ep2
                            WHERE ep2.employee_id = e.employee_id
                            AND ep2.deployment = ANY(:deployments)
                        )

                        GROUP BY e.employee_id

                        ORDER BY split_part(e.employee_id, '/', 2)::int
                        LIMIT :limit OFFSET :offset;"""), 
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

    async def _get_all_projects(self):
        try:
            with get_db_session() as session:
                rows = session.execute(text("SELECT * FROM projects ORDER BY project_name")).mappings().all()
            response = [dict(row) for row in rows]
            return {'status': 200, 'response': response}
        except Exception as e:
            logger.error(f"Error while fetching data from Projects: {str(e)}")
            raise

    async def get_employees_deployment_wise_counts(self):
        with get_db_session() as session:
            try:

                query = """
                WITH ranked_resources AS (
                    SELECT
                        employee_id,
                        deployment,
                        occupancy,
                        ROW_NUMBER() OVER (
                            PARTITION BY employee_id
                            ORDER BY
                                occupancy DESC,
                                CASE deployment
                                    WHEN 'Billable' THEN 1
                                    WHEN 'Budgeted' THEN 2
                                    WHEN 'Internal Budgeted' THEN 3
                                    WHEN 'RandD Internal Budgeted' THEN 4
                                    WHEN 'Client Backup' THEN 5
                                    WHEN 'MFG Support Backup' THEN 6
                                    WHEN 'Billable Backup' THEN 7
                                    WHEN 'Shadow' THEN 8
                                    WHEN 'R and D Shadow' THEN 9
                                    WHEN 'Free' THEN 10
                                    WHEN 'Trainee' THEN 11
                                    WHEN 'Planned' THEN 12
                                    WHEN 'Long Leave' THEN 13
                                    WHEN 'BU Common' THEN 14
                                    ELSE 999
                                END
                        ) AS rn
                    FROM employee_projects
                )
                SELECT
                    deployment,
                    COUNT(*) AS total_resources
                FROM ranked_resources
                WHERE rn = 1
                GROUP BY deployment
                ORDER BY total_resources DESC;
                """
                result = session.execute(text(query)).mappings().all()
                return {
                    "status": 200,
                    "data": [dict(row) for row in result]
                }

            except Exception as e:
                logger.error(f"Error fetching employees deployment wise counts: {e}")
                raise

    async def get_all_deployments(self):
        with get_db_session() as session:
            try:
                result = session.execute(text("SELECT DISTINCT deployment FROM employee_projects WHERE deployment IS NOT NULL AND TRIM(deployment) <> ''ORDER BY deployment")).mappings().all()
                return {"status": 200, "data": result}
            except Exception as e:
                logger.error(f"Error fetching deployments")
                raise

    async def get_all_techgroups(self):
        with get_db_session() as session:
            try:
                result = session.execute(text("SELECT DISTINCT tech_group FROM employees WHERE tech_group IS NOT NULL ORDER BY tech_group")).mappings().all()
                return {"status": 200, "data": result}
            except Exception as e:
                logger.error(f"Error fetching tech groups")
                raise

    async def get_deployment_resources(self, deployment, tech_group):
        with get_db_session() as session:
            try:
                query = """
                WITH ranked_resources AS (
                    SELECT
                        ep.employee_id,
                        ep.project_name,
                        ep.deployment,
                        ep.occupancy,
                        ep.project_joined_date,
                        ROW_NUMBER() OVER (
                            PARTITION BY ep.employee_id
                            ORDER BY
                                ep.occupancy DESC,
                                CASE ep.deployment
                                    WHEN 'Billable' THEN 1
                                    WHEN 'Budgeted' THEN 2
                                    WHEN 'Internal Budgeted' THEN 3
                                    WHEN 'RandD Internal Budgeted' THEN 4
                                    WHEN 'Client Backup' THEN 5
                                    WHEN 'MFG Support Backup' THEN 6
                                    WHEN 'Billable Backup' THEN 7
                                    WHEN 'Shadow' THEN 8
                                    WHEN 'R and D Shadow' THEN 9
                                    WHEN 'Free' THEN 10
                                    WHEN 'Trainee' THEN 11
                                    WHEN 'Planned' THEN 12
                                    WHEN 'Long Leave' THEN 13
                                    WHEN 'BU Common' THEN 14
                                    ELSE 999
                                END
                        ) AS rn
                    FROM employee_projects ep
                )
                SELECT
                    e.employee_id,
                    e.display_name,
                    e.designation,
                    e.employee_department,
                    e.tech_group,
                    e.total_exp,
                    e.emp_location,
                    rr.project_name,
                    rr.deployment,
                    rr.occupancy,
                    rr.project_joined_date,
                    CURRENT_DATE - rr.project_joined_date AS aging_days
                FROM ranked_resources rr
                JOIN employees e
                    ON e.employee_id = rr.employee_id
                WHERE rr.rn = 1
                """
                params = {}
                # Apply tech group filter only if not All
                if deployment.strip().lower() != "all":
                    query += """
                    AND LOWER(TRIM(rr.deployment)) = LOWER(TRIM(:deployment))
                    """
                    params["deployment"] = deployment
                if tech_group.strip().lower() != "all":
                    query += """
                    AND LOWER(TRIM(e.tech_group)) = LOWER(TRIM(:tech_group))
                    """
                    params["tech_group"] = tech_group

                query += """
                ORDER BY
                    CAST(
                        REGEXP_REPLACE(e.total_exp, '[^0-9.]', '', 'g')
                        AS FLOAT
                    ) DESC
                """

                result = session.execute(
                    text(query),
                    params
                ).mappings().all()

                return {
                    "status": 200,
                    "count": len(result),
                    "data": [dict(row) for row in result]
                }

            except Exception as e:
                logger.error(f"Error fetching deployment resources: {e}")
                raise
