"""
Upload Service - Handles file uploads and data processing
"""
import logging
import pandas as pd
import io
from typing import Dict, Any, List
from fastapi import UploadFile, HTTPException
from sqlalchemy import text
from ..core.database import get_db_session, engine
from ..models.schemas import UploadResponse
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.project_repository import ProjectRepository
from .compression_service import compression_service
from datetime import datetime

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process uploaded data files"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def validate_file(self, filename: str) -> bool:
        """Validate file format"""
        return any(filename.lower().endswith(ext) for ext in self.supported_formats)
    
    def read_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Read file content into DataFrame"""
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format")
            
            # Clean data
            df = df.fillna('')
            df.columns = [col.strip().lower() for col in df.columns]
            
            logger.info(f"File read successfully: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise ValueError(f"Could not read file: {str(e)}")

class DatabaseManager:
    """Manage database operations"""
    
    def clear_existing_data(self):
        """Clear all existing data"""
        try:
            with get_db_session() as session:
                session.execute(text("DELETE FROM employee_projects"))
                session.execute(text("DELETE FROM employees"))
                session.commit()
                logger.info("Cleared existing data")
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise
    
    def insert_employees(self, employees_data: List[Dict]) -> int:
        """Insert employee records"""
        inserted = 0
        try:
            with get_db_session() as session:
                for employee in employees_data:
                    savepoint = session.begin_nested()
                    try:
                        columns = list(employee.keys())
                        values = [f":{col}" for col in columns]
                        
                        sql = f"""
                        INSERT INTO employees ({', '.join(columns)})
                        VALUES ({', '.join(values)})
                        """
                        
                        session.execute(text(sql), employee)
                        savepoint.commit()
                        inserted += 1
                    except Exception as e:
                        savepoint.rollback()
                        logger.error(f"Error inserting employee {employee.get('employee_id')}: {e}")
                        continue
                
                session.commit()
                logger.info(f"Inserted {inserted} employees")
                
        except Exception as e:
            logger.error(f"Employee insertion failed: {e}")
            raise
        
        return inserted
    
    def insert_projects(self, projects_data: List[Dict]) -> int:
        """Insert project records using batch processing with savepoints"""
        inserted = 0
        try:
            with get_db_session() as session:
                sql = """
                INSERT INTO employee_projects (
                    employee_id, project_name, customer, project_department, 
                    project_industry, project_status, occupancy,
                    project_extended_end_date, project_committed_end_date,
                    start_date, end_date, role, deployment, project_joined_date
                )
                VALUES (:employee_id, :project_name, :customer, :project_department, 
                        :project_industry, :project_status, :occupancy,
                        :project_extended_end_date, :project_committed_end_date,
                        :start_date, :end_date, :role, :deployment, :project_joined_date)
                """
                
                for project in projects_data:
                    try:
                        # Use savepoint for individual record error handling
                        savepoint = session.begin_nested()
                        
                        clean_project = {
                            'employee_id': project.get('employee_id', ''),
                            'project_name': project.get('project_name', ''),
                            'customer': project.get('customer', ''),
                            'project_department': project.get('project_department', ''),
                            'project_industry': project.get('project_industry', ''),
                            'project_status': project.get('project_status', 'active'),
                            'occupancy': project.get('occupancy', 0),
                            'project_extended_end_date': project.get('project_extended_end_date'),
                            'project_committed_end_date': project.get('project_committed_end_date'),
                            'start_date': project.get('start_date', ''),
                            'end_date': project.get('end_date'),
                            'role': project.get('role', ''),
                            'deployment': project.get('deployment', ''),
                            'project_joined_date': project.get('project_joined_date', '')
                        }
                        
                        session.execute(text(sql), clean_project)
                        savepoint.commit()
                        inserted += 1
                        
                    except Exception as e:
                        savepoint.rollback()
                        logger.error(f"Error inserting project {project.get('project_name', 'unknown')}: {e}")
                        continue
                
                logger.info(f"Inserted {inserted} projects")
                
        except Exception as e:
            logger.error(f"Project insertion failed: {e}")
            raise
        
        return inserted

class UploadService:
    """Main upload service"""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.db_manager = DatabaseManager()
        self.employee_repo = EmployeeRepository()
        self.project_repo = ProjectRepository()
        self.compression_service = compression_service
    
    async def process_file_upload(self, file: UploadFile, description: str = "") -> UploadResponse:
        """Process file upload"""
        try:
            # Validate file format
            if not self.processor.validate_file(file.filename):
                raise HTTPException(status_code=400, detail="Unsupported file format")
            
            # Read and process file
            start_time = datetime.now()
            file_content = await file.read()
            logger.info(f"File read time: {datetime.now() - start_time}s")
            if len(file_content) == 0:
                raise HTTPException(status_code=400, detail="Empty file")
            
            df = self.processor.read_file(file_content, file.filename)
            employees_data, projects_data = self._process_dataframe(df)
            
            # Clear and insert data
            self.db_manager.clear_existing_data()
            db_employees = self.db_manager.insert_employees(employees_data)
            db_projects = self.db_manager.insert_projects(projects_data)
            
            # # NEW: Generate compressed profiles after data insertion
            # await self.compression_service.rebuild_cache()
            
        except Exception as e:
            logger.error(f"File upload processing error: {e}")
            raise HTTPException(status_code=422, detail=f"Processing error: {str(e)}")
        
        try:
            all_employees = self._get_all_employees()
            
            return UploadResponse(
                status="success",
                message=f"Successfully processed {file.filename}",
                records_processed=len(df),
                database_records=db_employees + db_projects,
                vector_documents=0,
                file_metadata={
                    "rows": len(df),
                    "columns": len(df.columns),
                    "columns_list": list(df.columns)
                },
                all_employees=all_employees
            )
        except Exception as e:
            logger.error(f"Error building response: {e}")
            raise HTTPException(status_code=422, detail=f"Response building error: {str(e)}")
    
    def _process_dataframe(self, df: pd.DataFrame) -> tuple[List[Dict], List[Dict]]:
        """Process DataFrame into employees and projects data"""
        employees_data = {}
        projects_data = []
        
        for _, row in df.iterrows():
            employee_id = str(row.get('employee_id', '')).strip()
            if not employee_id:
                continue
            
            # Process employee data (once per employee)
            if employee_id not in employees_data:
                employees_data[employee_id] = {
                    'employee_id': employee_id,
                    'display_name': str(row.get('display_name', '')).strip(),
                    'employee_department': str(row.get('employee_department', '')).strip(),
                    'pm': str(row.get('pm', '')).strip(),
                    'total_exp': str(row.get('total_exp', '')).strip(),
                    'vvdn_exp': str(row.get('vvdn_exp', '')).strip(),
                    'designation': str(row.get('designation', '')).strip(),
                    'tech_group': str(row.get('tech_group', '')).strip(),
                    'emp_location': str(row.get('emp_location', '')).strip(),
                    'skill_set': str(row.get('skill_set', '')).strip(),
                    'rm_id': str(row.get('rm_id', '')).strip(),
                    'rm_name': str(row.get('rm_name', '')).strip(),
                    'joined_date': self._parse_date(row.get('joined_date')),
                    'committed_relieving_date': self._parse_date(row.get('committed_relieving_date')),
                    'extended_relieving_date': self._parse_date(row.get('extended_relieving_date'))
                }
            
            # Process project data
            project_name = row.get('project')
            if project_name and str(project_name).strip():
                projects_data.append({
                    'employee_id': employee_id,
                    'project_name': str(project_name).strip(),
                    'customer': str(row.get('customer', '')).strip(),
                    'project_department': str(row.get('project_department', '')).strip(),
                    'project_industry': str(row.get('project_industry', '')).strip(),
                    'project_status': str(row.get('project_status', '')).strip(),
                    'occupancy': self._safe_int_convert(row.get('occupancy', 0)),
                    'start_date': self._parse_date(row.get('start_date')),
                    'end_date': self._parse_date(row.get('end_date')),
                    'role': str(row.get('role', '')).strip(),
                    'deployment': str(row.get('deployment', '')).strip(),
                    'project_joined_date': self._parse_date(row.get('project_joined_date')),
                    'project_extended_end_date': self._parse_date(row.get('project_extended_end_date')),
                    'project_committed_end_date': self._parse_date(row.get('project_committed_end_date'))
                })
        
        return list(employees_data.values()), projects_data
    
    def _safe_int_convert(self, value) -> int:
        """Safely convert value to integer"""
        try:
            if pd.isna(value) or value == '':
                return 0
            return int(float(str(value)))
        except (ValueError, TypeError):
            return 0
    
    def _parse_date(self, value):
        """Safely parse date value"""
        try:
            if pd.isna(value) or value == '':
                return None
            # Handle various date formats
            return pd.to_datetime(value).date()
        except (ValueError, TypeError):
            return None
    
    def _get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees with their projects - matches hrms_chatbot.py format"""
        try:
            with get_db_session() as session:
                # Get all employees
                employees_result = session.execute(text("SELECT * FROM employees"))
                employees = [dict(row._mapping) for row in employees_result]
                
                # Get all projects grouped by employee
                projects_result = session.execute(text("""
                    SELECT employee_id, project_name, customer, project_department, 
                           project_industry, project_status, occupancy,
                           start_date, end_date, role, deployment, project_joined_date, project_extended_end_date, project_committed_end_date
                    FROM employee_projects 
                    ORDER BY employee_id, created_at
                """))
                
                # Group projects by employee_id
                projects_by_employee = {}
                for row in projects_result:
                    employee_id = row.employee_id
                    if employee_id not in projects_by_employee:
                        projects_by_employee[employee_id] = []
                    
                    projects_by_employee[employee_id].append({
                        "project_name": row.project_name,
                        "customer": row.customer,
                        "project_department": row.project_department,
                        "project_industry": row.project_industry,
                        "project_status": row.project_status,
                        "occupancy": row.occupancy or 0,
                        "role": row.role,
                        "deployment": row.deployment,
                        "start_date": str(row.start_date) if row.start_date else None,
                        "end_date": str(row.end_date) if row.end_date else None,
                        "project_joined_date": str(row.project_joined_date) if row.project_joined_date else None,
                        "project_extended_end_date": str(row.project_extended_end_date) if row.project_extended_end_date else None,
                        "project_committed_end_date": str(row.project_committed_end_date) if row.project_committed_end_date else None
                    })
                
                # Build comprehensive response matching hrms_chatbot.py format
                all_employees_response = []
                for employee in employees:
                    employee_id = employee.get('employee_id')
                    projects = projects_by_employee.get(employee_id, [])
                    
                    # Calculate total occupancy from projects
                    total_project_occupancy = sum(p.get('occupancy', 0) for p in projects)
                    available_capacity = max(0, 100 - total_project_occupancy)
                    
                    # Determine employee status based on deployment column
                    deployment_status = employee.get('deployment', '').lower()
                    is_billable = deployment_status == 'billable'
                    is_budgeted = deployment_status == 'budgeted'
                    is_free_pool = deployment_status == 'free'
                    is_support = deployment_status == 'support'
                    
                    employee_response = {
                        "employee_id": employee.get('employee_id', ''),
                        "display_name": employee.get('display_name', ''),
                        "employee_department": employee.get('employee_department', ''),
                        "role": employee.get('role', ''),
                        "deployment": employee.get('deployment', ''),
                        "occupancy": employee.get('occupancy', 0),  # Keep for backward compatibility
                        "total_project_occupancy": total_project_occupancy,
                        "available_capacity": available_capacity,
                        "joined_date": employee.get('joined_date', ''),
                        "total_exp": employee.get('total_exp', ''),
                        "vvdn_exp": employee.get('vvdn_exp', ''),
                        "designation": employee.get('designation', ''),
                        "tech_group": employee.get('tech_group', ''),
                        "emp_location": employee.get('emp_location', ''),
                        "skill_set": employee.get('skill_set', ''),
                        "rm_id": employee.get('rm_id', ''),
                        "rm_name": employee.get('rm_name', ''),
                        "projects": projects,
                        "project_count": len(projects),
                        "is_free_pool": is_free_pool,
                        "is_billable": is_billable,
                        "is_budgeted": is_budgeted,
                        "is_support": is_support,
                        "deployment_status": deployment_status
                    }
                    all_employees_response.append(employee_response)
                
                return all_employees_response
                
        except Exception as e:
            logger.error(f"Error getting all employees: {e}")
            return []
    
    async def initialize_database(self) -> Dict[str, Any]:
        """Initialize database tables"""
        try:
            with engine.connect() as conn:
                # Create schema
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS hrms"))
                
                # Create employees table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS employees (
                        employee_id VARCHAR(50) PRIMARY KEY,
                        display_name VARCHAR(255) NOT NULL,
                        employee_ou_type VARCHAR(100),
                        employee_department VARCHAR(100),
                        delivery_owner_emp_id VARCHAR(50),
                        delivery_owner VARCHAR(255),
                        joined_date VARCHAR(50),
                        role VARCHAR(100),
                        deployment VARCHAR(100),
                        created_by_employee_id VARCHAR(50),
                        created_by_display_name VARCHAR(255),
                        pm VARCHAR(255),
                        total_exp VARCHAR(50),
                        vvdn_exp VARCHAR(50),
                        designation VARCHAR(100),
                        sub_department VARCHAR(100),
                        tech_group VARCHAR(100),
                        emp_location VARCHAR(100),
                        rm_id VARCHAR(50),
                        rm_name VARCHAR(255),
                        skill_set TEXT,
                        occupancy INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Add new columns if they don't exist
                conn.execute(text("""
                    ALTER TABLE employees 
                    ADD COLUMN IF NOT EXISTS employee_ou_type VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS delivery_owner_emp_id VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS delivery_owner VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS joined_date VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS created_by_employee_id VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS created_by_display_name VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS pm VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS sub_department VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS rm_id VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS rm_name VARCHAR(255)
                """))
                
                # Create projects table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS employee_projects (
                        project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        employee_id VARCHAR(50) NOT NULL,
                        project_name VARCHAR(255),
                        customer VARCHAR(255),
                        project_department VARCHAR(100),
                        project_industry VARCHAR(100),
                        project_status VARCHAR(100),
                        occupancy INTEGER DEFAULT 0,
                        start_date DATE,
                        end_date DATE,
                        role VARCHAR(100),
                        deployment VARCHAR(100),
                        project_extended_end_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Add new columns if they don't exist
                conn.execute(text("""
                    ALTER TABLE employee_projects 
                    ADD COLUMN IF NOT EXISTS occupancy INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS start_date DATE,
                    ADD COLUMN IF NOT EXISTS end_date DATE,
                    ADD COLUMN IF NOT EXISTS role VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS deployment VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS project_extended_end_date DATE
                """))
                
                conn.commit()
                
            return {
                "status": "success",
                "message": "Database initialized successfully"
            }
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def get_employee_details(self, employee_id: str) -> Dict[str, Any]:
        """Get detailed employee information"""
        try:
            with get_db_session() as session:
                # Get employee data
                employee_result = session.execute(
                    text("SELECT * FROM employees WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                employee = employee_result.fetchone()
                
                if not employee:
                    raise ValueError(f"Employee {employee_id} not found")
                
                # Get projects
                projects_result = session.execute(
                    text("""
                        SELECT * FROM employee_projects 
                        WHERE employee_id = :employee_id 
                        ORDER BY created_at DESC
                    """),
                    {"employee_id": employee_id}
                )
                
                projects = [dict(row._mapping) for row in projects_result]
                employee_dict = dict(employee._mapping)
                employee_dict['projects'] = projects
                
                return {"status": "success", "employee": employee_dict}
                
        except Exception as e:
            logger.error(f"Error getting employee details: {e}")
            raise
    
    async def update_employee_skills(self, employee_id: str, skills_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee skills by appending new skills to existing ones"""
        try:
            with get_db_session() as session:
                # Get current skills
                current_result = session.execute(
                    text("SELECT skill_set FROM employees WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                current_row = current_result.fetchone()
                
                if not current_row:
                    raise ValueError(f"Employee {employee_id} not found")
                
                # Parse existing and new skills
                existing_skills = current_row.skill_set or ''
                new_skills = skills_data.get('skills', [])
                
                # Combine skills
                if existing_skills:
                    existing_skills_list = [s.strip() for s in existing_skills.split(',') if s.strip()]
                else:
                    existing_skills_list = []
                
                # Add new skills that don't already exist (case-insensitive)
                existing_lower = [s.lower() for s in existing_skills_list]
                for skill in new_skills:
                    if skill.strip() and skill.strip().lower() not in existing_lower:
                        existing_skills_list.append(skill.strip())
                
                # Update database
                updated_skill_set = ', '.join(existing_skills_list)
                session.execute(
                    text("UPDATE employees SET skill_set = :skill_set WHERE employee_id = :employee_id"),
                    {"skill_set": updated_skill_set, "employee_id": employee_id}
                )
                
                return {
                    "status": "success", 
                    "message": f"Added {len(new_skills)} skills successfully",
                    "updated_skills": updated_skill_set
                }
                
        except Exception as e:
            logger.error(f"Error updating skills: {e}")
            raise
    
    async def add_employee_projects(self, employee_id: str, projects_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new projects to employee (does not remove existing projects)"""
        try:
            with get_db_session() as session:
                projects = projects_data.get('projects', [])
                
                # Get current total occupancy
                current_result = session.execute(
                    text("SELECT COALESCE(SUM(occupancy), 0) as total FROM employee_projects WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                current_occupancy = current_result.fetchone().total
                
                # Validate new total occupancy
                new_occupancy = sum(p.get('occupancy', 0) for p in projects)
                total_occupancy = current_occupancy + new_occupancy
                
                if total_occupancy > 100:
                    raise ValueError(f"Total occupancy would be {total_occupancy}% (current: {current_occupancy}%, adding: {new_occupancy}%). Cannot exceed 100%")
                
                # Insert new projects
                for project in projects:
                    session.execute(
                        text("""
                            INSERT INTO employee_projects (
                                employee_id, project_name, customer, project_department,
                                project_industry, project_status, occupancy,
                                start_date, end_date, role, deployment, project_extended_end_date
                            ) VALUES (
                                :employee_id, :project_name, :customer, :project_department,
                                :project_industry, :project_status, :occupancy,
                                :start_date, :end_date, :role, :deployment, :project_extended_end_date
                            )
                        """),
                        {
                            "employee_id": employee_id,
                            "project_name": project.get('project_name', ''),
                            "customer": project.get('customer', ''),
                            "project_department": project.get('project_department', ''),
                            "project_industry": project.get('project_industry', ''),
                            "project_status": project.get('project_status', 'active'),
                            "occupancy": project.get('occupancy', 0),
                            "start_date": project.get('start_date'),
                            "end_date": project.get('end_date'),
                            "role": project.get('role', ''),
                            "deployment": project.get('deployment', ''),
                            "project_extended_end_date": project.get('project_extended_end_date')
                        }
                    )
                
                return {"status": "success", "message": f"Added {len(projects)} projects successfully"}
                
        except Exception as e:
            logger.error(f"Error adding projects: {e}")
            raise
    
    async def list_employee_projects(self, employee_id: str) -> Dict[str, Any]:
        """List all projects for an employee"""
        try:
            with get_db_session() as session:
                # Check if employee exists
                employee_check = session.execute(
                    text("SELECT 1 FROM employees WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                if not employee_check.fetchone():
                    raise ValueError(f"Employee {employee_id} not found")
                
                # Get projects
                projects_result = session.execute(
                    text("""
                        SELECT id, project_name, customer, project_department,
                               project_industry, project_status, occupancy,
                               start_date, end_date, role, deployment, project_extended_end_date
                        FROM employee_projects 
                        WHERE employee_id = :employee_id 
                        ORDER BY created_at DESC
                    """),
                    {"employee_id": employee_id}
                )
                
                projects = []
                total_occupancy = 0
                
                for row in projects_result:
                    occupancy = row.occupancy or 0
                    total_occupancy += occupancy
                    
                    projects.append({
                        "id": str(row.id),
                        "project_name": row.project_name,
                        "customer": row.customer,
                        "project_department": row.project_department,
                        "project_industry": row.project_industry,
                        "project_status": row.project_status,
                        "occupancy": occupancy,
                        "role": row.role,
                        "deployment": row.deployment,
                        "start_date": str(row.start_date) if row.start_date else None,
                        "end_date": str(row.end_date) if row.end_date else None,
                        "project_extended_end_date": str(row.project_extended_end_date) if row.project_extended_end_date else None
                    })
                
                return {
                    "status": "success",
                    "projects": projects,
                    "total_occupancy": total_occupancy,
                    "available_capacity": max(0, 100 - total_occupancy)
                }
                
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise
    
    async def delete_all_employee_projects(self, employee_id: str) -> Dict[str, Any]:
        """Delete all projects for an employee"""
        try:
            with get_db_session() as session:
                # Check if employee exists
                employee_check = session.execute(
                    text("SELECT 1 FROM employees WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                if not employee_check.fetchone():
                    raise ValueError(f"Employee {employee_id} not found")
                
                # Count projects to be deleted
                count_result = session.execute(
                    text("SELECT COUNT(*) as count FROM employee_projects WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                project_count = count_result.fetchone().count
                
                # Delete all projects
                session.execute(
                    text("DELETE FROM employee_projects WHERE employee_id = :employee_id"),
                    {"employee_id": employee_id}
                )
                
                return {
                    "status": "success",
                    "message": f"Deleted {project_count} projects for employee {employee_id}"
                }
                
        except Exception as e:
            logger.error(f"Error deleting all projects: {e}")
            raise
    
    async def delete_employee_project(self, employee_id: str, project_id: str) -> Dict[str, Any]:
        """Delete specific project for an employee"""
        try:
            with get_db_session() as session:
                # Check if project exists for this employee
                project_check = session.execute(
                    text("""
                        SELECT project_name FROM employee_projects 
                        WHERE employee_id = :employee_id AND id = :project_id
                    """),
                    {"employee_id": employee_id, "project_id": project_id}
                )
                project = project_check.fetchone()
                
                if not project:
                    raise ValueError(f"Project {project_id} not found for employee {employee_id}")
                
                # Delete the project
                session.execute(
                    text("""
                        DELETE FROM employee_projects 
                        WHERE employee_id = :employee_id AND id = :project_id
                    """),
                    {"employee_id": employee_id, "project_id": project_id}
                )
                
                return {
                    "status": "success",
                    "message": f"Deleted project '{project.project_name}' for employee {employee_id}"
                }
                
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            raise
    
    async def update_employee_profile(self, employee_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee profile"""
        try:
            with get_db_session() as session:
                # Build dynamic update query
                allowed_fields = ['display_name', 'employee_department', 'role', 'deployment', 
                                'total_exp', 'vvdn_exp', 'designation', 'tech_group', 'emp_location']
                
                update_fields = []
                params = {'employee_id': employee_id}
                
                for field in allowed_fields:
                    if field in profile_data:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = profile_data[field]
                
                if update_fields:
                    sql = f"UPDATE employees SET {', '.join(update_fields)} WHERE employee_id = :employee_id"
                    session.execute(text(sql), params)
                
                return {"status": "success", "message": "Profile updated successfully"}
                
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            raise

    async def get_all_employee_details(self, page_number: int, page_size: int) -> Dict[str, Any]:
        """Get all Employee Details including Projects"""
        try:
            offset = (page_number - 1) * page_size
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT 
                            e.*,

                            COALESCE(
                                json_agg(DISTINCT to_jsonb(ep))
                                FILTER (WHERE ep.employee_id IS NOT NULL),
                                '[]'::json
                            ) AS projects

                        FROM employees e
                        LEFT JOIN employee_projects ep 
                            ON e.employee_id = ep.employee_id

                        GROUP BY e.employee_id

                        ORDER BY split_part(e.employee_id, '/', 2)::int
                        LIMIT :limit OFFSET :offset;"""
                    ),
                    {
                        "limit": page_size,
                        "offset": offset
                    }
                ).mappings().all()
            employees = [dict(row) for row in result]
            return {
                "status": 200,
                "employees": employees
            }
        except Exception as e:
            logger.error(f"Failed to fetch from DB: {str(e)}")
            raise