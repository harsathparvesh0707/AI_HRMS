"""
Base Repository - Abstract base class for all repositories
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from ..core.database import get_db_session

class BaseRepository(ABC):
    """Base repository with common database operations"""
    
    def __init__(self):
        pass
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        with get_db_session() as session:
            result = session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    
    def execute_single(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute SELECT query and return single result"""
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with get_db_session() as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result.rowcount
    
    def execute_batch(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute batch operations"""
        with get_db_session() as session:
            total_affected = 0
            for params in params_list:
                result = session.execute(text(query), params)
                total_affected += result.rowcount
            session.commit()
            return total_affected