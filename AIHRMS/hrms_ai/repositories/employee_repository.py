"""
Employee Repository - Database operations for employees
"""
from typing import Dict, List, Any, Optional
from .base_repository import BaseRepository

class EmployeeRepository(BaseRepository):
    """Repository for employee-related database operations"""
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees"""
        query = "SELECT * FROM employees ORDER BY employee_id"
        return self.execute_query(query)
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        query = "SELECT * FROM employees WHERE employee_id = :employee_id"
        return self.execute_single(query, {"employee_id": employee_id})
    
    def create_employee(self, employee_data: Dict[str, Any]) -> bool:
        """Create new employee"""
        columns = list(employee_data.keys())
        values = [f":{col}" for col in columns]
        
        query = f"""
        INSERT INTO employees ({', '.join(columns)})
        VALUES ({', '.join(values)})
        """
        
        return self.execute_update(query, employee_data) > 0
    
    def update_employee(self, employee_id: str, update_data: Dict[str, Any]) -> bool:
        """Update employee data"""
        set_clauses = [f"{col} = :{col}" for col in update_data.keys()]
        update_data['employee_id'] = employee_id
        
        query = f"""
        UPDATE employees 
        SET {', '.join(set_clauses)}
        WHERE employee_id = :employee_id
        """
        
        return self.execute_update(query, update_data) > 0
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete employee"""
        query = "DELETE FROM employees WHERE employee_id = :employee_id"
        return self.execute_update(query, {"employee_id": employee_id}) > 0
    
    def search_employees_by_skills(self, skills: List[str]) -> List[Dict[str, Any]]:
        """Search employees by skills"""
        skill_conditions = " OR ".join([f"LOWER(skill_set) LIKE LOWER(:skill_{i})" for i in range(len(skills))])
        params = {f"skill_{i}": f"%{skill}%" for i, skill in enumerate(skills)}
        
        query = f"""
        SELECT * FROM employees 
        WHERE {skill_conditions}
        ORDER BY employee_id
        """
        
        return self.execute_query(query, params)
    
    def get_employees_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get employees by department"""
        query = """
        SELECT * FROM employees 
        WHERE LOWER(employee_department) = LOWER(:department)
        ORDER BY employee_id
        """
        return self.execute_query(query, {"department": department})
    
    def get_employees_by_tech_group(self, tech_group: str) -> List[Dict[str, Any]]:
        """Get employees by tech group"""
        query = """
        SELECT * FROM employees 
        WHERE LOWER(tech_group) = LOWER(:tech_group)
        ORDER BY employee_id
        """
        return self.execute_query(query, {"tech_group": tech_group})
    
    def clear_all_employees(self) -> int:
        """Clear all employees"""
        query = "DELETE FROM employees"
        return self.execute_update(query)
    
    def bulk_insert_employees(self, employees_data: List[Dict[str, Any]]) -> int:
        """Bulk insert employees"""
        if not employees_data:
            return 0
        
        columns = list(employees_data[0].keys())
        values = [f":{col}" for col in columns]
        
        query = f"""
        INSERT INTO employees ({', '.join(columns)})
        VALUES ({', '.join(values)})
        """
        
        return self.execute_batch(query, employees_data)
    


    def get_all_tech_groups(self) -> List[str]:
        """Fetch all distinct tech groups from employees table."""
        query = "SELECT DISTINCT tech_group FROM employees WHERE tech_group IS NOT NULL AND tech_group <> ''"
        results = self.execute_query(query)
        return [row["tech_group"] for row in results if row.get("tech_group")]
    def get_all_skills(self) -> List[str]:
        """Fetch all distinct skills from employees skill_set."""
        query = "SELECT DISTINCT skill_set FROM employees WHERE skill_set IS NOT NULL AND skill_set <> ''"
        results = self.execute_query(query)
        
        all_skills = set()
        for row in results:
            skills_text = row.get("skill_set", "") or ""
            # Split by comma first, then clean each skill
            skill_tokens = [s.strip().lower() for s in skills_text.split(',') if s.strip() and len(s.strip()) > 2]
            all_skills.update(skill_tokens)
        
        return list(all_skills)