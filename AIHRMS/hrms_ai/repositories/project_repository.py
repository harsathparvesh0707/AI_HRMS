"""
Project Repository - Database operations for employee projects
"""
from typing import Dict, List, Any, Optional
from .base_repository import BaseRepository

class ProjectRepository(BaseRepository):
    """Repository for project-related database operations"""
    
    def get_projects_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get all projects for an employee"""
        query = """
        SELECT * FROM employee_projects 
        WHERE employee_id = :employee_id 
        ORDER BY created_at DESC
        """
        return self.execute_query(query, {"employee_id": employee_id})
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        query = "SELECT * FROM employee_projects WHERE id = :project_id"
        return self.execute_single(query, {"project_id": project_id})
    
    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create new project"""
        query = """
        INSERT INTO employee_projects (
            employee_id, project_name, customer, project_department,
            project_industry, project_status, occupancy,
            start_date, end_date, role, deployment, project_extended_end_date, project_committed_end_date
        ) VALUES (
            :employee_id, :project_name, :customer, :project_department,
            :project_industry, :project_status, :occupancy,
            :start_date, :end_date, :role, :deployment, :project_extended_end_date, :project_committed_end_date
        )
        """
        return self.execute_update(query, project_data) > 0
    
    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> bool:
        """Update project data"""
        set_clauses = [f"{col} = :{col}" for col in update_data.keys()]
        update_data['project_id'] = project_id
        
        query = f"""
        UPDATE employee_projects 
        SET {', '.join(set_clauses)}
        WHERE id = :project_id
        """
        
        return self.execute_update(query, update_data) > 0
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project by ID"""
        query = "DELETE FROM employee_projects WHERE id = :project_id"
        return self.execute_update(query, {"project_id": project_id}) > 0
    
    def delete_projects_by_employee(self, employee_id: str) -> int:
        """Delete all projects for an employee"""
        query = "DELETE FROM employee_projects WHERE employee_id = :employee_id"
        return self.execute_update(query, {"employee_id": employee_id})
    
    def get_employee_total_occupancy(self, employee_id: str) -> int:
        """Get total occupancy for an employee"""
        query = """
        SELECT COALESCE(SUM(occupancy), 0) as total 
        FROM employee_projects 
        WHERE employee_id = :employee_id
        """
        result = self.execute_single(query, {"employee_id": employee_id})
        return result['total'] if result else 0
    
    def get_projects_by_name(self, project_name: str) -> List[Dict[str, Any]]:
        """Get all projects by name"""
        query = """
        SELECT * FROM employee_projects 
        WHERE LOWER(project_name) LIKE LOWER(:project_name)
        ORDER BY created_at DESC
        """
        return self.execute_query(query, {"project_name": f"%{project_name}%"})
    
    def get_projects_by_customer(self, customer: str) -> List[Dict[str, Any]]:
        """Get all projects by customer"""
        query = """
        SELECT * FROM employee_projects 
        WHERE LOWER(customer) LIKE LOWER(:customer)
        ORDER BY created_at DESC
        """
        return self.execute_query(query, {"customer": f"%{customer}%"})
    
    def clear_all_projects(self) -> int:
        """Clear all projects"""
        query = "DELETE FROM employee_projects"
        return self.execute_update(query)
    
    def bulk_insert_projects(self, projects_data: List[Dict[str, Any]]) -> int:
        """Bulk insert projects"""
        if not projects_data:
            return 0
        
        query = """
        INSERT INTO employee_projects (
            employee_id, project_name, customer, project_department,
            project_industry, project_status, occupancy,
            start_date, end_date, role, deployment, project_extended_end_date, project_committed_end_date
        ) VALUES (
            :employee_id, :project_name, :customer, :project_department,
            :project_industry, :project_status, :occupancy,
            :start_date, :end_date, :role, :deployment, :project_extended_end_date, :project_committed_end_date
        )
        """
        
        return self.execute_batch(query, projects_data)
    
    def get_all_projects_with_employees(self) -> List[Dict[str, Any]]:
        """Get all projects with employee details"""
        query = """
        SELECT 
            p.*,
            e.display_name,
            e.employee_department,
            e.tech_group,
            e.skill_set
        FROM employee_projects p
        JOIN employees e ON p.employee_id = e.employee_id
        ORDER BY p.created_at DESC
        """
        return self.execute_query(query)
    
    def get_employees_with_projects(self) -> List[Dict[str, Any]]:
        return self.execute_query("""
            SELECT e.*, p.*
            FROM employees e
            LEFT JOIN employee_projects p ON p.employee_id = e.employee_id
        """)