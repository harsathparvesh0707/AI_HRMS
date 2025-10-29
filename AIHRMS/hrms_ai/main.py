from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy.orm import Session
from db import execute_query
from database import get_db
from schemas import QueryRequest, QueryResponse, EmployeeData
from models import Employee
from llm_integration import process_query
from vector_db import search_employee

app = FastAPI(title="HRMS AI Backend")

# @app.post("/query", response_model=QueryResponse)
# def handle_query(request: QueryRequest, db: Session = Depends(get_db)):
#     # Step 1: Get user query
#     user_query = request.query

#     # Step 2: Process with LLM
#     structured_query = process_query(user_query)

#     # Step 3: Use Vector DB to find relevant employees
#     vector_results = search_employee(structured_query)

#     # Step 4: Get matching employees from HRMS DB
#     employees = db.query(Employee).limit(5).all()

#     # Step 5: Format JSON response
#     response = QueryResponse(
#         chat_response=f"Processed Query: {structured_query}",
#         data=[EmployeeData.from_orm(e) for e in employees],
#         ui_actions={"show_table": True}
#     )
#     return response


# Pydantic models
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
    ui_actions: List[str]

@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    # Step 1: Use LLM to get structured query
    structured_query, fields, ui_actions, chat_response = process_query(request.query)
    
    # Step 2: Execute structured query on PostgreSQL
    results = execute_query(structured_query)
    
    # Step 3: Map results to EmployeeData
    data = [
        EmployeeData(
            id=row["id"],
            name=row["name"],
            department=row["department"],
            role=row["role"],
            status=row["status"]
        )
        for row in results
    ]
    
    return QueryResponse(
        chat_response=chat_response,
        data=data,
        ui_actions=ui_actions
    )
