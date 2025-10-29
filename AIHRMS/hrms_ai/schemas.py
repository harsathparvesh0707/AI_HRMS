from pydantic import BaseModel
from typing import List, Dict

class QueryRequest(BaseModel):
    query: str

class EmployeeData(BaseModel):
    id: int
    name: str
    department: str
    role: str
    status: str

class QueryResponse(BaseModel):
    chat_response: str
    data: List[EmployeeData]
    ui_actions: Dict
