import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import re
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.project_repository import ProjectRepository
from datetime import datetime
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class AvailableEmployeesService:
    """Service to find available employees based on project end dates and deployment status"""
    
    def __init__(self):
        self.project_repo = ProjectRepository()

    def _parse_total_exp(self, value) -> float:
        """
        Converts total_exp to numeric years.
        Accepts: '5Y 3M', '5.25', 5, None
        """
        try:
            if value is None or value == "" or pd.isna(value):
                return 0.0
            
            # If it's already a number, return it as float
            if isinstance(value, (int, float)):
                return float(value)
            
            # Convert to string for parsing
            value_str = str(value).strip()
            
            # Try direct float conversion first
            try:
                return float(value_str)
            except ValueError:
                pass
            
            years = months = 0

            match_y = re.search(r"(\d+)\s*Y", value_str, re.IGNORECASE)
            match_m = re.search(r"(\d+)\s*M", value_str, re.IGNORECASE)

            if match_y:
                years = int(match_y.group(1))
            if match_m:
                months = int(match_m.group(1))

            return round(years + months / 12, 2)
        
        except (TypeError, ValueError, AttributeError) as e:
            logger.warning(f"Could not parse experience '{value}': {e}")
            return 0.0
        
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

    

    def find_available_employees(self, months_threshold: int):
        raw_rows = self.project_repo.get_employees_with_projects()

        if not raw_rows:
            return {
                "status": "success",
                "months_threshold": months_threshold,
                "data": []
            }
        employees_data = self.normalize_employees_with_projects(raw_rows)

        return self._process_available_employees(
            employees_data,
            months_threshold
        )
    

    def _parse_total_exp(self, total_exp: str) -> float:
        """
        Converts '5Y 2M' → 5.17
        Used ONLY for internal sorting.
        """
        if not total_exp:
            return 0.0

        years = months = 0
        match_y = re.search(r"(\d+)\s*Y", total_exp)
        match_m = re.search(r"(\d+)\s*M", total_exp)

        if match_y:
            years = int(match_y.group(1))
        if match_m:
            months = int(match_m.group(1))

        return round(years + months / 12, 2)

    
    def _process_available_employees(self, employees, months_threshold: int, sort_by_columns: List[str] = ['deployment', 'total_exp', 'designation'], ascending_order: bool = True):

        today = datetime.utcnow().date()
        days_threshold = months_threshold * 30

        def is_trainee(emp: Dict[str, Any]) -> bool:
            return (
                "trainee" in (emp.get("designation") or "").lower()
                or "trainee" in (emp.get("deployment") or "").lower()
            )

        def parse_date(value):
            if not value:
                return None
            if isinstance(value, datetime):
                return value.date()
            try:
                return datetime.fromisoformat(str(value)).date()
            except Exception:
                return None

        def max_days_to_end(emp: Dict[str, Any]) -> int | None:
            dates = [
                parse_date(emp.get("committed_relieving_date")),
                parse_date(emp.get("extended_relieving_date")),
                parse_date(emp.get("project_committed_end_date")),
                parse_date(emp.get("project_extended_end_date")),
            ]
            valid_dates = [d for d in dates if d]
            if not valid_dates:
                return None
            return max((d - today).days for d in valid_dates)

        # --------------------------------------------------
        # 1. Filter available employees
        # --------------------------------------------------
        available = []

        for emp in employees:
            if is_trainee(emp):
                continue

            deployment = (emp.get("deployment") or "").strip()
            days_to_end = max_days_to_end(emp)

            deployment = (emp.get("deployment") or "").strip().lower()
            days_to_end = max_days_to_end(emp)

            is_free = deployment == "free"
            ending_soon = (
                days_to_end is not None and days_to_end <= days_threshold
            )

            if is_free or ending_soon:
                available.append(emp)
        # --------------------------------------------------
        # 2. Deduplicate by employee_id
        # --------------------------------------------------
        unique_by_id = {}
        for emp in available:
            emp_id = emp.get("employee_id")
            if emp_id and emp_id not in unique_by_id:
                unique_by_id[emp_id] = emp

        unique_employees = list(unique_by_id.values())

        # --------------------------------------------------
        # 3. Split Free vs Others
        # --------------------------------------------------
        free_staff = []
        other_staff = []

        for emp in unique_employees:
            if (emp.get("deployment") or "").strip() == "free":
                free_staff.append(emp)
            else:
                other_staff.append(emp)

        # --------------------------------------------------
        # 4. Sorting
        # --------------------------------------------------
        free_staff.sort(
            key=lambda e: (
                -self._parse_total_exp(e.get("total_exp")),
                e.get("designation") or "",
            )
        )

        def sort_key(emp):
            key = []
            for col in sort_by_columns:
                value = emp.get(col)
                if value is None:
                    value = ""
                elif isinstance(value, str):
                    value = value.lower()
                key.append(value if ascending_order else _Reverse(value))
            return tuple(key)

        class _Reverse:
            def __init__(self, value):
                self.value = value
            def __lt__(self, other):
                return self.value > other.value

        other_staff.sort(key=sort_key)

        # --------------------------------------------------
        # 5. Final result
        # --------------------------------------------------
        available_employees = free_staff + other_staff
        return {
            "status":"success",
            "month_threshold":months_threshold,
            "data":available_employees
        }