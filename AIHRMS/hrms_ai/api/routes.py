from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Any
import logging
from ..services.ai_search_service import AISearchService

logger = logging.getLogger(__name__)
from ..services.upload_service import UploadService
from ..services.embedding_cache_service import EmbeddingCacheService
from ..services.dashboard_service import DashboardService
from ..models.schemas import (ChatRequest, UploadResponse,
                            SkillsUpdateRequest, ProjectsUpdateRequest, ProfileUpdateRequest, EmployeeResponse, ProjectsListResponse,
                            ProjectDistributionResponse, DepartmentDistributionResponse, AvailableEmployeesResponse, LowOccupancyResponse,
                            FreepoolCount, EmployeeDirectoryResponse, DeploymentFilter, AIRequest, User, UserResponse, ProjectRequirements)
from .endpoints import health
from ..celery.tasks import rebuild_embedding_cache
from ..websocket.websocket import ws_manager
from ..services.redis_broker import RedisMessageBroker
from ..services.available_employees_service import AvailableEmployeesService
from ..services.low_occupancy_service import LowOccupancyService
from ..services.ai_analytics import AiAnalytics
from ..services.cache_manager import cache_manager
from ..auth.security import Authentication
from ..auth.auth import Token
from ..services.project_requirements_service import ProjectRequirementSuggestion
from ..services.freepool_suggestion_service import FreepoolProjectSuggestionService
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import JWTError, ExpiredSignatureError
import asyncio

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])

search_service = AISearchService()
upload_service = UploadService()
cache_service = EmbeddingCacheService()
dashboard_service = DashboardService()
broker = RedisMessageBroker()
available_employees_service = AvailableEmployeesService()
low_occupancy_service = LowOccupancyService()
ai_analytics = AiAnalytics()
project_suggestion = ProjectRequirementSuggestion()
freepool_suggestion_service = FreepoolProjectSuggestionService()
user_auth = Authentication()
user_token = Token()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_details = user_token._decode_access_token(token)
        user_id = user_details.get("user_id")
        username = user_details.get("username")
        if not user_id or not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "user_id": user_id,
            "username": username
        }
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token has Expired")
    
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



@api_router.post("/search-rank-simplified-new", tags=["search"])
async def search_results_simplified_new(request: ChatRequest, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Search with simplified parsing - uses general tech categories instead of specific ones"""
    logger.info(f"🔍 /search-rank-simplified API called with query: '{request.query}'")
    print(f"🔍 /search-rank-simplified API called with query: '{request.query}'")
    
    result = await search_service.process_search_and_rank_with_criteria_simplified_new_llm(
        query=request.query,
        top_k=request.top_k
    )
    
    logger.info(f"✅ /search-rank-simplified completed: {result.get('total_results', 0)} results")
    print(f"✅ /search-rank-simplified completed: {result.get('total_results', 0)} results")
    return result


@api_router.post("/upload/hrms-data", response_model=UploadResponse, tags=["upload"])
async def upload_hrms_data(
    file: UploadFile = File(...),
    description: str = Form(""), current_user: dict = Depends(get_current_user)
) -> UploadResponse:
    """File Upload Endpoint"""
    # Process file upload
    result = await upload_service.process_file_upload(file, description)
    keys = await cache_manager.keys("dashboard:*")
    for key in keys:
        await cache_manager.delete(key)
    # Trigger cache rebuild in background for search optimization
    # background_tasks.add_task(_post_upload_cache_rebuild)
    rebuild_embedding_cache.delay()
    
    return result

@api_router.get("/stats", tags=["analytics"])
async def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    stats = await search_service.get_system_statistics()
    
    # No background tasks for direct service usage
    stats['background_tasks'] = {
        'active': 0,
        'completed': 0,
        'failed': 0,
        'total': 0
    }
    
    return {"status": "success", "statistics": stats}

@api_router.post("/init-database", tags=["admin"])
async def initialize_database() -> Dict[str, Any]:
    """Initialize database tables and performance indexes"""
    try:
        # Initialize database tables and indexes (handled in database.py)
        result = await upload_service.initialize_database()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/debug-data", tags=["debug"])
async def debug_data() -> Dict[str, Any]:
    """Debug endpoint"""
    return await search_service.get_debug_data()

@api_router.post("/index-employees", tags=["admin"])
async def index_employees(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Index employees - Non-blocking background processing"""
    try:
        background_tasks.add_task(_index_employees_background)
        background_tasks.add_task(_precompute_embeddings_background)
        
        return {
            "status": "accepted",
            "message": "Employee indexing and cache rebuild started in background",
            "estimated_time": "2-5 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _index_employees_background():
    """Background task for heavy indexing operations"""
    try:
        search_svc = search_service
        if hasattr(search_svc, 'hybrid_engine') and search_svc.hybrid_engine and search_svc.hybrid_engine.available:
            await search_svc.hybrid_engine.index_employees()
        logger.info("✅ Background indexing completed")
    except Exception as e:
        logger.error(f"❌ Background indexing failed: {e}")

async def _precompute_embeddings_background():
    """Background task for unified embedding precomputation"""
    try:
        embedding_service = EmbeddingCacheService()
        if embedding_service.available:
            result = await embedding_service.rebuild_all_caches()
            if result.get('status') == 'success':
                logger.info(f"✅ Unified embedding precomputation completed: {result.get('employees_processed', 0)} employees")
            else:
                logger.warning(f"⚠️ Embedding precomputation had issues: {result.get('message', 'Unknown error')}")
        else:
            logger.warning("⚠️ Embedding service not available")
    except Exception as e:
        logger.error(f"❌ Embedding precomputation failed: {e}")

@api_router.post("/precompute-embeddings", tags=["performance"])
async def precompute_embeddings(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """🚀 Pre-compute embeddings - Non-blocking background processing"""
    try:
        background_tasks.add_task(_precompute_embeddings_background)
        
        return {
            "status": "accepted",
            "message": "Unified embedding precomputation started in background",
            "estimated_time": "1-3 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/cache-stats", tags=["performance"])
async def get_cache_stats(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get cache stats"""
    try:
        stats = {}
        
        # Embedding cache stats
        embedding_service = EmbeddingCacheService()
        if embedding_service.available:
            stats["embedding_cache"] = embedding_service.get_cache_stats()
        
        # Skill embeddings cache stats
        if hasattr(search_service, 'hybrid_engine') and search_service.hybrid_engine:
            stats["skill_embeddings"] = {
                "initialized": search_service.hybrid_engine.skill_embeddings_initialized,
                "cached_skills": len(search_service.hybrid_engine.skill_embeddings)
            }
        
        return {"status": "success", "cache_stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.delete("/clear-cache", tags=["performance"])
async def clear_all_caches(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Clear ALL caches - embeddings, queries, and skill mappings"""
    embedding_service = EmbeddingCacheService()
    if embedding_service.available:
        # Clear employee embeddings
        await embedding_service.invalidate_employee_cache()
        
        # Clear query cache (embeddings + parsed queries)
        query_result = embedding_service.clear_query_cache()
        
        # Clear skill embeddings cache
        if hasattr(search_service, 'hybrid_engine') and search_service.hybrid_engine:
            search_service.hybrid_engine.skill_embeddings = {}
            search_service.hybrid_engine.skill_embeddings_initialized = False
        
        return {
            "status": "success", 
            "message": "All caches cleared",
            "query_cache": query_result
        }
    return {"status": "unavailable", "message": "Cache service not available"}

@api_router.post("/rebuild-compression-cache", tags=["performance"])
async def rebuild_compression_cache(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Rebuild compression cache"""
    try:
        from ..services.compression_service import compression_service
        
        background_tasks.add_task(_rebuild_compression_background, compression_service)
        
        return {
            "status": "accepted",
            "message": "Compression cache rebuild started in background",
            "estimated_time": "1-2 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/compression-stats", tags=["performance"])
async def get_compression_stats(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get compression cache stats"""
    try:
        from ..services.compression_service import compression_service
        from ..services.cache_manager import cache_manager
        
        # Get basic cache stats
        cache_stats = cache_manager.get_stats()
        
        # Get compression-specific stats
        comp_ids = await cache_manager.get("comp:ids")
        if comp_ids and isinstance(comp_ids, (set, list)):
            sample_data = await compression_service.get_compressed_batch(list(comp_ids)[:3])
            compressed_count = len(comp_ids)
        else:
            sample_data = []
            compressed_count = 0
        
        stats = {
            "cache_type": cache_stats.get("selected_type", "unknown"),
            "compressed_employees": compressed_count,
            "sample_compressed": [item.get("compact", "") for item in sample_data],
            "cache_available": cache_manager.is_available()
        }
        
        return {"status": "success", "compression_stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/cache-info", tags=["performance"])
async def get_cache_info(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get detailed cache system information"""
    try:
        from ..services.cache_manager import cache_manager
        cache_stats = cache_manager.get_stats()
        return {"status": "success", "cache_info": cache_stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.post("/switch-cache", tags=["admin"])
async def switch_cache_type(cache_type: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Switch cache type (redis/memory) - for testing purposes"""
    try:
        from ..services.cache_manager import cache_manager
        
        if cache_type not in ["redis", "memory"]:
            raise HTTPException(status_code=400, detail="Invalid cache type. Use 'redis' or 'memory'")
        
        # This would require reinitialization - for now just return current status
        current_stats = cache_manager.get_stats()
        return {
            "status": "info",
            "message": f"Current cache type: {current_stats.get('selected_type', 'unknown')}",
            "note": "Cache type switching requires application restart"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def _rebuild_compression_background(compression_service):
    """Background task for compression cache rebuild"""
    try:
        count = await compression_service.rebuild_cache()
        logger.info(f"✅ Compression cache rebuilt: {count} employees")
    except Exception as e:
        logger.error(f"❌ Compression cache rebuild failed: {e}")

@api_router.get("/system-health", tags=["monitoring"])
async def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
    try:
        from ..services.monitoring_service import MonitoringService
        monitoring = MonitoringService()
        return monitoring.get_system_health()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/performance-metrics", tags=["monitoring"])
async def get_performance_metrics(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get detailed performance metrics"""
    try:
        stats = await search_service.get_system_statistics()
        return {"status": "success", "metrics": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/query-analytics", tags=["monitoring"])
async def get_query_analytics(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get query analytics and insights"""
    try:
        from ..services.monitoring_service import MonitoringService
        monitoring = MonitoringService()
        analytics = monitoring.get_query_analytics()
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Employee Management APIs
@api_router.get("/employees", tags=["employee-management"])
async def get_all_employees(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1), current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get All Employees"""
    try:
        result = await upload_service.get_all_employee_details(page, page_size)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch all employee details: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/employees/{employee_id}", tags=["employee-management"])
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get employee details with all projects"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.get_employee_details(full_employee_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@api_router.put("/employees/{employee_id}/skills", response_model=EmployeeResponse, tags=["employee-management"])
async def update_employee_skills(employee_id: str, skills_data: SkillsUpdateRequest, current_user: dict = Depends(get_current_user)) -> EmployeeResponse:
    """Update employee skills"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.update_employee_skills(full_employee_id, skills_data.dict())
        
        # Invalidate and rebuild caches for this employee
        from ..services.cache_invalidation_service import cache_invalidation_service
        await cache_invalidation_service.invalidate_and_rebuild_employee(full_employee_id)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/employees/{employee_id}/projects", response_model=EmployeeResponse, tags=["employee-management"])
async def add_employee_projects(employee_id: str, projects_data: ProjectsUpdateRequest, current_user: dict = Depends(get_current_user)) -> EmployeeResponse:
    """Add new projects to employee (does not remove existing projects)"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.add_employee_projects(full_employee_id, projects_data.dict())
        
        # Invalidate and rebuild caches for this employee
        from ..services.cache_invalidation_service import cache_invalidation_service
        await cache_invalidation_service.invalidate_and_rebuild_employee(full_employee_id)

        keys = await cache_manager.keys("dashboard:*")
        for key in keys:
            await cache_manager.delete(key)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/employees/{employee_id}/projects", response_model=ProjectsListResponse, tags=["employee-management"])
async def list_employee_projects(employee_id: str, current_user: dict = Depends(get_current_user)) -> ProjectsListResponse:
    """List all projects for an employee"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.list_employee_projects(full_employee_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@api_router.delete("/employees/{employee_id}/projects", tags=["employee-management"])
async def delete_all_employee_projects(employee_id: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete all projects for an employee"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.delete_all_employee_projects(full_employee_id)
        
        # Invalidate and rebuild caches for this employee
        from ..services.cache_invalidation_service import cache_invalidation_service
        await cache_invalidation_service.invalidate_and_rebuild_employee(full_employee_id)

        keys = await cache_manager.keys("dashboard:*")
        for key in keys:
            await cache_manager.delete(key)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/employees/{employee_id}/projects/{project_name}", tags=["employee-management"])
async def delete_employee_project(employee_id: str, project_name: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete specific project for an employee"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.delete_employee_project(full_employee_id, project_name)
        
         # Invalidate and rebuild caches for this employee
        from ..services.cache_invalidation_service import cache_invalidation_service
        await cache_invalidation_service.invalidate_and_rebuild_employee(full_employee_id)
        
        keys = await cache_manager.keys("dashboard:*")
        for key in keys:
            await cache_manager.delete(key)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.patch("/employees/{employee_id}/profile", response_model=EmployeeResponse, tags=["employee-management"])
async def update_employee_profile(employee_id: str, profile_data: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)) -> EmployeeResponse:
    """Update employee profile information"""
    try:
        # Add VVDN prefix if not present
        full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
        result = await upload_service.update_employee_profile(full_employee_id, profile_data.dict(exclude_unset=True))
        
        # Invalidate and rebuild caches for this employee
        from ..services.cache_invalidation_service import cache_invalidation_service
        await cache_invalidation_service.invalidate_and_rebuild_employee(full_employee_id)

        keys = await cache_manager.keys("dashboard:*")
        for key in keys:
            await cache_manager.delete(key)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/dashboard/project_distribution",  response_model=ProjectDistributionResponse, tags=["dashboard"])
async def project_distribution(current_user: dict = Depends(get_current_user)):
    """API for total_project count and top-most aligned projects"""
    try:
        cache_key = f"dashborad:project_distribution"
        result = await cache_manager.get(cache_key)
        if not result:
            logger.info(f"Cache Not Found for key: {cache_key}")
            result = await dashboard_service.get_project_distribution(top_n=4)
            await cache_manager.set(cache_key, result, 300)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get("/dashboard/department_counts", response_model=DepartmentDistributionResponse, tags=["dashboard"])
async def department_distribution(current_user: dict = Depends(get_current_user)):
    """Departments and Employee Counts"""
    try:
        cache_key = f"dashboard:department_counts"
        result = await cache_manager.get(cache_key)
        if not result:
            logger.info(f"Cache Not Found for key: {cache_key}")
            result = await dashboard_service.get_department_distribution()
            await cache_manager.set(cache_key, result, 300)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@api_router.get("/dashboard/count_data", response_model=FreepoolCount)
async def get_dashboard_count(current_user: dict = Depends(get_current_user)):
    """Freepool, Employee and Projects Count"""
    try:
        cache_key = f"dashboard:count_data"
        result = await cache_manager.get(cache_key)
        if not result:
            logger.info(f"Cache Not Found for key: {cache_key}")
            result = await dashboard_service.get_dashboard_count_details()
            await cache_manager.set(cache_key, result, 300)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get("/dashboard/employees_deployment", tags=["employee-management"])
async def get_employees_deployment_wise(deployment: DeploymentFilter = Query(...), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1), current_user: dict = Depends(get_current_user)):
    """Get Employee Details deployment wise"""
    try:
        result = await dashboard_service.get_employees_deployment_wise(deployment, page, page_size)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    

@api_router.get("/available_employees", response_model=AvailableEmployeesResponse, tags=["employee-management"])
async def find_available_employees(month_threshold: int = Query(3, ge=0), current_user: dict = Depends(get_current_user)):
    """Find employees who are currently free or whose projects are ending soon"""
    try:
        cache_key = f"dashboard:available_employees_{month_threshold}"
        result = await cache_manager.get(cache_key)
        if not result:
            logger.info(f"Cache Not Found for key: {cache_key}")
            logger.info(f"🔍 Finding available employees with {month_threshold} months threshold")
            result = available_employees_service.find_available_employees(months_threshold=month_threshold)
            await cache_manager.set(cache_key, result, 300)
        return result
        
    except Exception as e:
        logger.error(f"Error finding available employees: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/low_occupancy_employees", response_model=LowOccupancyResponse, tags=["employee-management"])
async def find_low_occupancy_employees(occupancy_threshold: int = Query(50, ge=0, lt=100), long_term_extension_months: int = Query(36, ge=0), current_user: dict = Depends(get_current_user)) -> LowOccupancyResponse:
    """Find low occupancy employees based on occupancy and months threshold"""
    try:
        result = low_occupancy_service.find_long_term_low_occupancy_employees(occupancy_threshold=occupancy_threshold, long_term_extension_months=long_term_extension_months)
        return result

    except Exception as e:
        logger.exception("Error finding low occupancy employees")
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get("/dashboard/employee_directory", response_model=EmployeeDirectoryResponse, tags=["employee-management"])
async def get_employee_directory(current_user: dict = Depends(get_current_user)):
    """Employee Directory Data"""
    try:
        cache_key = f"dashboard:employee_directory"
        result = await cache_manager.get(cache_key)
        if not result:
            logger.info(f"Cache Not Found for key: {cache_key}")
            result = await dashboard_service.get_employees_directory()
            await cache_manager.set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("Error while fetching employee directory")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/ai-analytics")
async def generate_ai_widgets(request: AIRequest, current_user: dict = Depends(get_current_user)):
    try:
        logger.info(f"🔍 /ai-analytics API called with prompt: '{request.prompt}\n {request.chartType}'")
        result = await ai_analytics.ai_analytics_service(request)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get("/projects", status_code=200)
async def get_all_projects(current_user: dict = Depends(get_current_user)):
    try:
        result = await dashboard_service._get_all_projects()
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))

    
@api_router.post("/project_requirements")
async def add_new_project_requirements(request: ProjectRequirements, current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion.add_project_requirement(request)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get('/project_requirements', status_code=200)
async def get_all_project_requirement(current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._get_all_project_requirements()
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get('/projects/{project_name}/project_requirements', status_code=200)
async def get_requirements_by_project(project_name: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._get_requirements_by_project_name(project_name)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get('/project_requirements/{id}', status_code=200)
async def get_project_requirement_by_id(id: int ,current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._get_requirement_by_id(id)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put('/project_requirements/{id}', status_code=200)
async def update_project_requirement(id: int, update_data: ProjectRequirements, current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._update_project_requirement(id, update_data)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.delete('/project_requirements/{id}', status_code=200)
async def delete_project_requirement(id: int, current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._delete_project_requirement(id)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/project_requirement_suggestion", status_code=200, tags=["suggestions"])
async def project_requirement_suggestion(project_requirement_id = Query(default=None), current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion.process_requirement_suggestion(project_requirement_id=project_requirement_id)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/suggested_requirements", status_code=200, tags=["suggestions"])
async def get_suggested_requirements(project_requirement_id: int = Query(default=None), current_user: dict = Depends(get_current_user)):
    try:
        result = await project_suggestion._get_all_project_suggestions(project_requirement_id = project_requirement_id)
        return result
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@api_router.get("/freepool_project_suggestions", tags=["suggestions"], status_code=200)
async def get_freepool_project_suggestions(current_user: dict = Depends(get_current_user)):
    try:
        await freepool_suggestion_service.get_suggestions()
        return
    except Exception as e:
        logger.error(f"Error generating freepool project suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/freepool_suggestions", status_code=200, tags=["suggestions", "dashboard"])
async def get_freepool_sugestions(current_user: dict = Depends(get_current_user)):
    try:
        result = await freepool_suggestion_service.get_suggestions_from_db()
        return result
    except Exception as e:
        logger.error(f"Error while fetching freepool suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    
@api_router.post("/register")
async def user_registration(user: User):
    try:
        result = await user_auth._create_registered_user(user.dict())
        return result
    except Exception as e:
        logger.error(f"Error while registering user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/login")
async def user_login(user: User):
    try:
        result = await user_auth._user_login(user.dict())
        return result
    except Exception as e:
        logger.error(f"Error while Login: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.websocket("/ws/notification")
async def websocket_connection(websocket: WebSocket):
    logger.info("Connecting to Web Socket...")
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected (code={e.code})")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await ws_manager.disconnect(websocket)



@api_router.on_event("startup")
async def start_redis_listener():

    async def handle_message(data: dict):
        await ws_manager.broadcast(data)

    asyncio.create_task(broker.subscribe(handle_message))