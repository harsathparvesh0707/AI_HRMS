# complete_hrms_chatbot_enhanced.py
import os
import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from langchain.llms import Ollama
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import io
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil

# -------------------------
# Config
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/hrms_db")
VECTOR_PERSIST_DIR = os.getenv("VECTOR_PERSIST_DIR", "./chroma_db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:0.5b").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# DB setup (SQLAlchemy)
# -------------------------
try:
    engine: Engine = create_engine(DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine)
    metadata = MetaData()
    logger.info("Database connection established")
except Exception as e:
    logger.error(f"Error setting up database: {e}")
    raise

# -------------------------
# Embeddings + Vector DB
# -------------------------
try:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma(persist_directory=VECTOR_PERSIST_DIR, embedding_function=embeddings)
    logger.info("Vector store initialized")
except Exception as e:
    logger.error(f"Error initializing vector store: {e}")
    raise

# -------------------------
# LLM
# -------------------------
try:
    llm = Ollama(model=OLLAMA_MODEL, verbose=True)
    logger.info(f"LLM initialized with model: {OLLAMA_MODEL}")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    raise

# -------------------------
# Pydantic models
# -------------------------
class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    search_type: Optional[str] = "combined"

class ChatResponse(BaseModel):
    action: str
    response: str
    data: Dict[str, Any]
    ui_suggestions: List[Dict[str, Any]]
    search_metadata: Dict[str, Any]

class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int
    database_records: int
    vector_documents: int
    file_metadata: Dict[str, Any]
    all_employees: List[Dict[str, Any]]

# -------------------------
# Database Setup
# -------------------------
def setup_database():
    """Creates PostgreSQL database and tables if they don't exist"""
    try:
        with engine.connect() as conn:
            # Create schema
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS hrms"))
            
            # Create employees table with all CSV fields
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS hrms.employees (
                    employee_id VARCHAR(50) PRIMARY KEY,
                    display_name VARCHAR(255) NOT NULL,
                    employee_ou_type VARCHAR(100),
                    employee_department VARCHAR(100),
                    delivery_owner_emp_id VARCHAR(50),
                    delivery_owner VARCHAR(255),
                    joined_date VARCHAR(50),
                    role VARCHAR(100),
                    deployment VARCHAR(100),
                    occupancy INTEGER,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create employee_projects table WITHOUT unique constraint initially
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS hrms.employee_projects (
                    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    employee_id VARCHAR(50) NOT NULL,
                    project_name VARCHAR(255),
                    customer VARCHAR(255),
                    project_department VARCHAR(100),
                    project_industry VARCHAR(100),
                    project_status VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
            logger.info("✅ Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        # Don't raise the exception, just log it
        logger.info("Database setup completed with warnings")

def cleanup_duplicate_projects():
    """Clean up duplicate project entries"""
    try:
        with engine.connect() as conn:
            # First check if table exists
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'hrms' 
                    AND table_name = 'employee_projects'
                )
            """)).scalar()
            
            if not table_exists:
                logger.info("No employee_projects table to clean up")
                return
                
            # Remove duplicate projects keeping the latest one
            cleanup_sql = """
            DELETE FROM hrms.employee_projects 
            WHERE project_id NOT IN (
                SELECT DISTINCT ON (employee_id, project_name) project_id
                FROM hrms.employee_projects 
                ORDER BY employee_id, project_name, created_at DESC
            )
            """
            result = conn.execute(text(cleanup_sql))
            conn.commit()
            logger.info(f"✅ Cleaned up {result.rowcount} duplicate project entries")
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {e}")

# -------------------------
# Metadata Filtering Utility
# -------------------------
def filter_complex_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out complex metadata types that ChromaDB cannot handle.
    Converts lists to strings and removes other complex types.
    """
    filtered_metadata = {}
    
    for key, value in metadata.items():
        if value is None:
            filtered_metadata[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            filtered_metadata[key] = value
        elif isinstance(value, list):
            # Convert list to comma-separated string
            filtered_metadata[key] = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            # Convert dict to JSON string
            filtered_metadata[key] = json.dumps(value)
        else:
            # Convert any other type to string
            filtered_metadata[key] = str(value)
    
    return filtered_metadata

# -------------------------
# Enhanced Response Builder for Frontend
# -------------------------
def build_employee_with_projects_response(employee_data: Dict, projects_data: List[Dict]) -> Dict[str, Any]:
    """Build comprehensive employee response with all projects"""
    
    # Determine employee status based on deployment column (FIXED)
    deployment_status = employee_data.get('deployment', '').lower()
    is_billable = deployment_status == 'billable'
    is_budgeted = deployment_status == 'budgeted'
    is_free_pool = deployment_status == 'free'
    is_support = deployment_status == 'support'
    
    # Format projects for response
    formatted_projects = []
    for project in projects_data:
        formatted_projects.append({
            "project_name": project.get('project_name', ''),
            "customer": project.get('customer', ''),
            "project_department": project.get('project_department', ''),
            "project_industry": project.get('project_industry', ''),
            "project_status": project.get('project_status', '')
        })
    
    return {
        "employee_id": employee_data.get('employee_id', ''),
        "display_name": employee_data.get('display_name', ''),
        "employee_ou_type": employee_data.get('employee_ou_type', ''),
        "employee_department": employee_data.get('employee_department', ''),
        "delivery_owner_emp_id": employee_data.get('delivery_owner_emp_id', ''),
        "delivery_owner": employee_data.get('delivery_owner', ''),
        "joined_date": employee_data.get('joined_date', ''),
        "role": employee_data.get('role', ''),
        "deployment": employee_data.get('deployment', ''),
        "occupancy": employee_data.get('occupancy', 0),
        "created_by_employee_id": employee_data.get('created_by_employee_id', ''),
        "created_by_display_name": employee_data.get('created_by_display_name', ''),
        "pm": employee_data.get('pm', ''),
        "total_exp": employee_data.get('total_exp', ''),
        "vvdn_exp": employee_data.get('vvdn_exp', ''),
        "designation": employee_data.get('designation', ''),
        "sub_department": employee_data.get('sub_department', ''),
        "tech_group": employee_data.get('tech_group', ''),
        "emp_location": employee_data.get('emp_location', ''),
        "rm_id": employee_data.get('rm_id', ''),
        "rm_name": employee_data.get('rm_name', ''),
        "skill_set": employee_data.get('skill_set', ''),
        "projects": formatted_projects,
        "project_count": len(formatted_projects),
        "is_free_pool": is_free_pool,
        "is_billable": is_billable,
        "is_budgeted": is_budgeted,
        "is_support": is_support,
        "deployment_status": deployment_status
    }

def get_all_employees_with_projects() -> List[Dict[str, Any]]:
    """Get all employees with their projects for upload response"""
    try:
        with engine.connect() as conn:
            # Get all employees
            employees_result = conn.execute(text("SELECT * FROM hrms.employees"))
            employees = [dict(row._mapping) for row in employees_result]
            
            # Get all projects grouped by employee
            projects_result = conn.execute(text("""
                SELECT employee_id, project_name, customer, project_department, 
                       project_industry, project_status 
                FROM hrms.employee_projects 
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
                    "project_status": row.project_status
                })
            
            # Build comprehensive response
            all_employees_response = []
            for employee in employees:
                employee_id = employee.get('employee_id')
                projects = projects_by_employee.get(employee_id, [])
                
                employee_response = build_employee_with_projects_response(employee, projects)
                all_employees_response.append(employee_response)
            
            return all_employees_response
            
    except Exception as e:
        logger.error(f"Error getting all employees with projects: {e}")
        return []

# -------------------------
# Experience Parser Utility
# -------------------------
def parse_experience_years(exp_string: str) -> float:
    """
    Parse experience string to extract years as float.
    Handles formats like: '10 years', '5.5 years', '8+ years', '3-5 years', '2.5'
    """
    if not exp_string or pd.isna(exp_string):
        return 0.0
    
    exp_string = str(exp_string).lower().strip()
    
    # Extract numbers using regex
    numbers = re.findall(r'(\d+\.?\d*)', exp_string)
    if numbers:
        # Take the first number found
        return float(numbers[0])
    
    return 0.0

# -------------------------
# Enhanced Multi-Condition Query Handler
# -------------------------
def handle_multi_condition_query(query: str) -> Dict[str, Any]:
    """
    Handle complex queries with multiple conditions like:
    - "freepool and python developers" 
    - "employees in cloud department with java skills"
    - "free pool python developers"
    - "show all java developers in freepool"
    - "python developers in VIMU_GSUP"
    - "bangalore python developers in free pool"
    - "employees with more than 10 years experience"
    """
    try:
        query_lower = query.lower()
        
        # Extract conditions
        conditions = {
            'free_pool': any(term in query_lower for term in ['free pool', 'freepool', 'free']),
            'billable': any(term in query_lower for term in ['billable', 'billable employees']),
            'budgeted': any(term in query_lower for term in ['budgeted', 'budgeted employees']),
            'support': any(term in query_lower for term in ['support', 'support employees']),
            'skills': [],
            'department': None,
            'location': None,
            'project': None,
            'experience_min': None,
            'experience_max': None,
            'exact_name': None
        }
        
        # Extract exact name for precise matching (FIXED)
        name_patterns = [
            r'^show\s+details\s+of\s+([a-zA-Z\s]+)$',
            r'^find\s+employee\s+([a-zA-Z\s]+)$',
            r'^([a-zA-Z\s]+)\s+details$',
            r'^employee\s+([a-zA-Z\s]+)$',
            r'^who\s+is\s+([a-zA-Z\s]+)$',
            r'^get\s+([a-zA-Z\s]+)\s+information$',
            r'^search\s+for\s+([a-zA-Z\s]+)$',
            r'^lookup\s+([a-zA-Z\s]+)$',
            r'^([a-zA-Z\s]+)$',
            r'^find\s+([a-zA-Z\s]+)$',
            r'^search\s+([a-zA-Z\s]+)$'

        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:  # Ensure it's a meaningful name
                    conditions['exact_name'] = name
                    break
        
        # Extract experience conditions
        exp_patterns = [
            (r'more than\s*(\d+)\s*years?', 'min'),
            (r'greater than\s*(\d+)\s*years?', 'min'),
            (r'over\s*(\d+)\s*years?', 'min'),
            (r'less than\s*(\d+)\s*years?', 'max'),
            (r'under\s*(\d+)\s*years?', 'max'),
            (r'(\d+)\s*\+\s*years?', 'min'),
            (r'(\d+)\s*-\s*(\d+)\s*years?', 'range'),
            (r'(\d+)\s*to\s*(\d+)\s*years?', 'range'),
            (r'(\d+)\s*years?', 'exact')
        ]
        
        for pattern, exp_type in exp_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if exp_type == 'min':
                    conditions['experience_min'] = float(match.group(1))
                elif exp_type == 'max':
                    conditions['experience_max'] = float(match.group(1))
                elif exp_type == 'range':
                    conditions['experience_min'] = float(match.group(1))
                    conditions['experience_max'] = float(match.group(2))
                elif exp_type == 'exact':
                    conditions['experience_min'] = float(match.group(1))
                    conditions['experience_max'] = float(match.group(1))
                break
        
        # Extract skills
        skill_keywords = ['python', 'java', 'javascript', 'react', 'angular', 'docker', 'kubernetes', 
                         'aws', 'azure', 'golang', 'spring', 'node', 'mysql', 'postgresql', 'mongodb',
                         'microservices', 'devops', 'ai/ml', 'machine learning', 'data science']
        
        for skill in skill_keywords:
            if skill in query_lower:
                conditions['skills'].append(skill)
        
        # Extract project names (common project patterns)
        project_patterns = [
            r'in\s+(\w+_\w+)',
            r'project\s+(\w+_\w+)',
            r'team\s+of\s+(\w+_\w+)',
            r'(\w+_\w+)\s+project',
            r'(\w+_\w+)\s+team'
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, query_lower)
            if match:
                project_name = match.group(1).upper()
                conditions['project'] = project_name
                break
        
        # Extract department
        dept_patterns = [
            (r'cloud department', 'Cloud'),
            (r'quality department', 'Quality'),
            (r'it department', 'IT'),
            (r'devops department', 'DevOps'),
            (r'data department', 'Data'),
            (r'mobile department', 'Mobile')
        ]
        
        for pattern, dept in dept_patterns:
            if re.search(pattern, query_lower):
                conditions['department'] = dept
                break
        
        # Enhanced location extraction
        location_keywords = ['bangalore', 'kochi', 'gurgaon', 'pune', 'chennai', 'hyderabad', 'delhi', 'mumbai']
        location_patterns = [
            r'in\s+(bangalore|kochi|gurgaon|pune|chennai|hyderabad|delhi|mumbai)',
            r'(bangalore|kochi|gurgaon|pune|chennai|hyderabad|delhi|mumbai)\s+employees',
            r'(bangalore|kochi|gurgaon|pune|chennai|hyderabad|delhi|mumbai)\s+team',
            r'(bangalore|kochi|gurgaon|pune|chennai|hyderabad|delhi|mumbai)\s+developers',
            r'employees\s+in\s+(bangalore|kochi|gurgaon|pune|chennai|hyderabad|delhi|mumbai)'
        ]
        
        # Check for location keywords first
        for location in location_keywords:
            if location in query_lower:
                conditions['location'] = location.capitalize()
                break
        
        # If no location found via keywords, try patterns
        if not conditions['location']:
            for pattern in location_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    loc = match.group(1).capitalize()
                    conditions['location'] = loc
                    break
        
        # Build SQL query based on conditions
        sql_parts = []
        join_parts = []
        where_conditions = []
        
        # Handle deployment status conditions (FIXED - based on deployment column)
        deployment_conditions = []
        if conditions['free_pool']:
            deployment_conditions.append("e.deployment ILIKE '%free%'")
        if conditions['billable']:
            deployment_conditions.append("e.deployment ILIKE '%billable%'")
        if conditions['budgeted']:
            deployment_conditions.append("e.deployment ILIKE '%budgeted%'")
        if conditions['support']:
            deployment_conditions.append("e.deployment ILIKE '%support%'")
        
        if deployment_conditions:
            where_conditions.append(f"({' OR '.join(deployment_conditions)})")
        
        # Handle specific project condition
        if conditions['project']:
            join_parts.append("JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id")
            where_conditions.append(f"ep.project_name ILIKE '%{conditions['project']}%'")
        
        # Handle exact name matching (FIXED - precise matching)
        if conditions['exact_name']:
            # Use word boundaries for exact name matching
            where_conditions.append(f"(e.display_name ILIKE '% {conditions['exact_name']} %' OR e.display_name ILIKE '{conditions['exact_name']} %' OR e.display_name ILIKE '% {conditions['exact_name']}' OR e.display_name = '{conditions['exact_name']}')")
        
        # Handle skills condition
        if conditions['skills']:
            skill_conditions = []
            for skill in conditions['skills']:
                # Check both skill_set and tech_group fields
                skill_conditions.append(f"(e.skill_set ILIKE '%{skill}%' OR e.tech_group ILIKE '%{skill}%')")
            where_conditions.append(f"({' OR '.join(skill_conditions)})")
        
        # Handle department condition
        if conditions['department']:
            where_conditions.append(f"e.employee_department ILIKE '%{conditions['department']}%'")
        
        # Handle location condition
        if conditions['location']:
            where_conditions.append(f"e.emp_location ILIKE '%{conditions['location']}%'")
        
        # Handle experience conditions
        if conditions['experience_min'] is not None or conditions['experience_max'] is not None:
            # We'll handle experience filtering in post-processing since it requires parsing
            # For now, we'll select all and filter later
            pass
        
        # Build final SQL - Select ALL fields
        base_sql = "SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status"
        # Add project fields if we're joining projects table
        if join_parts:
            sql = f"""
            {base_sql}
            FROM hrms.employees e
            {' '.join(join_parts)}
            """
        else:
            sql = f"{base_sql} FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id"
        
        if where_conditions:
            sql += f" WHERE {' AND '.join(where_conditions)}"
        
        # Build vector search terms
        vector_terms = []
        if conditions['skills']:
            vector_terms.extend(conditions['skills'])
        if conditions['free_pool']:
            vector_terms.append("free pool")
        if conditions['billable']:
            vector_terms.append("billable")
        if conditions['budgeted']:
            vector_terms.append("budgeted")
        if conditions['support']:
            vector_terms.append("support")
        if conditions['project']:
            vector_terms.append(conditions['project'])
        if conditions['location']:
            vector_terms.append(conditions['location'])
        if conditions['experience_min']:
            vector_terms.append(f"{conditions['experience_min']} years experience")
        
        vector_search_terms = " ".join(vector_terms) if vector_terms else query
        
        reasoning_parts = []
        if conditions['free_pool']:
            reasoning_parts.append("free pool employees")
        if conditions['billable']:
            reasoning_parts.append("billable employees")
        if conditions['budgeted']:
            reasoning_parts.append("budgeted employees")
        if conditions['support']:
            reasoning_parts.append("support employees")
        if conditions['skills']:
            reasoning_parts.append(f"with {', '.join(conditions['skills'])} skills")
        if conditions['department']:
            reasoning_parts.append(f"in {conditions['department']} department")
        if conditions['location']:
            reasoning_parts.append(f"in {conditions['location']} location")
        if conditions['project']:
            reasoning_parts.append(f"working on {conditions['project']} project")
        if conditions['exact_name']:
            reasoning_parts.append(f"with exact name: {conditions['exact_name']}")
        if conditions['experience_min']:
            if conditions['experience_max']:
                reasoning_parts.append(f"with {conditions['experience_min']}-{conditions['experience_max']} years experience")
            else:
                reasoning_parts.append(f"with more than {conditions['experience_min']} years experience")
        elif conditions['experience_max']:
            reasoning_parts.append(f"with less than {conditions['experience_max']} years experience")
        
        reasoning = "Finding " + " and ".join(reasoning_parts) if reasoning_parts else "Complex multi-condition search"
        
        return {
            "action": "combined",
            "query_type": "multi_condition",
            "sql_query": sql,
            "vector_search_terms": vector_search_terms,
            "reasoning": reasoning,
            "detected_conditions": conditions
        }
        
    except Exception as e:
        logger.error(f"Multi-condition query error: {e}")
        return {
            "action": "combined",
            "query_type": "general",
            "sql_query": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10",
            "vector_search_terms": query,
            "reasoning": "Fallback for complex query"
        }

# -------------------------
# Enhanced LLM Router
# -------------------------
def enhanced_llm_route_query(query: str, llm) -> Dict[str, Any]:
    """
    Enhanced LLM router that understands specific HRMS queries better
    """
    try:
        query_lower = query.lower().strip()
        
        # Enhanced patterns for specific query types
        patterns = {
            # Single employee queries with exact name matching
            'single_employee': [
                r'show\s+details\s+of\s+([a-zA-Z\s]+)$',
                r'find\s+employee\s+([a-zA-Z\s]+)$',
                r'^([a-zA-Z\s]+)\s+details$',
                r'^employee\s+([a-zA-Z\s]+)$',
                r'^who\s+is\s+([a-zA-Z\s]+)$',
                r'^get\s+([a-zA-Z\s]+)\s+information$',
                r'^search\s+for\s+([a-zA-Z\s]+)$',
                r'^lookup\s+([a-zA-Z\s]+)$'
                r'^([a-zA-Z\s]+)$',
                r'^find\s+([a-zA-Z\s]+)$',
                r'^search\s+([a-zA-Z\s]+)$'
            ],
            
            # Deployment status queries (FIXED - based on deployment column)
            'free_pool': [
                r'^free\s+pool$',
                r'^freepool$',
                r'^who\s+are\s+in\s+free\s+pool$',
                r'^list\s+free\s+pool$',
                r'^employees\s+in\s+free\s+pool$',
                r'^free\s+employees$'
            ],
            
            'billable': [
                r'^billable$',
                r'^who\s+are\s+billable$',
                r'^billable\s+employees$'
            ],
            
            'budgeted': [
                r'^budgeted$',
                r'^budgeted\s+employees$'
            ],
            
            'support': [
                r'^support$',
                r'^support\s+employees$'
            ],
            
            # Experience queries
            'experience': [
                r'employees with (more than|greater than|over) (\d+) years experience',
                r'employees with (less than|under) (\d+) years experience',
                r'employees with (\d+)\s*\+\s*years experience',
                r'employees with (\d+) to (\d+) years experience',
                r'employees with (\d+) years experience',
                r'(\d+)\s*years?\s*experience'
            ],
            
            # Project-specific queries
            'project_specific': [
                r'who\s+all\s+are\s+there\s+in\s+(\w+)',
                r'employees\s+in\s+project\s+(\w+)',
                r'team\s+of\s+project\s+(\w+)',
                r'(\w+)\s+project\s+team',
                r'who\s+works\s+on\s+(\w+)',
                r'project\s+(\w+)\s+members',
                r'(\w+)\s+team\s+members'
            ],
            
            # Location queries
            'location': [
                r'^employees\s+in\s+(\w+)$',
                r'^(\w+)\s+employees$',
                r'^staff\s+in\s+(\w+)$',
                r'^team\s+in\s+(\w+)$',
                r'^who\s+is\s+in\s+(\w+)$'
            ],
            
            # Department queries
            'department': [
                r'^(\w+)\s+department$',
                r'^department\s+of\s+(\w+)$',
                r'^team\s+(\w+)$',
                r'^(\w+)\s+team$'
            ],
            
            # Skill queries
            'skills': [
                r'^employees\s+with\s+(\w+)\s+skills$',
                r'^who\s+knows\s+(\w+)$',
                r'^(\w+)\s+developers$',
                r'^(\w+)\s+experts$',
                r'^skilled\s+in\s+(\w+)$'
            ],
            
            # List all queries
            'list_all': [
                r'^list\s+all\s+employees$',
                r'^show\s+all\s+employees$',
                r'^get\s+all\s+employees$',
                r'^all\s+employees$',
                r'^every\s+employee$'
            ]
        }
        
        # Check for multi-condition queries FIRST (this is the key fix)
        multi_condition_indicators = [
            ' and ', ' with ', ' in ', ' developers', ' skills', ' freepool', ' free pool',
            ' python', ' java', ' docker', ' kubernetes', ' react', ' angular',
            ' show all ', ' bangalore ', ' kochi ', ' gurgaon ', ' pune ',
            ' cloud ', ' mobile ', ' quality ', ' devops ', ' years experience',
            ' more than ', ' less than ', ' greater than ', ' billable ', ' budgeted ', ' support '
        ]
        
        if any(indicator in query_lower for indicator in multi_condition_indicators):
            logger.info(f" Detected multi-condition query: {query}")
            return handle_multi_condition_query(query)
        
        # Check for experience queries
        for pattern in patterns['experience']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return handle_multi_condition_query(query)
        
        # Check for list all queries
        for pattern in patterns['list_all']:
            if re.search(pattern, query_lower):
                return {
                    "action": "sql_only",
                    "query_type": "list_all",
                    "sql_query": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id ORDER BY display_name",
                    "reasoning": "Retrieving complete list of all employees"
                }
        
        # Check for single employee queries with exact name matching (FIXED)
        for pattern in patterns['single_employee']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                employee_name = match.group(1).strip()
                # Exclude common stop words and ensure it's a meaningful name
                excluded_terms = ['all', 'free', 'pool', 'billable', 'budgeted', 'support', 'employees', 'employee']
                if (employee_name and 
                    len(employee_name) > 1 and 
                    employee_name.lower() not in excluded_terms):

                    name_parts = employee_name.split()
                    if len(name_parts) == 1:
                        # Single name - use word boundaries
                        name_condition = f"""
                        (e.display_name ILIKE '% {employee_name} %' 
                         OR e.display_name ILIKE '{employee_name} %' 
                         OR e.display_name ILIKE '% {employee_name}' 
                         OR e.display_name = '{employee_name}')
                        """
                    else:
                        # Multi-word name - match the full name with flexible patterns
                        name_condition = f"""
                        (e.display_name ILIKE '%{employee_name}%' 
                         OR e.display_name ILIKE '{employee_name}%' 
                         OR e.display_name ILIKE '%{employee_name}')
                         """
                    # Use exact name matching with word boundaries
                    return {
                        "action": "sql_only",
                        "query_type": "single_employee",
                        "sql_query": f"""
                        SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status 
                        FROM hrms.employees e 
                        LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id 
                        WHERE {name_condition}
                        """,
                        "reasoning": f"Searching for specific employee: {employee_name}"
                    }
        
        # Check for deployment status queries (FIXED - based on deployment column)
        for pattern in patterns['free_pool']:
            if re.search(pattern, query_lower):
                return {
                    "action": "sql_only", 
                    "query_type": "free_pool",
                    "sql_query": """
                    SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
                    FROM hrms.employees e
                    LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE e.deployment ILIKE '%free%'
                    """,
                    "reasoning": "Finding employees with free deployment status"
                }
        
        for pattern in patterns['billable']:
            if re.search(pattern, query_lower):
                return {
                    "action": "sql_only",
                    "query_type": "billable",
                    "sql_query": """
                    SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
                    FROM hrms.employees e
                    LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE e.deployment ILIKE '%billable%'
                    """,
                    "reasoning": "Finding employees with billable deployment status"
                }
        
        for pattern in patterns['budgeted']:
            if re.search(pattern, query_lower):
                return {
                    "action": "sql_only",
                    "query_type": "budgeted",
                    "sql_query": """
                    SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
                    FROM hrms.employees e
                    LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE e.deployment ILIKE '%budgeted%'
                    """,
                    "reasoning": "Finding employees with budgeted deployment status"
                }
        
        for pattern in patterns['support']:
            if re.search(pattern, query_lower):
                return {
                    "action": "sql_only",
                    "query_type": "support",
                    "sql_query": """
                    SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
                    FROM hrms.employees e
                    LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE e.deployment ILIKE '%support%'
                    """,
                    "reasoning": "Finding employees with support deployment status"
                }
        
        # Check for project-specific queries
        for pattern in patterns['project_specific']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                project_name = match.group(1)
                return {
                    "action": "sql_only",
                    "query_type": "project_specific", 
                    "sql_query": f"""
                    SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
                    FROM hrms.employees e
                    JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE ep.project_name ILIKE '%{project_name}%'
                    """,
                    "reasoning": f"Finding employees working on project: {project_name}"
                }
        
        # Check for simple location queries (only exact matches)
        for pattern in patterns['location']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                location = match.group(1)
                excluded_terms = ['all', 'free', 'pool', 'billable', 'budgeted', 'support', 'employees']
                if location.lower() not in excluded_terms:
                    return {
                        "action": "sql_only",
                        "query_type": "location",
                        "sql_query": f"SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE e.emp_location ILIKE '%{location}%'",
                        "reasoning": f"Finding employees in location: {location}"
                    }
        
        # Check for simple department queries (only exact matches)
        for pattern in patterns['department']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                department = match.group(1)
                excluded_terms = ['all', 'free', 'pool', 'billable', 'budgeted', 'support']
                if department.lower() not in excluded_terms:
                    return {
                        "action": "sql_only",
                        "query_type": "department",
                        "sql_query": f"SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE e.employee_department ILIKE '%{department}%'",
                        "reasoning": f"Finding employees in department: {department}"
                    }
        
        # Check for simple skill queries (only exact matches)
        for pattern in patterns['skills']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                skill = match.group(1)
                return {
                    "action": "combined",
                    "query_type": "skills",
                    "sql_query": f"SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE e.skill_set ILIKE '%{skill}%'",
                    "vector_search_terms": f"{skill} skills programming development expertise",
                    "reasoning": f"Finding employees with {skill} skills using both SQL and semantic search"
                }

        # Default fallback - use LLM for complex queries
        return use_llm_for_complex_query(query, llm)
        
    except Exception as e:
        logger.error(f"Enhanced routing error: {e}")
        return {
            "action": "combined",
            "query_type": "general",
            "sql_query": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10",
            "reasoning": "Fallback due to routing error"
        }

def use_llm_for_complex_query(query: str, llm) -> Dict[str, Any]:
    """
    Use LLM for complex queries that need natural language understanding
    """
    try:
        prompt = f"""
        Analyze this HRMS query and generate appropriate SQL and search strategy.
        
        QUERY: "{query}"
        
        AVAILABLE TABLES:
        - employees: employee_id, display_name, employee_department, emp_location, role, designation, skill_set, deployment, total_exp, etc.
        - employee_projects: project_name, customer, project_status, etc.
        
        IMPORTANT NOTES:
        - For employee name searches, use exact matching with word boundaries
        - Deployment status is stored in 'deployment' column (billable, budgeted, free, support)
        - Experience is stored in 'total_exp' column as string (e.g., '10 years', '5.5 years')
        
        COMMON QUERY PATTERNS:
        - Single employee: "show details of John", "find employee Sarah" (use exact name matching)
        - Deployment status: "free pool", "billable employees", "budgeted", "support" 
        - Experience: "employees with more than 10 years experience", "5+ years experience"
        - Projects: "team of INSU_PEGS", "employees in EXNI_CLRQ project"
        - Location: "employees in Kochi", "Gurgaon team"
        - Department: "Cloud department", "QA team"
        - Skills: "Java developers", "employees with Python skills"
        - List all: "list all employees", "show everyone"
        - Multi-condition: "freepool java developers", "python developers with 5+ years experience", "bangalore billable employees"
        
        Return JSON format:
        {{
            "action": "sql_only|vector_only|combined",
            "query_type": "single_employee|free_pool|billable|budgeted|support|experience|project|location|department|skills|list_all|multi_condition|general",
            "sql_query": "appropriate SQL query",
            "vector_search_terms": "terms for semantic search if needed",
            "reasoning": "explanation of approach"
        }}
        
        Return ONLY JSON:
        """
        
        response = llm.invoke(prompt)
        text_resp = response if isinstance(response, str) else getattr(response, "text", str(response))
        
        # Clean and parse JSON
        cleaned = re.sub(r'^```json\s*', '', text_resp.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        parsed = json.loads(cleaned)
        return parsed
        
    except Exception as e:
        logger.error(f"LLM complex query error: {e}")
        return {
            "action": "combined",
            "query_type": "general", 
            "sql_query": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10",
            "vector_search_terms": query,
            "reasoning": "LLM fallback"
        }

# -------------------------
# STEP 1: File Upload Processor with Transaction Support
# -------------------------
class HRMSDataProcessor:
    def __init__(self, db_engine, vector_store):
        self.engine = db_engine
        self.vector_store = vector_store
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def validate_file_format(self, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in self.supported_formats)
    
    def read_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Read CSV or Excel file into DataFrame"""
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format")
            
            # Clean column names and handle missing values
            df = df.fillna('')
            df.columns = [col.strip().lower() for col in df.columns]
            
            logger.info(f" File read successfully: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f" Columns: {list(df.columns)}")
            logger.info(f" First 3 rows sample: {df.head(3).to_dict('records')}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise ValueError(f"Could not read file: {str(e)}")
    
    def clear_existing_data(self):
        """Clear all existing data from database and vector store"""
        try:
            with self.engine.connect() as conn:
                # Start transaction
                trans = conn.begin()
                
                try:
                    # Delete all data from employee_projects table
                    result_projects = conn.execute(text("DELETE FROM hrms.employee_projects"))
                    logger.info(f" Cleared hrms.employee_projects table: {result_projects.rowcount} rows")
                    
                    # Delete all data from employees table
                    result_employees = conn.execute(text("DELETE FROM hrms.employees"))
                    logger.info(f" Cleared hrms.employees table: {result_employees.rowcount} rows")
                    
                    # Commit the transaction
                    trans.commit()
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                
            # Clear Chroma vector DB
            try:
                # Get all collection IDs and delete them
                collections = self.vector_store._client.list_collections()
                for collection in collections:
                    self.vector_store._client.delete_collection(collection.name)
                
                # Reinitialize the vector store
                self.vector_store = Chroma(persist_directory=VECTOR_PERSIST_DIR, embedding_function=embeddings)
                logger.info(" Cleared Chroma vector database")
                
            except Exception as e:
                logger.error(f"Error clearing vector store: {e}")
                # Continue even if vector store clearing fails
                
        except Exception as e:
            logger.error(f"Error clearing existing data: {e}")
            raise
    
    def process_to_database(self, df: pd.DataFrame) -> int:
        """STEP 1A: Structured Data Extraction → PostgreSQL Database - FIXED VERSION"""
        try:
            employee_records = {}
            project_records = []
            
            # Debug: Print column names and first few rows
            logger.info(f" Processing DataFrame with {len(df)} rows")
            logger.info(f" DataFrame columns: {list(df.columns)}")
            
            for index, row in df.iterrows():
                employee_id = row.get('employee_id')
                if not employee_id:
                    logger.warning(f" Row {index} has no employee_id, skipping")
                    continue
                
                # Convert employee_id to string and clean it
                employee_id = str(employee_id).strip()
                if not employee_id:
                    logger.warning(f" Row {index} has empty employee_id, skipping")
                    continue
                
                # Store employee record - only once per employee_id
                if employee_id not in employee_records:
                    try:
                        # Handle occupancy conversion safely
                        occupancy_raw = row.get('occupancy', 0)
                        try:
                            if pd.isna(occupancy_raw) or occupancy_raw == '':
                                occupancy = 0
                            else:
                                occupancy = int(float(str(occupancy_raw)))
                        except (ValueError, TypeError):
                            occupancy = 0
                        
                        employee_data = {
                            'employee_id': employee_id,
                            'display_name': str(row.get('display_name', '')).strip(),
                            'employee_ou_type': str(row.get('employee_ou_type', '')).strip(),
                            'employee_department': str(row.get('employee_department', '')).strip(),
                            'delivery_owner_emp_id': str(row.get('delivery_owner_emp_id', '')).strip(),
                            'delivery_owner': str(row.get('delivery_owner', '')).strip(),
                            'joined_date': str(row.get('joined_date', '')).strip(),
                            'role': str(row.get('role', '')).strip(),
                            'deployment': str(row.get('deployment', '')).strip(),
                            'occupancy': occupancy,
                            'created_by_employee_id': str(row.get('created_by_employee_id', '')).strip(),
                            'created_by_display_name': str(row.get('created_by_display_name', '')).strip(),
                            'pm': str(row.get('pm', '')).strip(),
                            'total_exp': str(row.get('total_exp', '')).strip(),
                            'vvdn_exp': str(row.get('vvdn_exp', '')).strip(),
                            'designation': str(row.get('designation', '')).strip(),
                            'sub_department': str(row.get('sub_department', '')).strip(),
                            'tech_group': str(row.get('tech_group', '')).strip(),
                            'emp_location': str(row.get('emp_location', '')).strip(),
                            'rm_id': str(row.get('rm_id', '')).strip(),
                            'rm_name': str(row.get('rm_name', '')).strip(),
                            'skill_set': str(row.get('skill_set', '')).strip()
                        }
                        employee_records[employee_id] = employee_data
                        logger.info(f" Added employee record: {employee_id} - {employee_data['display_name']}")
                    except Exception as emp_error:
                        logger.error(f" Error processing employee {employee_id} at row {index}: {emp_error}")
                        continue
                
                # Store project record for each project entry
                project_name = row.get('project')
                if project_name and str(project_name).strip():
                    try:
                        project_data = {
                            'employee_id': employee_id,
                            'project_name': str(project_name).strip(),
                            'customer': str(row.get('customer', '')).strip(),
                            'project_department': str(row.get('project_department', '')).strip(),
                            'project_industry': str(row.get('project_industry', '')).strip(),
                            'project_status': str(row.get('project_status', '')).strip()
                        }
                        project_records.append(project_data)
                        logger.info(f" Added project record: {project_data['project_name']} for employee: {employee_id}")
                    except Exception as proj_error:
                        logger.error(f" Error processing project for {employee_id} at row {index}: {proj_error}")
                        continue
            
            inserted_employees = 0
            inserted_projects = 0
            
            logger.info(f" Starting database insertion: {len(employee_records)} employees, {len(project_records)} projects")
            
            # Use separate transactions for employees and projects to avoid transaction aborts
            with self.engine.connect() as conn:
                # Insert employees in one transaction
                try:
                    trans = conn.begin()
                    for employee_id, employee_data in employee_records.items():
                        try:
                            columns = list(employee_data.keys())
                            values = [f":{col}" for col in columns]
                            params = employee_data
                            
                            sql = f"""
                            INSERT INTO hrms.employees ({', '.join(columns)})
                            VALUES ({', '.join(values)})
                            """
                            
                            result = conn.execute(text(sql), params)
                            inserted_employees += 1
                            logger.info(f" Inserted employee into DB: {employee_id}")
                            
                        except Exception as row_error:
                            logger.error(f" Error inserting employee {employee_id}: {row_error}")
                            # Continue with next employee even if one fails
                            continue
                    
                    trans.commit()
                    logger.info(f" Successfully inserted {inserted_employees} employees")
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f" Employee insertion failed, rolling back: {e}")
                    # Don't re-raise, continue to try projects
            
            # Insert projects in separate transaction
            with self.engine.connect() as conn:
                try:
                    trans = conn.begin()
                    for project_data in project_records:
                        try:
                            # Use INSERT with ON CONFLICT to handle duplicates gracefully
                            sql = """
                            INSERT INTO hrms.employee_projects (
                                employee_id, project_name, customer, project_department, 
                                project_industry, project_status
                            )
                            VALUES (:employee_id, :project_name, :customer, :project_department, 
                                    :project_industry, :project_status)
                            ON CONFLICT (employee_id, project_name) DO NOTHING
                            """
                            
                            result = conn.execute(text(sql), project_data)
                            if result.rowcount > 0:
                                inserted_projects += 1
                                logger.info(f" Inserted project into DB: {project_data['project_name']} for {project_data['employee_id']}")
                            else:
                                logger.info(f"  Project already exists, skipped: {project_data['project_name']} for {project_data['employee_id']}")
                            
                        except Exception as project_error:
                            logger.error(f" Error inserting project for {project_data['employee_id']}: {project_error}")
                            # Continue with next project even if one fails
                            continue
                    
                    trans.commit()
                    logger.info(f"✅ Successfully inserted {inserted_projects} projects")
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f" Project insertion failed, rolling back: {e}")
                    # Don't re-raise, we still want to continue with vector store
            
            logger.info(f" Database Processing COMPLETED:")
            logger.info(f"   - Unique employees found: {len(employee_records)}")
            logger.info(f"   - Employees inserted: {inserted_employees}")
            logger.info(f"   - Projects to insert: {len(project_records)}")
            logger.info(f"   - Projects inserted: {inserted_projects}")
            
            return inserted_employees + inserted_projects
            
        except Exception as e:
            logger.error(f" Database processing error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def process_to_vector_store(self, df: pd.DataFrame) -> int:
        """STEP 1B: Document Embeddings Generation → ChromaDB Vector Store"""
        try:
            documents = []
            
            # Group by employee to create comprehensive documents
            employee_groups = df.groupby('employee_id')
            
            logger.info(f" Creating vector documents from {len(employee_groups)} employee groups")
            
            for employee_id, group in employee_groups:
                employee_data = group.iloc[0]
                
                # Create comprehensive content with all projects
                content_parts = [
                    f"Employee: {employee_data.get('display_name', '')}",
                    f"ID: {employee_id}",
                    f"Department: {employee_data.get('employee_department', '')}",
                    f"Role: {employee_data.get('role', '')}",
                    f"Designation: {employee_data.get('designation', '')}",
                    f"Location: {employee_data.get('emp_location', '')}",
                    f"Total Experience: {employee_data.get('total_exp', '')}",
                    f"VVDN Experience: {employee_data.get('vvdn_exp', '')}",
                    f"Skills: {employee_data.get('skill_set', '')}",
                    f"Tech Group: {employee_data.get('tech_group', '')}",
                    f"OU Type: {employee_data.get('employee_ou_type', '')}",
                    f"Sub Department: {employee_data.get('sub_department', '')}",
                    f"RM: {employee_data.get('rm_name', '')}",
                    f"Deployment Status: {employee_data.get('deployment', '')}"
                ]
                
                # Add project information
                projects_info = []
                for _, project_row in group.iterrows():
                    project_name = project_row.get('project')
                    if project_name and str(project_name).strip():
                        project_text = f"Project: {project_name} - {project_row.get('customer', '')} ({project_row.get('project_status', '')}) - {project_row.get('project_department', '')} - {project_row.get('project_industry', '')}"
                        projects_info.append(project_text)
            
                if projects_info:
                    content_parts.append("Projects: " + "; ".join(projects_info))
                
                # Filter out empty parts and join
                filtered_parts = [part for part in content_parts if part.split(": ")[1] and part.split(": ")[1].strip()]
                content = ". ".join(filtered_parts)
            
                if not content.strip():
                    logger.warning(f" Empty content for employee {employee_id}, skipping")
                    continue
                
                # Create comprehensive metadata (with proper filtering)
                raw_metadata = {
                    "document_type": "employee",
                    "source": "csv_upload",
                    "employee_id": str(employee_id),
                    "display_name": str(employee_data.get('display_name', '')),
                    "employee_ou_type": str(employee_data.get('employee_ou_type', '')),
                    "employee_department": str(employee_data.get('employee_department', '')),
                    "project_name": str(employee_data.get('project', '')),
                    "customer": str(employee_data.get('customer', '')),
                    "project_department": str(employee_data.get('project_department', '')),
                    "project_industry": str(employee_data.get('project_industry', '')),
                    "project_status": str(employee_data.get('project_status', '')),
                    "delivery_owner_emp_id": str(employee_data.get('delivery_owner_emp_id', '')),
                    "delivery_owner": str(employee_data.get('delivery_owner', '')),
                    "joined_date": str(employee_data.get('joined_date', '')),
                    "role": str(employee_data.get('role', '')),
                    "deployment": str(employee_data.get('deployment', '')),
                    "occupancy": str(employee_data.get('occupancy', '')),
                    "created_by_employee_id": str(employee_data.get('created_by_employee_id', '')),
                    "created_by_display_name": str(employee_data.get('created_by_display_name', '')),
                    "pm": str(employee_data.get('pm', '')),
                    "total_exp": str(employee_data.get('total_exp', '')),
                    "vvdn_exp": str(employee_data.get('vvdn_exp', '')),
                    "designation": str(employee_data.get('designation', '')),
                    "sub_department": str(employee_data.get('sub_department', '')),
                    "tech_group": str(employee_data.get('tech_group', '')),
                    "emp_location": str(employee_data.get('emp_location', '')),
                    "rm_id": str(employee_data.get('rm_id', '')),
                    "rm_name": str(employee_data.get('rm_name', '')),
                    "skill_set": str(employee_data.get('skill_set', '')),
                    "project_count": int(len(group)),
                    "projects": str([str(p) for p in group['project'].unique() if p and str(p).strip()])
                }
                
                # Filter metadata to ensure only simple types
                filtered_metadata = filter_complex_metadata(raw_metadata)
                
                documents.append(Document(page_content=content, metadata=filtered_metadata))
                logger.info(f" Created vector document for employee: {employee_id}")
            
            # Add to vector store in batches to avoid memory issues
            if documents:
                logger.info(f" Adding {len(documents)} documents to vector store...")
                
                # Process in smaller batches
                batch_size = 50
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    self.vector_store.add_documents(batch)
                    logger.info(f" Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
                
                # Note: Chroma 0.4.x+ automatically persists, so we don't need to call persist()
                logger.info(f" Document Embeddings: {len(documents)} documents added to ChromaDB")
            else:
                logger.warning(" No documents to add to vector store")
            
            return len(documents)
            
        except Exception as e:
            logger.error(f" Vector store processing error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def process_upload_transaction(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Main processing method with transaction support - replaces all existing data"""
        try:
            # Read file
            df = self.read_file(file_content, filename)
            logger.info(f" File Upload: Read {len(df)} rows from {filename}")
            
            # Start DB transaction - Clear all existing data
            logger.info(" Starting transaction: Clearing existing data...")
            self.clear_existing_data()
            
            # Process new data to database
            logger.info(" Processing new data to database...")
            db_records = self.process_to_database(df)
            
            # Process new data to vector store
            logger.info(" Processing new data to vector store...")
            vector_docs = self.process_to_vector_store(df)
            
            # Get all employees with their projects for response
            logger.info(" Building comprehensive employee response...")
            all_employees = get_all_employees_with_projects()
            
            # Transaction completed successfully
            logger.info(" Transaction completed successfully")
            
            return {
                "status": "success",
                "message": f"Successfully replaced all data with new file: {filename}",
                "records_processed": len(df),
                "database_records": db_records,
                "vector_documents": vector_docs,
                "file_metadata": {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "columns_list": list(df.columns)
                },
                "all_employees": all_employees
            }
            
        except Exception as e:
            logger.error(f" Upload processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "records_processed": 0,
                "database_records": 0,
                "vector_documents": 0,
                "file_metadata": {},
                "all_employees": []
            }

# Initialize the processor
hrms_processor = HRMSDataProcessor(engine, vector_store)

# -------------------------
# Enhanced SQL Query Executor with Experience Filtering
# -------------------------
class EnhancedSQLQueryExecutor:
    def __init__(self, db_engine):
        self.engine = db_engine
    
    def execute_enhanced_query(self, routing_decision: Dict[str, Any]) -> List[Dict]:
        """Execute SQL queries based on enhanced routing decisions with experience filtering"""
        try:
            sql_query = routing_decision.get("sql_query")
            query_type = routing_decision.get("query_type", "general")
            conditions = routing_decision.get("detected_conditions", {})
            
            if not sql_query:
                # Generate fallback query based on type
                sql_query = self.generate_fallback_query(query_type)
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = []
                for row in result:
                    if hasattr(row, '_mapping'):
                        rows.append(dict(row._mapping))
                    else:
                        row_dict = {}
                        for idx, col in enumerate(result.keys()):
                            row_dict[col] = row[idx]
                        rows.append(row_dict)
                
                # Apply experience filtering if needed
                if conditions.get('experience_min') is not None or conditions.get('experience_max') is not None:
                    rows = self.filter_by_experience(rows, conditions)
                
                logger.info(f" Enhanced SQL Query ({query_type}): Retrieved {len(rows)} records")
                return rows
                
        except Exception as e:
            logger.error(f"Enhanced SQL execution error: {e}")
            return []
    
    def filter_by_experience(self, rows: List[Dict], conditions: Dict) -> List[Dict]:
        """Filter rows based on experience conditions"""
        filtered_rows = []
        
        for row in rows:
            exp_string = row.get('total_exp', '')
            exp_years = parse_experience_years(exp_string)
            
            include = True
            
            # Check minimum experience
            if conditions.get('experience_min') is not None:
                if exp_years < conditions['experience_min']:
                    include = False
            
            # Check maximum experience  
            if conditions.get('experience_max') is not None:
                if exp_years > conditions['experience_max']:
                    include = False
            
            if include:
                # Add parsed experience for display
                row['parsed_experience'] = exp_years
                filtered_rows.append(row)
        
        return filtered_rows
    
    def generate_fallback_query(self, query_type: str) -> str:
        """Generate appropriate fallback queries based on query type"""
        fallback_queries = {
            "single_employee": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 5",
            "free_pool": """
            SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
            FROM hrms.employees e
            LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.deployment ILIKE '%free%'
            LIMIT 20
            """,
            "billable": """
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
            FROM hrms.employees e  
            LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.deployment ILIKE '%billable%'
            LIMIT 20
            """,
            "budgeted": """
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
            FROM hrms.employees e  
            LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.deployment ILIKE '%budgeted%'
            LIMIT 20
            """,
            "support": """
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
            FROM hrms.employees e  
            LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.deployment ILIKE '%support%'
            LIMIT 20
            """,
            "project_specific": """
            SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status
            FROM hrms.employees e
            JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id
            WHERE ep.project_name IS NOT NULL
            LIMIT 15
            """,
            "location": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE emp_location IS NOT NULL LIMIT 15",
            "department": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE employee_department IS NOT NULL LIMIT 15",
            "skills": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE skill_set IS NOT NULL LIMIT 15",
            "experience": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id WHERE total_exp IS NOT NULL LIMIT 15",
            "list_all": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id ORDER BY display_name LIMIT 50",
            "multi_condition": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10",
            "general": "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10"
        }
    
        return fallback_queries.get(query_type, "SELECT e.*, ep.project_name, ep.customer, ep.project_department, ep.project_industry, ep.project_status FROM hrms.employees e LEFT JOIN hrms.employee_projects ep ON e.employee_id = ep.employee_id LIMIT 10")

# Initialize SQL Executor
sql_executor = EnhancedSQLQueryExecutor(engine)

# -------------------------
# STEP 3B: Vector Search
# -------------------------
class VectorSearch:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """STEP 3B: Vector Search for document content"""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            hits = []
            for doc, score in results:
                similarity = 1 - score
                
                hits.append({
                    "document_type": doc.metadata.get("document_type", "unknown"),
                    "employee_id": doc.metadata.get("employee_id"),
                    "display_name": doc.metadata.get("display_name", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": float(similarity)
                })
            
            logger.info(f" Vector Search: Found {len(hits)} relevant documents")
            return hits
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

# Initialize Vector Search
vector_searcher = VectorSearch(vector_store)

# -------------------------
# STEP 4: Results Fusion
# -------------------------
class ResultsFuser:
    def __init__(self):
        pass
    
    def fuse_results(self, sql_results: List[Dict], vector_results: List[Dict], query: str) -> Dict[str, Any]:
        """STEP 4: Results Fusion → Unified Response"""
        try:
            unified_results = []
            seen_employees = set()
            
            # Add SQL results (structured data)
            for result in sql_results:
                employee_id = result.get('employee_id')
                if employee_id and employee_id not in seen_employees:
                    unified_results.append({
                        "type": "structured",
                        "employee_id": employee_id,
                        "display_name": result.get('display_name', ''),
                        "employee_ou_type": result.get('employee_ou_type', ''),
                        "employee_department": result.get('employee_department', ''),
                        "project": result.get('project_name', ''),
                        "customer": result.get('customer', ''),
                        "project_department": result.get('project_department', ''),
                        "project_industry": result.get('project_industry', ''),
                        "project_status": result.get('project_status', ''),
                        "delivery_owner_emp_id": result.get('delivery_owner_emp_id', ''),
                        "delivery_owner": result.get('delivery_owner', ''),
                        "joined_date": result.get('joined_date', ''),
                        "role": result.get('role', ''),
                        "deployment": result.get('deployment', ''),
                        "occupancy": result.get('occupancy', ''),
                        "created_by_employee_id": result.get('created_by_employee_id', ''),
                        "created_by_display_name": result.get('created_by_display_name', ''),
                        "pm": result.get('pm', ''),
                        "total_exp": result.get('total_exp', ''),
                        "vvdn_exp": result.get('vvdn_exp', ''),
                        "designation": result.get('designation', ''),
                        "sub_department": result.get('sub_department', ''),
                        "tech_group": result.get('tech_group', ''),
                        "emp_location": result.get('emp_location', ''),
                        "rm_id": result.get('rm_id', ''),
                        "rm_name": result.get('rm_name', ''),
                        "skill_set": result.get('skill_set', ''),
                        "parsed_experience": result.get('parsed_experience'),
                        "score": 1.0,
                        "source": "sql"
                    })
                    seen_employees.add(employee_id)
            
            # Add vector results (semantic matches)
            for result in vector_results:
                employee_id = result.get("employee_id")
                if employee_id and employee_id not in seen_employees:
                    unified_results.append({
                        "type": "semantic", 
                        "employee_id": employee_id,
                        "display_name": result.get("display_name", ""),
                        "employee_ou_type": result["metadata"].get("employee_ou_type", ""),
                        "employee_department": result["metadata"].get("employee_department", ""),
                        "project": result["metadata"].get("project_name", ""),
                        "customer": result["metadata"].get("customer", ""),
                        "project_department": result["metadata"].get("project_department", ""),
                        "project_industry": result["metadata"].get("project_industry", ""),
                        "project_status": result["metadata"].get("project_status", ""),
                        "delivery_owner_emp_id": result["metadata"].get("delivery_owner_emp_id", ""),
                        "delivery_owner": result["metadata"].get("delivery_owner", ""),
                        "joined_date": result["metadata"].get("joined_date", ""),
                        "role": result["metadata"].get("role", ""),
                        "deployment": result["metadata"].get("deployment", ""),
                        "occupancy": result["metadata"].get("occupancy", ""),
                        "created_by_employee_id": result["metadata"].get("created_by_employee_id", ""),
                        "created_by_display_name": result["metadata"].get("created_by_display_name", ""),
                        "pm": result["metadata"].get("pm", ""),
                        "total_exp": result["metadata"].get("total_exp", ""),
                        "vvdn_exp": result["metadata"].get("vvdn_exp", ""),
                        "designation": result["metadata"].get("designation", ""),
                        "sub_department": result["metadata"].get("sub_department", ""),
                        "tech_group": result["metadata"].get("tech_group", ""),
                        "emp_location": result["metadata"].get("emp_location", ""),
                        "rm_id": result["metadata"].get("rm_id", ""),
                        "rm_name": result["metadata"].get("rm_name", ""),
                        "skill_set": result["metadata"].get("skill_set", ""),
                        "score": result.get("similarity", 0.5),
                        "source": "vector"
                    })
                    seen_employees.add(employee_id)
            
            # Sort by score
            unified_results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f" Results Fusion: Created {len(unified_results)} unified results")
            
            return {
                "unified_results": unified_results,
                "total_count": len(unified_results),
                "sql_count": len(sql_results),
                "vector_count": len(vector_results),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Results fusion error: {e}")
            return {
                "unified_results": [],
                "total_count": 0,
                "sql_count": 0, 
                "vector_count": 0,
                "query": query,
                "error": str(e)
            }

# Initialize Results Fuser
results_fuser = ResultsFuser()

# -------------------------
# Main Search Orchestrator
# -------------------------
class HRMSSearchOrchestrator:
    def __init__(self, sql_executor, vector_searcher, results_fuser, llm):
        self.sql_executor = sql_executor
        self.vector_searcher = vector_searcher
        self.results_fuser = results_fuser
        self.llm = llm
    
    def process_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Orchestrate the complete search pipeline"""
        logger.info(f" Processing query: '{query}'")
        
        # STEP 2: Enhanced LLM Router
        routing_decision = enhanced_llm_route_query(query, self.llm)
        action = routing_decision.get("action", "combined")
        query_type = routing_decision.get("query_type", "general")
        
        sql_results = []
        vector_results = []
        
        # STEP 3A: Enhanced SQL Queries
        if action in ["sql_only", "combined"]:
            sql_results = self.sql_executor.execute_enhanced_query(routing_decision)
        
        # STEP 3B: Vector Search
        if action in ["vector_only", "combined"]:
            search_terms = routing_decision.get("vector_search_terms", query)
            vector_results = self.vector_searcher.semantic_search(search_terms, top_k=top_k)
        
        # STEP 4: Results Fusion
        fused_results = self.results_fuser.fuse_results(sql_results, vector_results, query)
        
        response = {
            "query": query,
            "query_type": query_type,
            "routing_decision": routing_decision,
            "results": fused_results,
            "summary": {
                "total_employees_found": fused_results["total_count"],
                "search_strategy": action,
                "query_category": query_type,
                "sql_results_count": len(sql_results),
                "vector_results_count": len(vector_results)
            }
        }
        
        logger.info(f" Search completed ({query_type}): Found {fused_results['total_count']} employees")
        return response

# Initialize Orchestrator
search_orchestrator = HRMSSearchOrchestrator(sql_executor, vector_searcher, results_fuser, llm)

# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(
    title="HRMS AI Chatbot - Enhanced Architecture",
    description="Complete implementation with enhanced LLM routing and query understanding",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "HRMS AI Chatbot with Enhanced Architecture is running!",
        "architecture": [
            "1. File Upload → Structured Data + Vector Embeddings",
            "2. User Query → Enhanced LLM Router", 
            "3. SQL Queries + Vector Search",
            "4. Results Fusion → Unified Response"
        ],
        "features": [
            "Single employee search with exact name matching",
            "Deployment status filtering (billable, budgeted, free, support)", 
            "Experience-based filtering (years of experience)",
            "Project-specific team queries",
            "Location-based filtering",
            "Department-wise searches",
            "Skill-based matching",
            "Multi-condition queries"
        ],
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /upload/hrms-data",
            "search": "POST /search",
            "stats": "GET /stats",
            "init-database": "POST /init-database",
            "debug-data": "GET /debug-data"
        }
    }

@app.get("/health")
def health_check():
    """Health check that handles missing tables gracefully"""
    try:
        with engine.connect() as conn:
            # Check if schema exists
            schema_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.schemata 
                    WHERE schema_name = 'hrms'
                )
            """)).scalar()
            
            if schema_exists:
                # Check if tables exist
                employees_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'hrms' 
                        AND table_name = 'employees'
                    )
                """)).scalar()
                
                projects_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'hrms' 
                        AND table_name = 'employee_projects'
                    )
                """)).scalar()
                
                if employees_exists and projects_exists:
                    employee_count = conn.execute(text("SELECT COUNT(*) FROM hrms.employees")).scalar()
                    project_count = conn.execute(text("SELECT COUNT(*) FROM hrms.employee_projects")).scalar()
                else:
                    employee_count = 0
                    project_count = 0
                
                tables_created = employees_exists and projects_exists
            else:
                employee_count = 0
                project_count = 0
                tables_created = False
        
        return {
            "status": "healthy",
            "database_connected": True,
            "tables_created": tables_created,
            "employees_in_db": employee_count,
            "projects_in_db": project_count,
            "vector_store": "ChromaDB",
            "llm": OLLAMA_MODEL
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "database_connected": False,
            "tables_created": False
        }

@app.post("/init-database")
def initialize_database():
    """Initialize database tables and clean up duplicates"""
    try:
        # Clean up any existing duplicates first
        cleanup_duplicate_projects()
        
        # Setup database with proper error handling
        setup_database()
        
        return {
            "status": "success",
            "message": "Database initialized successfully",
            "tables_created": True
        }
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

@app.get("/stats")
def get_system_stats():
    """Get system statistics"""
    try:
        with engine.connect() as conn:
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'hrms' 
                    AND table_name = 'employees'
                )
            """)).scalar()
            
            if table_exists:
                employee_count = conn.execute(text("SELECT COUNT(*) FROM hrms.employees")).scalar()
                project_count = conn.execute(text("SELECT COUNT(*) FROM hrms.employee_projects")).scalar()
                
                # Department stats
                dept_stats = conn.execute(text("""
                    SELECT employee_department, COUNT(*) as count 
                    FROM hrms.employees 
                    GROUP BY employee_department
                """)).fetchall()
                
                # Location stats
                location_stats = conn.execute(text("""
                    SELECT emp_location, COUNT(*) as count 
                    FROM hrms.employees 
                    GROUP BY emp_location
                """)).fetchall()
                
                # Deployment stats
                deployment_stats = conn.execute(text("""
                    SELECT deployment, COUNT(*) as count 
                    FROM hrms.employees 
                    GROUP BY deployment
                """)).fetchall()
                
                stats = {
                    "total_employees": employee_count,
                    "total_projects": project_count,
                    "department_distribution": {dept: count for dept, count in dept_stats},
                    "location_distribution": {loc: count for loc, count in location_stats},
                    "deployment_distribution": {deploy: count for deploy, count in deployment_stats}
                }
            else:
                stats = {
                    "total_employees": 0,
                    "total_projects": 0,
                    "department_distribution": {},
                    "location_distribution": {},
                    "deployment_distribution": {},
                    "message": "No data uploaded yet"
                }
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug-data")
def debug_data():
    """Debug endpoint to check what data exists"""
    try:
        with engine.connect() as conn:
            # Get all employees with projects
            all_employees = get_all_employees_with_projects()
            
            return {
                "employees_count": len(all_employees),
                "projects_count": sum(len(emp.get('projects', [])) for emp in all_employees),
                "all_employees": all_employees
            }
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload/hrms-data")
async def upload_hrms_data(
    file: UploadFile = File(...),
    description: str = Form("")
):
    """STEP 1: File Upload Endpoint with Transaction Support"""
    try:
        # Ensure tables exist before upload (with better error handling)
        try:
            setup_database()
        except Exception as db_error:
            logger.warning(f"Database setup had issues but continuing: {db_error}")
        
        if not hrms_processor.validate_file_format(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Use transaction-based processing that replaces all data
        result = hrms_processor.process_upload_transaction(file_content, file.filename)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return comprehensive response including all employees data
        return UploadResponse(
            status="success",
            message=result["message"],
            records_processed=result["records_processed"],
            database_records=result["database_records"],
            vector_documents=result["vector_documents"],
            file_metadata=result["file_metadata"],
            all_employees=result["all_employees"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search_endpoint(req: ChatRequest):
    """Complete Search Pipeline Endpoint"""
    try:
        # Ensure tables exist before search
        setup_database()
        
        result = search_orchestrator.process_query(req.query, req.top_k or 5)
        
        # Build appropriate response based on query type
        response_text = build_response_text(result)
        
        return ChatResponse(
            action="search",
            response=response_text,
            data=result,
            ui_suggestions=build_ui_suggestions(result),
            search_metadata={
                "search_type": req.search_type or "combined",
                "routing_strategy": result['routing_decision']['action'],
                "query_category": result['query_type'],
                "results_count": result['summary']['total_employees_found']
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def build_response_text(result: Dict) -> str:
    """Build appropriate response text based on query type and results"""
    query_type = result.get('query_type', 'general')
    total_count = result['summary']['total_employees_found']
    
    responses = {
        'single_employee': f"Found employee details" if total_count > 0 else "No employee found with that exact name",
        'free_pool': f"Found {total_count} employees with free deployment status" if total_count > 0 else "No employees found with free deployment status",
        'billable': f"Found {total_count} employees with billable deployment status" if total_count > 0 else "No employees found with billable deployment status",
        'budgeted': f"Found {total_count} employees with budgeted deployment status" if total_count > 0 else "No employees found with budgeted deployment status",
        'support': f"Found {total_count} employees with support deployment status" if total_count > 0 else "No employees found with support deployment status",
        'experience': f"Found {total_count} employees matching experience criteria" if total_count > 0 else "No employees found matching experience criteria",
        'project_specific': f"Found {total_count} employees working on this project" if total_count > 0 else "No employees found for this project",
        'location': f"Found {total_count} employees in this location" if total_count > 0 else "No employees found in this location",
        'department': f"Found {total_count} employees in this department" if total_count > 0 else "No employees found in this department",
        'skills': f"Found {total_count} employees with matching skills" if total_count > 0 else "No employees found with these skills",
        'list_all': f"Found {total_count} employees in total",
        'multi_condition': f"Found {total_count} employees matching your criteria",
        'general': f"Found {total_count} employees matching your query"
    }
    
    return responses.get(query_type, f"Found {total_count} employees matching your query")

def build_ui_suggestions(result: Dict) -> List[Dict[str, Any]]:
    """Build UI suggestions based on search results and query type"""
    suggestions = []
    query_type = result.get('query_type', 'general')
    total_count = result['summary']['total_employees_found']
    
    if total_count > 0:
        suggestions.extend([
            {"type": "view_employees", "title": "View Employees"},
            {"type": "export_data", "title": "Export Results"}
        ])
    
    # Query-type specific suggestions
    type_suggestions = {
        'single_employee': [
            {"type": "contact_info", "title": "Contact Information"},
            {"type": "project_history", "title": "Project History"}
        ],
        'free_pool': [
            {"type": "assign_project", "title": "Assign to Project"},
            {"type": "skill_analysis", "title": "Analyze Skills"}
        ],
        'billable': [
            {"type": "project_details", "title": "Project Details"},
            {"type": "utilization", "title": "View Utilization"}
        ],
        'budgeted': [
            {"type": "budget_analysis", "title": "Budget Analysis"},
            {"type": "resource_planning", "title": "Resource Planning"}
        ],
        'support': [
            {"type": "support_tickets", "title": "Support Tickets"},
            {"type": "workload_analysis", "title": "Workload Analysis"}
        ],
        'experience': [
            {"type": "experience_analysis", "title": "Experience Analysis"},
            {"type": "seniority_report", "title": "Seniority Report"}
        ],
        'project_specific': [
            {"type": "project_overview", "title": "Project Overview"},
            {"type": "team_structure", "title": "Team Structure"}
        ],
        'skills': [
            {"type": "skill_gap", "title": "Skill Gap Analysis"},
            {"type": "training", "title": "Training Recommendations"}
        ],
        'location': [
            {"type": "location_map", "title": "View on Map"},
            {"type": "local_contacts", "title": "Local Contacts"}
        ],
        'multi_condition': [
            {"type": "advanced_filter", "title": "Advanced Filters"},
            {"type": "skill_matrix", "title": "Skill Matrix"},
            {"type": "project_analysis", "title": "Project Analysis"}
        ]
    }
    
    suggestions.extend(type_suggestions.get(query_type, []))
    
    return suggestions

# -------------------------
# Run the application
# -------------------------
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting HRMS AI Chatbot with Enhanced Architecture...")
    
    # Initialize database on startup
    setup_database()
    logger.info("Database setup completed")
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    