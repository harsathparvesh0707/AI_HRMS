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

            required_columns = {"employee_id", "display_name", "employee_ou_type", "employee_department", "total_exp", "vvdn_exp", "designation",
                                "sub_department", "tech_group", "emp_location", "rm_id", "rm_name", "skill_set", "project", "customer",
                                "project_department", "project_industry", "project_status", "delivery_owner_emp_id", "delivery_owner", "pm",
                                "project_category", "project_committed_end_date", "project_extended_end_date", "role", "deployment", "occupancy",
                                "committed_relieving_date", "extended_relieving_date"}
            missing_columns = required_columns - set(df.columns)

            if missing_columns:
                logger.warning(f"Missing required Columns: {', '.join(missing_columns)}")
                raise ValueError(f"Upload File is Incorrect. Missing required Columns")
            
            logger.info(f"File read successfully: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise ValueError(f"{str(e)}")

class DatabaseManager:
    """Manage database operations"""
    
    def clear_existing_data(self):
        """Clear all existing data"""
        try:
            with get_db_session() as session:
                session.execute(text("DELETE FROM project_requirement_suggestions"))
                session.execute(text("DELETE FROM project_requirements"))
                session.execute(text("DELETE FROM employee_projects"))
                session.execute(text("DELETE FROM projects"))
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
                for project in projects_data:
                    try:
                        # Use savepoint for individual record error handling
                        savepoint = session.begin_nested()
                        
                        session.execute(text("""
                            INSERT INTO projects (
                                project_name, customer, project_department,
                                project_industry, project_status, project_category,
                                delivery_owner_emp_id, delivery_owner, pm,
                                project_committed_end_date, project_extended_end_date
                            )
                            VALUES (
                                :project_name, :customer, :project_department,
                                :project_industry, :project_status, :project_category,
                                :delivery_owner_emp_id, :delivery_owner, :pm,
                                :project_committed_end_date, :project_extended_end_date
                            )
                        """), project)

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
    
    def insert_employee_project(self, employee_projects_data: List[Dict]) -> int:
        inserted = 0
        with get_db_session() as session:
            for row in employee_projects_data:
                try:
                    savepoint = session.begin_nested()
                    session.execute(text("""
                        INSERT INTO employee_projects (
                            employee_id, project_name, project_joined_date,
                            role, deployment, occupancy,
                            committed_relieving_date, extended_relieving_date,
                            created_by_employee_id, created_by_display_name
                        )
                        VALUES (
                            :employee_id, :project_name, :project_joined_date,
                            :role, :deployment, :occupancy,
                            :committed_relieving_date, :extended_relieving_date,
                            :created_by_employee_id, :created_by_display_name
                        )
                    """), row)
                    savepoint.commit()
                    inserted += 1
                    
                except Exception as e:
                    logger.error(f"Employee project insert error: {e}")
                    continue
            session.commit()
            logger.info(f"Inserted {inserted} Employee Project Mapping Details")
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
            employees_data, projects_data, employees_project_data = self._process_dataframe(df)
            
            # Clear and insert data
            self.db_manager.clear_existing_data()
            db_employees = self.db_manager.insert_employees(employees_data)
            db_projects = self.db_manager.insert_projects(projects_data)
            db_employees_projects_data = self.db_manager.insert_employee_project(employees_project_data)
            
            # # NEW: Generate compressed profiles after data insertion
            # await self.compression_service.rebuild_cache()
        except ValueError as e:
            logger.error(f"File validation error: {e}")
            raise ValueError(f"File validation error: {str(e)}")
            
        except Exception as e:
            logger.error(f"File upload processing error: {e}")
            raise HTTPException(status_code=422, detail=f"Processing error: {str(e)}")
        
        try:
            all_employees = self._get_all_employees()
            
            return UploadResponse(
                status="success",
                message=f"Successfully processed {file.filename}",
                records_processed=len(df),
                database_records=db_employees + db_projects + db_employees_projects_data,
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
        projects_data = {}
        employee_projects_data = []
        
        for _, row in df.iterrows():
            employee_id = str(row.get('employee_id', '')).strip()
            if not employee_id:
                continue
            
            # Employee
            if employee_id not in employees_data:
                employees_data[employee_id] = {
                    'employee_id': employee_id,
                    'display_name': str(row.get('display_name', '')).strip(),
                    'employee_department': str(row.get('employee_department', '')).strip(),
                    'total_exp': str(row.get('total_exp', '')).strip(),
                    'vvdn_exp': str(row.get('vvdn_exp', '')).strip(),
                    'designation': str(row.get('designation', '')).strip(),
                    'tech_group': str(row.get('tech_group', '')).strip(),
                    'emp_location': str(row.get('emp_location', '')).strip(),
                    'skill_set': str(row.get('skill_set', '')).strip(),
                    'rm_id': str(row.get('rm_id', '')).strip(),
                    'rm_name': str(row.get('rm_name', '')).strip(),
                    'employee_ou_type': str(row.get('employee_ou_type')).strip(),
                    'sub_department': str(row.get('sub_department')).strip()
                }
            
            # Projects
            project_name = str(row.get('project', '')).strip()
            if project_name:
                if project_name not in projects_data:
                    projects_data[project_name] = {
                        'project_name': project_name,
                        'customer': str(row.get('customer', '')).strip(),
                        'project_department': str(row.get('project_department', '')).strip(),
                        'project_industry': str(row.get('project_industry', '')).strip(),
                        'project_status': str(row.get('project_status', '')).strip(),
                        'project_category': str(row.get('project_category', '')).strip(),
                        'delivery_owner_emp_id': str(row.get('delivery_owner_emp_id', '')).strip(),
                        'delivery_owner': str(row.get('delivery_owner', '')).strip(),
                        'pm': str(row.get('pm', '')).strip(),
                        'project_committed_end_date': self._parse_date(row.get('project_committed_end_date')),
                        'project_extended_end_date': self._parse_date(row.get('project_extended_end_date'))
                    }
            
            # Employee Projects
            employee_projects_data.append({
                'employee_id': employee_id,
                'project_name': project_name,
                'project_joined_date': self._parse_date(row.get('joined_date')),
                'start_date': self._parse_date(row.get('start_date')),
                'end_date': self._parse_date(row.get('end_date')),
                'role': str(row.get('role', '')).strip(),
                'deployment': str(row.get('deployment', '')).strip(),
                'occupancy': self._safe_int_convert(row.get('occupancy', 0)),
                'committed_relieving_date': self._parse_date(row.get('committed_relieving_date')),
                'extended_relieving_date': self._parse_date(row.get('extended_relieving_date')),
                'created_by_employee_id': employee_id,
                'created_by_display_name': str(row.get('display_name', '')).strip()
            })
        
        return list(employees_data.values()), list(projects_data.values()), employee_projects_data
    
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
                SELECT 
                    ep.employee_id,
                    p.project_name,
                    p.customer,
                    p.project_department,
                    p.project_industry,
                    p.project_status,
                    ep.occupancy,
                    ep.role,
                    ep.deployment,
                    ep.project_joined_date,
                    p.project_extended_end_date,
                    p.project_committed_end_date,
                    ep.start_date,
                    ep.end_date
                FROM employee_projects ep
                LEFT JOIN projects p 
                    ON ep.project_name = p.project_name
                ORDER BY ep.employee_id, ep.created_at
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
                conn.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS employees (
                        employee_id VARCHAR(50) PRIMARY KEY,
                        display_name VARCHAR(255),
                        employee_ou_type VARCHAR(100),
                        employee_department VARCHAR(100),
                        total_exp VARCHAR(50),
                        vvdn_exp VARCHAR(50),
                        designation VARCHAR(100),
                        sub_department VARCHAR(100),
                        tech_group VARCHAR(100),
                        emp_location VARCHAR(100),
                        rm_id VARCHAR(50),
                        rm_name VARCHAR(255),
                        skill_set TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """))
                
                conn.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        project_name VARCHAR(50) PRIMARY KEY,
                        customer VARCHAR(255),
                        project_department VARCHAR(100),
                        project_industry VARCHAR(100),
                        project_status VARCHAR(50),
                        delivery_owner_emp_id VARCHAR(50),
                        delivery_owner VARCHAR(255),
                        pm VARCHAR(255),
                        project_category VARCHAR(255),
                        project_committed_end_date DATE,
                        project_extended_end_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                ))

                conn.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS employee_projects (
                        id SERIAL PRIMARY KEY,
                        employee_id VARCHAR(50) REFERENCES employees(employee_id),
                        project_name VARCHAR(50) REFERENCES projects(project_name),
                        project_joined_date DATE,
                        role VARCHAR(100),
                        deployment VARCHAR(100),
                        committed_relieving_date DATE,
                        extended_relieving_date DATE,
                        occupancy INTEGER DEFAULT 0,
                        created_by_employee_id VARCHAR(50),
                        created_by_display_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                ))
                
                conn.execute(text("""CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
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
                        SELECT 
                            ep.*,
                            p.project_name,
                            p.customer,
                            p.project_department,
                            p.project_industry,
                            p.project_status,
                            p.project_category,
                            p.pm,
                            p.project_committed_end_date,
                            p.project_extended_end_date
                        FROM employee_projects ep
                        LEFT JOIN projects p 
                            ON ep.project_name = p.project_name
                        WHERE ep.employee_id = :employee_id
                        ORDER BY ep.created_at DESC
                    """),
                    {"employee_id": employee_id}
                )
                
                projects = []
                for row in projects_result:
                    row_dict = dict(row._mapping)
                    projects.append(row_dict)
                employee_dict = dict(employee._mapping)
                employee_dict['projects'] = projects

                return {
                    "status": "success",
                    "employee": employee_dict
                }
                
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
                # existing_skills = current_row.skill_set or ''
                # new_skills = skills_data.get('skills', [])
                
                # # Combine skills
                # if existing_skills:
                #     existing_skills_list = [s.strip() for s in existing_skills.split(',') if s.strip()]
                # else:
                #     existing_skills_list = []
                
                # # Add new skills that don't already exist (case-insensitive)
                # existing_lower = [s.lower() for s in existing_skills_list]
                # for skill in new_skills:
                #     if skill.strip() and skill.strip().lower() not in existing_lower:
                #         existing_skills_list.append(skill.strip())

                
                # Update database
                skills_list = skills_data.get('skills', [])
                # Clean + normalize
                cleaned_skills = [
                    skill.strip()
                    for skill in skills_list
                    if skill and skill.strip()
                ]

                # Convert to comma-separated string
                updated_skill_set = ", ".join(cleaned_skills)
                logger.info(updated_skill_set)
                session.execute(
                    text("UPDATE employees SET skill_set = :skill_set WHERE employee_id = :employee_id"),
                    {"skill_set": updated_skill_set, "employee_id": employee_id}
                )
                
                return {
                    "status": "success", 
                    "message": f"Updated skills successfully",
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

                # ================= CURRENT OCCUPANCY =================
                current_result = session.execute(
                    text("""
                        SELECT COALESCE(SUM(occupancy), 0) as total 
                        FROM employee_projects 
                        WHERE employee_id = :employee_id
                    """),
                    {"employee_id": employee_id}
                )
                current_occupancy = current_result.fetchone().total

                # ================= VALIDATION =================
                new_occupancy = sum(p.get('occupancy', 0) for p in projects)
                total_occupancy = current_occupancy + new_occupancy

                if total_occupancy > 100:
                    raise ValueError(
                        f"Total occupancy would be {total_occupancy}% "
                        f"(current: {current_occupancy}%, adding: {new_occupancy}%). Cannot exceed 100%"
                    )

                # ================= INSERT =================
                for project in projects:
                    project_name = project.get('project_name')  # using project_name as project_id

                    if not project_name:
                        continue

                    # -------- 1. INSERT INTO PROJECTS (if not exists) --------
                    session.execute(
                        text("""
                            INSERT INTO projects (
                                project_name customer, project_department,
                                project_industry, project_status,
                                project_category, pm,
                                project_committed_end_date, project_extended_end_date
                            )
                            VALUES (
                                :project_name, :customer, :project_department,
                                :project_industry, :project_status,
                                :project_category, :pm,
                                :project_committed_end_date, :project_extended_end_date
                            )
                            ON CONFLICT (project_id) DO NOTHING
                        """),
                        {
                            "project_name": project_name,
                            "customer": project.get('customer', ''),
                            "project_department": project.get('project_department', ''),
                            "project_industry": project.get('project_industry', ''),
                            "project_status": project.get('project_status', 'active'),
                            "project_category": project.get('project_category', ''),
                            "pm": project.get('pm', ''),
                            "project_committed_end_date": project.get('project_committed_end_date'),
                            "project_extended_end_date": project.get('project_extended_end_date')
                        }
                    )

                    # -------- 2. INSERT INTO EMPLOYEE_PROJECTS --------
                    session.execute(
                        text("""
                            INSERT INTO employee_projects (
                                employee_id, project_name, project_joined_date,
                                role, deployment, occupancy,
                                committed_relieving_date, extended_relieving_date,
                                created_by_employee_id, created_by_display_name
                            )
                            VALUES (
                                :employee_id, :project_name, :project_joined_date,
                                :role, :deployment, :occupancy,
                                :committed_relieving_date, :extended_relieving_date,
                                :created_by_employee_id, :created_by_display_name
                            )
                        """),
                        {
                            "employee_id": employee_id,
                            "project_name": project_name,
                            "project_joined_date": project.get('project_joined_date'),
                            "role": project.get('role', ''),
                            "deployment": project.get('deployment', ''),
                            "occupancy": project.get('occupancy', 0),
                            "committed_relieving_date": project.get('project_committed_end_date'),
                            "extended_relieving_date": project.get('project_extended_end_date'),
                            "created_by_employee_id": employee_id,
                            "created_by_display_name": project.get('created_by_display_name', '')
                        }
                    )

                session.commit()

                return {
                    "status": "success",
                    "message": f"Added {len(projects)} projects successfully"
                }

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
                        SELECT 
                            ep.id,
                            ep.project_name,
                            p.customer,
                            p.project_department,
                            p.project_industry,
                            p.project_status,
                            ep.occupancy,
                            ep.role,
                            ep.deployment,
                            ep.project_joined_date,
                            p.project_extended_end_date,
                            p.project_committed_end_date

                        FROM employee_projects ep
                        LEFT JOIN projects p 
                            ON ep.project_name = p.project_name

                        WHERE ep.employee_id = :employee_id

                        ORDER BY ep.created_at DESC
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
                        "project_committed_end_date": str(row.project_committed_end_date) if row.project_committed_end_date else None,
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
    
    async def delete_employee_project(self, employee_id: str, project_name: str) -> Dict[str, Any]:
        """Delete specific project for an employee"""
        try:
            with get_db_session() as session:
                # Check if project exists for this employee
                project_check = session.execute(
                    text("""
                        SELECT id FROM employee_projects 
                        WHERE employee_id = :employee_id AND project_name = :project_name
                    """),
                    {"employee_id": employee_id, "project_name": project_name}
                )
                project_id = project_check.fetchone()
                
                if not project_id:
                    raise ValueError(f"Project {project_name} not found for employee {employee_id}")
                
                # Delete the project
                session.execute(
                    text("""
                        DELETE FROM employee_projects 
                        WHERE employee_id = :employee_id AND project_name = :project_name
                    """),
                    {"employee_id": employee_id, "project_name": project_name}
                )
                
                return {
                    "status": "success",
                    "message": f"Deleted project '{project_name}' for employee {employee_id}"
                }
                
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            raise
    
    async def update_employee_profile(self, employee_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee profile"""
        try:
            with get_db_session() as session:
                # Build dynamic update query
                allowed_fields = ['display_name', 'employee_department', 'total_exp', 'vvdn_exp',
                                'designation', 'tech_group', 'emp_location']
                
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
                total = session.execute(
                    text(
                        "SELECT COUNT(*) FROM employees;"
                    )
                ).scalar()
                result = session.execute(
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
                            ) AS projects
                        FROM employees e
                        LEFT JOIN employee_projects ep 
                            ON e.employee_id = ep.employee_id
                        LEFT JOIN projects p 
                            ON ep.project_name = p.project_name
                        GROUP BY e.employee_id
                        ORDER BY split_part(e.employee_id, '/', 2)::int
                        LIMIT :limit OFFSET :offset;
                        """
                    ),
                    {
                        "limit": page_size,
                        "offset": offset
                    }
                ).mappings().all()
            employees = [dict(row) for row in result]
            return {
                "status": 200,
                "total_employees": total,
                "employees": employees
            }
        except Exception as e:
            logger.error(f"Failed to fetch from DB: {str(e)}")
            raise