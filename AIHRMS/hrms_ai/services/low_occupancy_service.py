import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from datetime import date
from ..repositories.project_repository import ProjectRepository
import re
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class LowOccupancyService:
    """Service to find employees with low occupancy and long-term project status"""
    
    def __init__(self):
        self.project_repo = ProjectRepository()


    def _parse_total_exp_years(self, exp: str | None) -> float:
        if not exp:
            return 0.0

        years = months = 0

        y = re.search(r"(\d+)\s*Y", exp, re.I)
        m = re.search(r"(\d+)\s*M", exp, re.I)

        if y:
            years = int(y.group(1))
        if m:
            months = int(m.group(1))

        return round(years + months / 12, 2)
    


    def _safe_to_date(self, value) -> Optional[date]:
        if not value:
            return None

        # datetime / pandas Timestamp
        if isinstance(value, datetime):
            return value.date()

        # already a date
        if isinstance(value, date):
            return value

        # ISO string
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "")).date()
            except ValueError:
                return None

        return None


    def _get_effective_end_date(self, emp: dict) -> Optional[date]:
        dates = [
            emp.get("project_extended_end_date"),
            emp.get("extended_relieving_date"),
            emp.get("project_committed_end_date"),
            emp.get("committed_relieving_date"),
        ]

        parsed_dates = [
            self._safe_to_date(d)
            for d in dates
            if self._safe_to_date(d)
        ]

        return max(parsed_dates) if parsed_dates else None
    
    def normalize_employees_with_projects(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        employees_map: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            emp_id = row["employee_id"]

            # ---- initialize employee only once ----
            if emp_id not in employees_map:
                employees_map[emp_id] = {
                    "employee_id": emp_id,
                    "display_name": row.get("display_name", ""),
                    "employee_department": row.get("employee_department", ""),
                    "role": "",
                    "deployment": "",
                    "occupancy": 0,
                    "total_project_occupancy": 0,
                    "available_capacity": 100,
                    "joined_date": row.get("joined_date"),
                    "total_exp": row.get("total_exp", ""),
                    "vvdn_exp": row.get("vvdn_exp", ""),
                    "designation": row.get("designation", ""),
                    "tech_group": row.get("tech_group", ""),
                    "emp_location": row.get("emp_location", ""),
                    "skill_set": row.get("skill_set", ""),
                    "rm_id": row.get("rm_id", ""),
                    "rm_name": row.get("rm_name", ""),
                    "committed_relieving_date": row.get("committed_relieving_date"),
                    "extended_relieving_date": row.get("extended_relieving_date"),
                    "projects": []
                }

            emp = employees_map[emp_id]

            # ---- add project if exists ----
            if row.get("project_name"):
                project = {
                    "project_name": row.get("project_name"),
                    "customer": row.get("customer"),
                    "project_department": row.get("project_department"),
                    "project_industry": row.get("project_industry"),
                    "project_status": row.get("project_status"),
                    "occupancy": row.get("occupancy") or 0,
                    "role": row.get("role"),
                    "deployment": row.get("deployment"),
                    "start_date": row.get("start_date"),
                    "end_date": row.get("end_date"),
                    "project_joined_date": row.get("project_joined_date"),
                    "project_extended_end_date": row.get("project_extended_end_date"),
                    "project_committed_end_date": row.get("project_committed_end_date"),
                }

                emp["projects"].append(project)
                emp["total_project_occupancy"] += project["occupancy"]

        # ---- finalize derived fields ----
        for emp in employees_map.values():
            emp["available_capacity"] = max(0, 100 - emp["total_project_occupancy"])

            # derive deployment from latest project if exists
            if emp["projects"]:
                emp["deployment"] = emp["projects"][-1].get("deployment", "").lower()
            else:
                emp["deployment"] = "free"

        return list(employees_map.values())
    
    
    def _get_effective_end_date_from_employee(self, emp: dict) -> Optional[date]:
        dates = []

        # employee-level dates
        dates.extend([
            self._safe_to_date(emp.get("committed_relieving_date")),
            self._safe_to_date(emp.get("extended_relieving_date")),
        ])

        # project-level dates (ALL projects)
        for project in emp.get("projects", []):
            dates.extend([
                self._safe_to_date(project.get("project_extended_end_date")),
                self._safe_to_date(project.get("project_committed_end_date")),
            ])

        valid_dates = [d for d in dates if d]
        return max(valid_dates) if valid_dates else None



    def find_long_term_low_occupancy_employees(self, occupancy_threshold: int, long_term_extension_months: int):
        raw_rows = self.project_repo.get_employees_with_projects()
        if not raw_rows:
            return {
                "status": "success",
                "occupancy_threshold": occupancy_threshold,
                "long_term_extension_months": long_term_extension_months,
                "data": [],
            }

        # Groups flat SQL rows into { emp_id: { ..., projects: [...] } }
        employees = self.normalize_employees_with_projects(raw_rows)
        
        today = date.today()
        result: List[Dict[str, Any]] = []

        for emp in employees:
            # 1. Basic Exclusions (Exclude Senior Management and Trainees)
            designation = (emp.get("designation") or "").lower()
            if any(keyword in designation for keyword in ["director", "trainee", "manager"]):
                continue

            projects = emp.get("projects", [])
            if not projects:
                continue

            # Tracking flags for this specific employee
            # We start with None and only assign a rank if they meet the project-specific criteria
            assigned_rank = None 
            
            # We need to know if they have a 'FREE' project at all for Scenario 1
            has_free_pool_anywhere = any(
                "FREE" in str(p.get("project_name") or p.get("project") or "").upper() 
                for p in projects
            )

            # 2. Project-Level Validation
            # We check each project to see if THAT SPECIFIC project is low occupancy AND long tenure
            for proj in projects:
                pj_date = proj.get("project_joined_date")
                if not pj_date:
                    continue
                # Calculate tenure for THIS specific project
                diff = relativedelta(today, pj_date)
                months_passed = (diff.years * 12) + diff.months
                
                proj_occupancy = proj.get("occupancy", 0)
                deployment = str(proj.get("deployment", "")).strip()

                # CRITERIA: This specific project must be low occupancy AND older than the threshold months
                if proj_occupancy <= occupancy_threshold and months_passed >= long_term_extension_months:
                    
                    # Scenario 1 (Highest Priority):
                    # Qualifying project found AND the employee has another project marked as FREE
                    if has_free_pool_anywhere:
                        assigned_rank = 0
                        break # Rank 0 is the highest possible, we can stop checking projects
                    
                    # Scenario 2 (Second Priority):
                    # Qualifying project found AND its deployment is internal/budgeted/shadow
                    elif deployment.lower() in ["randd internal budgeted", "shadow"]:
                        # We assign Rank 1 but keep looking in case another project gives them Rank 0
                        assigned_rank = 1

            # 3. FILTERING: Only add to result if they were assigned Rank 0 or Rank 1
            if assigned_rank is not None:
                emp["_rank_score"] = assigned_rank
                emp["_total_exp_years"] = self._parse_total_exp_years(emp.get("total_exp"))
                result.append(emp)

        # 4. SORTING: Priority Rank (0 then 1), then Experience (Descending)
        result.sort(
            key=lambda e: (
                e.get("_rank_score"), 
                -e.get("_total_exp_years", 0)
            )
        )

        # Cleanup internal keys
        for emp in result:
            emp.pop("_rank_score", None)
            emp.pop("_total_exp_years", None)

        return {
            "status": "success",
            "occupancy_threshold": occupancy_threshold,
            "long_term_extension_months": long_term_extension_months,
            "data": result,
        }
