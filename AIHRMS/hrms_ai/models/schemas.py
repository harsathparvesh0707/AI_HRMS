"""
Pydantic models for request/response schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date


class LLMResponse(BaseModel):
    sql: str
    fields: List[str]
    ui_actions: List[str]
    chat_response: str
    confidence: float = 0.8
    query_type: str = "general"
    search_strategy: str = "hybrid"  # "sql_only", "vector_only", "hybrid"


class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    search_type: Optional[str] = "combined"
    user_id: Optional[str] = "anonymous"

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    search_type: Optional[str] = "combined"


class QueryRequest(BaseModel):
    query: str
    required_skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    max_results: Optional[int] = 50
    user_id: Optional[str] = "anonymous"


class ChatResponse(BaseModel):
    action: str
    response: str
    data: List[Dict[str, Any]]  # Changed from Dict to List to match new format
    ui_suggestions: List[Dict[str, Any]]
    search_metadata: Dict[str, Any]
    results: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    query_id: Optional[str] = None

class SearchResponse(BaseModel):
    action: str
    response: str
    data: Dict[str, Any]
    ui_suggestions: List[Dict[str, str]]
    search_metadata: Dict[str, Any]


class EmployeeData(BaseModel):
    id: str
    name: str
    department: str
    tech_group: Optional[str] = None
    vvdn_exp: Optional[str] = None
    total_exp: Optional[str] = None
    skill_set: Optional[str] = None
    location: Optional[str] = None
    projects: Optional[List[Dict[str, Any]]] = []
    project_count: Optional[int] = 0
    total_project_occupancy: Optional[int] = 0
    available_capacity: Optional[int] = 100
    selection_reason: Optional[str] = None
    ai_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    designation: Optional[str] = None

class QueryResponse(BaseModel):
    chat_response: str
    data: List[Dict[str, Any]]  # More flexible than EmployeeData
    ui_actions: List[str]


class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int
    database_records: int
    vector_documents: int
    file_metadata: Dict[str, Any]
    all_employees: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str = "1.0.0"


class StatsResponse(BaseModel):
    database: Dict[str, Any]
    vector_store: Dict[str, Any]
    system: Dict[str, Any]


# Employee Management Schemas
class ProjectData(BaseModel):
    project_name: str
    customer: Optional[str] = ""
    project_department: Optional[str] = ""
    project_industry: Optional[str] = ""
    project_status: Optional[str] = "active"
    occupancy: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    committed_relieving_date: Optional[str] = None
    extended_relieving_date: Optional[str] = None
    project_committed_end_date: Optional[str] = None
    project_extended_end_date: Optional[str] = None
    role: Optional[str] = ""
    deployment: Optional[str] = ""


class SkillsUpdateRequest(BaseModel):
    skills: List[str]


class ProjectsUpdateRequest(BaseModel):
    projects: List[ProjectData]


class ProjectsListResponse(BaseModel):
    status: str
    projects: List[Dict[str, Any]]
    total_occupancy: int
    available_capacity: int


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    employee_department: Optional[str] = None
    total_exp: Optional[str] = None
    vvdn_exp: Optional[str] = None
    designation: Optional[str] = None
    tech_group: Optional[str] = None
    emp_location: Optional[str] = None


class ProjectResponse(BaseModel):
    project_name: str
    customer: Optional[str] = ""
    project_department: Optional[str] = ""
    project_industry: Optional[str] = ""
    project_status: Optional[str] = "active"
    occupancy: int = 0
    role: Optional[str] = ""
    deployment: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    committed_relieving_date: Optional[str] = None
    extended_relieving_date: Optional[str] = None
    project_committed_end_date: Optional[str] = None
    project_extended_end_date: Optional[str] = None


class EmployeeResponse(BaseModel):
    status: str
    employee: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ProjectEmployeeCount(BaseModel):
    project: str
    employee_count: int


class OthersEmployeeCount(BaseModel):
    employee_count: int


class ProjectDistributionResponse(BaseModel):
    status: str
    total_employees: int
    projects: List[ProjectEmployeeCount]

class DepartmentItem(BaseModel):
    department: str
    employee_count: int

class DepartmentDistributionResponse(BaseModel):
    status: str
    departments: List[DepartmentItem]


class AvailableEmployeesResponse(BaseModel):
    status: str
    month_threshold: int
    data: List[Dict[str, Any]]

class LowOccupancyResponse(BaseModel):
    status: str
    occupancy_threshold: int
    long_term_extension_months: int
    data: List[Dict[str, Any]]

class FreepoolCount(BaseModel):
    freepool_count: int
    project_count: int
    employee_count: int

class EmployeeDirectoryResponse(BaseModel):
    status: str
    employees: List[Dict[str, Any]]