import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from datetime import date
from ..repositories.project_repository import ProjectRepository
import re

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

        employees = self.normalize_employees_with_projects(raw_rows)

        today = date.today()
        long_term_days = long_term_extension_months * 30
        result: List[Dict[str, Any]] = []

        for emp in employees:
            # ---- exclude trainees / directors ----
            designation = (emp.get("designation") or "").lower()
            if "director" in designation or "trainee" in designation:
                continue

            # ---- must have at least one project ----
            if not emp.get("projects"):
                continue

            # ---- total occupancy (employee-level) ----
            total_occupancy = emp.get("occupancy", 0)
            if total_occupancy > occupancy_threshold:
                continue

            # ---- effective end date across ALL projects ----
            effective_end = self._get_effective_end_date_from_employee(emp)
            if not effective_end:
                continue

            if (effective_end - today).days < long_term_days:
                continue

            # ---- experience (sorting only) ----
            emp["_total_exp_years"] = self._parse_total_exp_years(emp.get("total_exp"))
            result.append(emp)

        # ---- sorting ----
        result.sort(
            key=lambda e: (
                -e.get("_total_exp_years", 0),
                e.get("designation") or "",
            )
        )

        # ---- cleanup ----
        for emp in result:
            emp.pop("_total_exp_years", None)

        return {
            "status": "success",
            "occupancy_threshold": occupancy_threshold,
            "long_term_extension_months": long_term_extension_months,
            "data": result,
        }
