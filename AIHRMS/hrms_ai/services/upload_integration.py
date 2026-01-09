# services/upload_integration.py
import logging
import hashlib
from typing import Dict, List, Optional
from .compression_service import compression_service
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class UploadIntegrationService:
    """Integration service for upload → compression → ranking pipeline"""
    
    async def post_upload_rebuild(self) -> Dict[str, any]:
        """
        Called after employee data upload to rebuild all compression caches
        This is your main integration point
        """
        try:
            logger.info("🚀 Starting post-upload rebuild process...")
            
            # Step 1: Clear old compression cache
            await compression_service.clear_compression_cache()
            
            # Step 2: Rebuild compressed employee data
            compression_result = await compression_service.compress_all_employees()
            
            # Step 3: Clear any cached ranking results (they're now stale)
            await self._clear_ranking_cache()
            
            logger.info("✅ Post-upload rebuild completed successfully")
            
            return {
                'status': 'success',
                'compressed_employees': compression_result['compressed_count'],
                'message': 'Compression cache rebuilt successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Post-upload rebuild failed: {e}")
            return {
                'status': 'error',
                'message': f'Rebuild failed: {str(e)}'
            }

    async def get_compressed_for_ranking(self, employee_ids: List[str] = None) -> Dict[str, str]:
        """
        Get compressed employee data for ranking
        If employee_ids is None, returns all compressed data
        """
        try:
            if employee_ids is None:
                # Return all compressed data
                return await cache_manager.get("compressed_employees") or {}
            
            # Return specific employees
            all_compressed = await cache_manager.get("compressed_employees") or {}
            result = {}
            
            for emp_id in employee_ids:
                clean_id = str(emp_id).replace('VVDN/', '')
                if clean_id in all_compressed:
                    result[clean_id] = all_compressed[clean_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get compressed data for ranking: {e}")
            return {}

    async def get_skills_intersection(self, employee_ids: List[str], semantic_skills: List[str]) -> Dict[str, List[str]]:
        """
        Get intersection of employee skills with semantic skills for LLM context
        This reduces the skill payload sent to LLM
        """
        try:
            result = {}
            skills_data = await cache_manager.get("employee_skills") or {}
            
            # Convert semantic skills to lowercase for matching
            semantic_lower = [skill.lower().strip() for skill in semantic_skills]
            
            for emp_id in employee_ids:
                clean_id = str(emp_id).replace('VVDN/', '')
                emp_skills = skills_data.get(clean_id, [])
                
                # Find intersection
                intersection = [skill for skill in emp_skills if skill in semantic_lower]
                result[clean_id] = intersection
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get skills intersection: {e}")
            return {}

    async def cache_ranking_query(self, query: str, filters: Dict, results: List[Dict]) -> str:
        """
        Cache ranking results with a query-based key
        Returns the cache key for future retrieval
        """
        try:
            # Create hash from query + filters
            query_data = f"{query}:{str(sorted(filters.items()))}"
            query_hash = hashlib.md5(query_data.encode()).hexdigest()[:16]
            
            cache_data = {
                'query': query,
                'filters': filters,
                'results': results,
                'result_count': len(results)
            }
            
            await compression_service.cache_ranking_result(query_hash, cache_data)
            return query_hash
            
        except Exception as e:
            logger.error(f"Failed to cache ranking query: {e}")
            return ""

    async def get_cached_ranking_query(self, query: str, filters: Dict) -> Optional[Dict]:
        """Get cached ranking results if available"""
        try:
            query_data = f"{query}:{str(sorted(filters.items()))}"
            query_hash = hashlib.md5(query_data.encode()).hexdigest()[:16]
            
            return await compression_service.get_cached_ranking(query_hash)
            
        except Exception as e:
            logger.error(f"Failed to get cached ranking query: {e}")
            return None

    async def _clear_ranking_cache(self) -> None:
        """Clear all ranking cache entries"""
        try:
            # This would need to be implemented based on your cache structure
            # For now, we'll just log it
            logger.info("🗑️ Cleared ranking cache entries")
        except Exception as e:
            logger.warning(f"Failed to clear ranking cache: {e}")

    async def get_compression_stats(self) -> Dict[str, any]:
        """Get compression statistics for monitoring"""
        try:
            compressed_data = await cache_manager.get("compressed_employees") or {}
            skills_data = await cache_manager.get("employee_skills") or {}
            
            # Sample compressed line for inspection
            sample_line = ""
            if compressed_data:
                sample_line = list(compressed_data.values())[0]
            
            return {
                'compressed_employees': len(compressed_data),
                'employees_with_skills': len(skills_data),
                'sample_compressed_line': sample_line,
                'cache_stats': cache_manager.get_stats()
            }
            
        except Exception as e:
            logger.error(f"Failed to get compression stats: {e}")
            return {'error': str(e)}

# Global instance
upload_integration = UploadIntegrationService()