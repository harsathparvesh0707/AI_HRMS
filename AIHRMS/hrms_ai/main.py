"""
Main application entry point
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging service first
try:
    from .services.logging_service import logging_service
except ImportError:
    from services.logging_service import logging_service

from .config.settings import settings
from .core.database import init_database
from .api.routes import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI HRMS Backend - Enhanced Architecture",
    description="Intelligent Human Resource Management System with clean architecture and improved query processing",
    version="2.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint with system status"""
    try:
        from .services.cache_manager import cache_manager
        cache_stats = cache_manager.get_stats()
        cache_system = cache_stats.get("selected_type", "none")
        cache_status = cache_stats.get("status", "unavailable")
    except Exception:
        cache_system = "none"
        cache_status = "unavailable"
    
    return {
        "message": "AI HRMS API is running", 
        "version": "2.0.0",
        "cache_system": cache_system,
        "cache_status": cache_status,
        "features": [
            "4_stage_hierarchical_ai_ranking",
            "intelligent_cache_management",
            "project_aware_search",
            "domain_expertise_matching",
            "production_monitoring"
        ]
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting AI HRMS Backend...")
        
        # Initialize database
        init_database()
        logger.info("✅ Database initialized")
        
        # Initialize intelligent cache system - Never fail startup
        try:
            from .services.cache_manager import cache_manager
            await cache_manager.initialize()
            cache_stats = cache_manager.get_stats()
            logger.info(f"✅ Cache system initialized: {cache_stats.get('selected_type', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Cache initialization failed: {e}")
            logger.info("⚠️ Continuing without cache - performance may be reduced")
        
        # Auto-rebuild embedding cache if empty on startup (only if DB has data)
        try:
            from .services.embedding_cache_service import EmbeddingCacheService
            from sqlalchemy import text
            from .core.database import get_db_session
            
            # Check if database has employee data
            with get_db_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM employees"))
                employee_count = result.scalar()
            
            if employee_count > 0:
                embedding_service = EmbeddingCacheService()
                if embedding_service.available:
                    cache_data = await embedding_service.get_cached_employee_embeddings()
                    if not cache_data.get('embeddings'):
                        logger.info(f"🔄 No cached embeddings found, auto-rebuilding for {employee_count} employees...")
                        result = await embedding_service.rebuild_all_caches()
                        if result.get('status') == 'success':
                            logger.info(f"✅ Auto-rebuilt all caches: {result.get('employees_processed', 0)} employees")
                        else:
                            logger.warning(f"⚠️ Auto-rebuild failed: {result.get('message', 'Unknown error')}")
                    else:
                        logger.info(f"✅ Found existing embedding cache: {len(cache_data['embeddings'])} employees")
            else:
                logger.info("⚠️ No employee data in database, skipping cache rebuild")
        except Exception as e:
            logger.warning(f"⚠️ Embedding cache check failed: {e}")
        
        # Initialize compression cache - Optional
        try:
            from .services.compression_service import compression_service
            count = await compression_service.rebuild_cache()
            logger.info(f"✅ Compression cache built: {count} employees")
        except Exception as e:
            logger.warning(f"⚠️ Could not build initial compression cache: {e}")
            logger.info("⚠️ Compression cache will be built on first search request")
        
        logger.info("🎉 AI HRMS Backend started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down AI HRMS Backend...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )