# services/compression_utils.py
import logging
from typing import Dict, List, Tuple
from .upload_integration import upload_integration
from .compression_service import compression_service

logger = logging.getLogger(__name__)

class CompressionUtils:
    """Utility functions for compression integration"""
    
    @staticmethod
    async def trigger_post_upload_rebuild():
        """
        Call this after your employee data upload completes
        This is your main integration point
        """
        return await upload_integration.post_upload_rebuild()
    
    @staticmethod
    async def get_ranking_data(employee_ids: List[str] = None) -> Dict[str, str]:
        """
        Get compressed employee data for ranking algorithms
        Returns format: {emp_id: "compressed_line"}
        """
        return await upload_integration.get_compressed_for_ranking(employee_ids)
    
    @staticmethod
    async def get_contextual_skills(employee_ids: List[str], semantic_skills: List[str]) -> Dict[str, List[str]]:
        """
        Get skill intersection for LLM context (reduces payload)
        Returns format: {emp_id: [intersected_skills]}
        """
        return await upload_integration.get_skills_intersection(employee_ids, semantic_skills)
    
    @staticmethod
    async def cache_search_results(query: str, filters: Dict, results: List[Dict]) -> str:
        """
        Cache search/ranking results for performance
        Returns cache key
        """
        return await upload_integration.cache_ranking_query(query, filters, results)
    
    @staticmethod
    async def get_cached_search(query: str, filters: Dict) -> Dict:
        """
        Get cached search results if available
        Returns None if not cached
        """
        return await upload_integration.get_cached_ranking_query(query, filters)
    
    @staticmethod
    async def get_stats() -> Dict:
        """Get compression statistics for monitoring"""
        return await upload_integration.get_compression_stats()
    
    @staticmethod
    def parse_compressed_line(compressed_line: str) -> Dict[str, str]:
        """
        Parse compressed line back to readable format
        Format: {id}|{R}|{D}|{L}|{X}|{P}|{DEP}|{SK}
        """
        try:
            parts = compressed_line.split('|')
            if len(parts) >= 7:
                return {
                    'employee_id': parts[0],
                    'role_code': parts[1],
                    'dept_code': parts[2],
                    'location_code': parts[3],
                    'experience': parts[4],
                    'project_count': parts[5],
                    'deployment_code': parts[6],
                    'skills': parts[7] if len(parts) > 7 else ''
                }
        except Exception as e:
            logger.error(f"Failed to parse compressed line: {e}")
        
        return {}
    
    @staticmethod
    async def force_rebuild():
        """Force rebuild of all compression caches"""
        try:
            await compression_service.clear_compression_cache()
            return await compression_service.compress_all_employees()
        except Exception as e:
            logger.error(f"Force rebuild failed: {e}")
            return {'status': 'error', 'message': str(e)}

# Example usage patterns for integration:
"""
# 1. After employee data upload:
result = await CompressionUtils.trigger_post_upload_rebuild()

# 2. For ranking/search:
compressed_data = await CompressionUtils.get_ranking_data(['123', '456'])
# compressed_data = {'123': '123|SE|ENG|BLR|5.2|3|BIL|python,java,react', ...}

# 3. For LLM context (reduced skills):
contextual_skills = await CompressionUtils.get_contextual_skills(
    ['123', '456'], 
    ['python', 'javascript', 'react', 'machine learning']
)
# contextual_skills = {'123': ['python', 'react'], '456': ['javascript']}

# 4. Cache search results:
cache_key = await CompressionUtils.cache_search_results(
    "python developer", 
    {"location": "bangalore", "experience": ">3"}, 
    search_results
)

# 5. Get cached results:
cached = await CompressionUtils.get_cached_search(
    "python developer", 
    {"location": "bangalore", "experience": ">3"}
)
"""