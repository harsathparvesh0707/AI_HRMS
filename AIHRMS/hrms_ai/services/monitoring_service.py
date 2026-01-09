"""
Monitoring Service - Production monitoring and performance tracking
"""
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring AI search performance and system health"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.error_counts = {}
        self.query_analytics = []
    
    def start_operation(self, operation_name: str) -> str:
        """Start monitoring an operation"""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.performance_metrics[operation_id] = {
            'operation': operation_name,
            'start_time': time.time(),
            'status': 'running'
        }
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, metadata: Dict = None):
        """End monitoring an operation"""
        if operation_id in self.performance_metrics:
            metric = self.performance_metrics[operation_id]
            metric['end_time'] = time.time()
            metric['duration'] = metric['end_time'] - metric['start_time']
            metric['status'] = 'success' if success else 'failed'
            metric['metadata'] = metadata or {}
            
            logger.info(f"Operation {metric['operation']} completed in {metric['duration']:.2f}s - Status: {metric['status']}")
    
    def record_query(self, query: str, parsed_query: Dict, results_count: int, processing_time: float):
        """Record query analytics"""
        self.query_analytics.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'query_type': parsed_query.get('query_type', 'unknown'),
            'multi_intent': parsed_query.get('multi_intent', False),
            'results_count': results_count,
            'processing_time': processing_time,
            'required_skills': parsed_query.get('required_skills', []),
            'project_domain': parsed_query.get('project_domain')
        })
        
        # Keep only last 1000 queries
        if len(self.query_analytics) > 1000:
            self.query_analytics = self.query_analytics[-1000:]
    
    def record_error(self, error_type: str, error_message: str, context: Dict = None):
        """Record error for monitoring"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        logger.error(f"Error recorded - Type: {error_type}, Message: {error_message}, Context: {context}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        completed_operations = [m for m in self.performance_metrics.values() if 'duration' in m]
        
        if not completed_operations:
            return {"status": "no_data"}
        
        durations = [op['duration'] for op in completed_operations]
        success_count = len([op for op in completed_operations if op['status'] == 'success'])
        
        return {
            "total_operations": len(completed_operations),
            "success_rate": success_count / len(completed_operations) * 100,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "error_counts": self.error_counts
        }
    
    def get_query_analytics(self) -> Dict[str, Any]:
        """Get query analytics"""
        if not self.query_analytics:
            return {"status": "no_data"}
        
        total_queries = len(self.query_analytics)
        avg_processing_time = sum(q['processing_time'] for q in self.query_analytics) / total_queries
        
        # Query type distribution
        query_types = {}
        for query in self.query_analytics:
            qtype = query['query_type']
            query_types[qtype] = query_types.get(qtype, 0) + 1
        
        # Multi-intent queries
        multi_intent_count = len([q for q in self.query_analytics if q['multi_intent']])
        
        return {
            "total_queries": total_queries,
            "avg_processing_time": avg_processing_time,
            "query_type_distribution": query_types,
            "multi_intent_percentage": multi_intent_count / total_queries * 100,
            "recent_queries": self.query_analytics[-10:]  # Last 10 queries
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        perf_stats = self.get_performance_stats()
        query_stats = self.get_query_analytics()
        
        # Determine health status
        health_status = "healthy"
        if perf_stats.get("success_rate", 100) < 95:
            health_status = "degraded"
        if perf_stats.get("success_rate", 100) < 80:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "performance": perf_stats,
            "query_analytics": query_stats,
            "uptime": "active"
        }