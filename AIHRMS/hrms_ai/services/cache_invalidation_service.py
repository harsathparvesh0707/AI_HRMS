# services/cache_invalidation_service.py
import logging
from typing import Dict, Any
from .cache_manager import cache_manager
from .compression_service import compression_service
from .codebook_service import codebook_service

logger = logging.getLogger(__name__)

class CacheInvalidationService:
    """Handle cache invalidation for individual employee updates"""
    
    async def invalidate_employee_caches(self, employee_id: str) -> Dict[str, Any]:
        """Invalidate caches for a specific employee"""
        try:
            clean_id = str(employee_id).replace('VVDN/', '')
            
            # Clear specific employee caches
            await cache_manager.delete(f"emp_embedding:{clean_id}")
            await cache_manager.delete(f"compression:{clean_id}")
            
            # Bump data revision to invalidate ranking caches
            await cache_manager.incr("data_rev")
            
            logger.info(f"🗑️ Invalidated caches for employee {employee_id}")
            return {"status": "success", "employee_id": employee_id}
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate caches for {employee_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def rebuild_employee_caches(self, employee_id: str) -> Dict[str, Any]:
        """Rebuild caches for a specific employee"""
        try:
            # Update compression cache for this employee
            success = await compression_service.update_compression(employee_id)
            
            if success:
                logger.info(f"✅ Rebuilt compression cache for employee {employee_id}")
                return {"status": "success", "employee_id": employee_id}
            else:
                return {"status": "error", "message": "Failed to rebuild compression"}
                
        except Exception as e:
            logger.error(f"❌ Failed to rebuild caches for {employee_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def invalidate_and_rebuild_employee(self, employee_id: str) -> Dict[str, Any]:
        """Invalidate and rebuild caches for a specific employee"""
        try:
            # Step 1: Invalidate old caches
            await self.invalidate_employee_caches(employee_id)
            
            # Step 2: Rebuild compression cache for this employee
            await self.rebuild_employee_caches(employee_id)
            
            return {"status": "success", "employee_id": employee_id}
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate and rebuild for {employee_id}: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
cache_invalidation_service = CacheInvalidationService()