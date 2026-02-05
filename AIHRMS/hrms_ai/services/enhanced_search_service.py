"""
Enhanced Search Service - RAG + Hybrid Search Implementation
Preserves ALL original API functionality while adding advanced AI capabilities
"""
import logging
import re
import os
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from ..core.database import get_db_session
from ..services.llm_service import LLMService
from ..services.hybrid_search_engine import HybridSearchEngine

from ..models.schemas import ChatResponse

logger = logging.getLogger(__name__)

class IntelligentQueryRouter:
    """Replaces regex-heavy routing with intelligent classification"""
    
    def __init__(self):
        # Keywords for different query types (replaces 50+ regex patterns)
        self.keywords = {
            'single_employee': ['show details of', 'find employee', 'who is', 'employee details', 'lookup', 'search for'],
            'free_pool': ['free pool', 'freepool', 'free employees', 'available', 'who are available', 'available employees', 'show available'],
            'billable': ['billable', 'billable employees'],
            'budgeted': ['budgeted', 'budgeted employees'], 
            'support': ['support', 'support employees'],
            'skills': ['python', 'java', 'javascript', 'react', 'angular', 'docker', 'kubernetes', 'aws', 'azure', 'golang', 'spring', 'node', 'mysql', 'postgresql', 'mongodb', 'microservices', 'devops', 'ai/ml', 'machine learning', 'data science'],
            'locations': ['bangalore', 'kochi', 'gurgaon', 'pune', 'chennai', 'hyderabad', 'delhi', 'mumbai'],
            'departments': ['cloud department', 'quality department', 'it department', 'devops department', 'data department', 'mobile department'],
            'projects': ['project', 'team of', 'working on', 'team members'],
            'experience': ['years experience', 'more than', 'less than', 'greater than', 'over', 'under', 'experience'],
            'list_all': ['list all', 'show all', 'all employees', 'every employee']
        }
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """Route query intelligently without complex regex"""
        query_lower = query.lower().strip()
        
        # Check for multi-condition queries (replaces complex regex logic)
        multi_indicators = [' and ', ' with ', ' in ', ' developers', ' skills', 'years experience']
        if any(indicator in query_lower for indicator in multi_indicators):
            return self._handle_multi_condition_query(query_lower)
        
        # Single condition routing
        if any(kw in query_lower for kw in self.keywords['single_employee']):
            return self._handle_single_employee(query_lower)
        elif any(kw in query_lower for kw in self.keywords['free_pool']):
            return self._handle_deployment_status('free', query_lower)
        elif any(kw in query_lower for kw in self.keywords['billable']):
            return self._handle_deployment_status('billable', query_lower)
        elif any(kw in query_lower for kw in self.keywords['budgeted']):
            return self._handle_deployment_status('budgeted', query_lower)
        elif any(kw in query_lower for kw in self.keywords['support']):
            return self._handle_deployment_status('support', query_lower)
        elif any(kw in query_lower for kw in self.keywords['list_all']):
            return self._handle_list_all()
        elif any(kw in query_lower for kw in self.keywords['skills']):
            return self._handle_skills_query(query_lower)
        elif any(kw in query_lower for kw in self.keywords['locations']):
            return self._handle_location_query(query_lower)
        elif any(kw in query_lower for kw in self.keywords['experience']):
            return self._handle_experience_query(query_lower)
        else:
            return self._handle_general_query(query_lower)
    
    def _handle_single_employee(self, query: str) -> Dict[str, Any]:
        """Handle single employee queries"""
        # Extract name (replaces complex regex)
        name = None
        for prefix in ['show details of ', 'find employee ', 'who is ', 'search for ', 'lookup ']:
            if prefix in query:
                name = query.replace(prefix, '').strip()
                break
        
        if not name:
            # Try to extract name from end patterns
            for suffix in [' details', ' information']:
                if query.endswith(suffix):
                    name = query.replace(suffix, '').strip()
                    break
        
        if not name:
            # Last resort - assume the whole query is a name
            excluded = ['show', 'find', 'employee', 'details', 'who', 'is', 'search', 'for', 'lookup']
            words = [w for w in query.split() if w not in excluded]
            name = ' '.join(words) if words else query
        
        return {
            'action': 'sql_only',
            'query_type': 'single_employee',
            'sql_query': f'''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE (e.display_name ILIKE '%{name}%' 
                   OR e.display_name ILIKE '{name}%' 
                   OR e.display_name ILIKE '%{name}')
            ''',
            'reasoning': f'Searching for employee: {name}'
        }
    
    def _handle_deployment_status(self, status: str, query: str) -> Dict[str, Any]:
        """Handle deployment status queries"""
        return {
            'action': 'sql_only',
            'query_type': f'{status}_employees',
            'sql_query': f'''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE ep.deployment ILIKE '%{status}%'
            ''',
            'reasoning': f'Finding {status} employees'
        }
    
    def _handle_multi_condition_query(self, query: str) -> Dict[str, Any]:
        """Handle complex multi-condition queries (replaces massive regex logic)"""
        conditions = {}
        where_clauses = []
        
        # Extract deployment status (now from projects table)
        if any(term in query for term in ['free pool', 'freepool', 'free', 'available', 'who are available']):
            where_clauses.append("(ep.deployment ILIKE '%free%' OR ep.deployment = 'Free')")
            conditions['deployment'] = 'free'
        elif 'billable' in query:
            where_clauses.append("ep.deployment ILIKE '%billable%'")
            conditions['deployment'] = 'billable'
        elif 'budgeted' in query:
            where_clauses.append("ep.deployment ILIKE '%budgeted%'")
            conditions['deployment'] = 'budgeted'
        elif 'support' in query:
            where_clauses.append("ep.deployment ILIKE '%support%'")
            conditions['deployment'] = 'support'
        
        # Extract skills
        found_skills = [skill for skill in self.keywords['skills'] if skill in query]
        if found_skills:
            skill_conditions = []
            for skill in found_skills:
                skill_conditions.append(f"(e.skill_set ILIKE '%{skill}%' OR e.tech_group ILIKE '%{skill}%')")
            where_clauses.append(f"({' OR '.join(skill_conditions)})")
            conditions['skills'] = found_skills
        
        # Extract location
        found_locations = [loc for loc in self.keywords['locations'] if loc in query]
        if found_locations:
            where_clauses.append(f"e.emp_location ILIKE '%{found_locations[0]}%'")
            conditions['location'] = found_locations[0]
        
        # Extract department
        found_depts = [dept for dept in self.keywords['departments'] if dept in query]
        if found_depts:
            dept_name = found_depts[0].replace(' department', '')
            where_clauses.append(f"e.employee_department ILIKE '%{dept_name}%'")
            conditions['department'] = dept_name
        
        # Extract experience (replaces complex regex patterns)
        exp_min, exp_max = self._extract_experience(query)
        if exp_min is not None or exp_max is not None:
            conditions['experience'] = {'min': exp_min, 'max': exp_max}
        
        # Extract project names
        project_match = None
        for pattern in ['in ', 'project ', 'team of ']:
            if pattern in query:
                parts = query.split(pattern)
                if len(parts) > 1:
                    potential_project = parts[1].split()[0].upper()
                    if '_' in potential_project:  # Looks like project name
                        project_match = potential_project
                        break
        
        if project_match:
            where_clauses.append(f"ep.project_name ILIKE '%{project_match}%'")
            conditions['project'] = project_match
        
        # Build SQL
        base_query = '''
        SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
               ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
        FROM employees e
        LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
        '''
        
        if where_clauses:
            base_query += ' WHERE ' + ' AND '.join(where_clauses)
        

        
        return {
            'action': 'combined',
            'query_type': 'multi_condition',
            'sql_query': base_query,
            'vector_search_terms': query,
            'reasoning': f'Multi-condition search: {conditions}',
            'detected_conditions': conditions
        }
    
    def _extract_experience(self, query: str) -> tuple[Optional[float], Optional[float]]:
        """Extract experience conditions (replaces complex regex)"""
        exp_min = None
        exp_max = None
        
        # Simple number extraction
        numbers = re.findall(r'(\d+(?:\.\d+)?)', query)
        
        if 'more than' in query or 'greater than' in query or 'over' in query:
            if numbers:
                exp_min = float(numbers[0])
        elif 'less than' in query or 'under' in query:
            if numbers:
                exp_max = float(numbers[0])
        elif '+' in query and 'years' in query:
            if numbers:
                exp_min = float(numbers[0])
        elif 'to' in query or '-' in query:
            if len(numbers) >= 2:
                exp_min = float(numbers[0])
                exp_max = float(numbers[1])
        elif 'years' in query and numbers:
            # Exact match
            exp_min = exp_max = float(numbers[0])
        
        return exp_min, exp_max
    
    def _handle_list_all(self) -> Dict[str, Any]:
        """Handle list all queries"""
        return {
            'action': 'sql_only',
            'query_type': 'list_all',
            'sql_query': '''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            ORDER BY e.display_name
            ''',
            'reasoning': 'Listing all employees'
        }
    
    def _handle_skills_query(self, query: str) -> Dict[str, Any]:
        """Handle skills-based queries"""
        found_skills = [skill for skill in self.keywords['skills'] if skill in query]
        
        skill_conditions = []
        for skill in found_skills:
            skill_conditions.append(f"(e.skill_set ILIKE '%{skill}%' OR e.tech_group ILIKE '%{skill}%')")
        
        return {
            'action': 'combined',
            'query_type': 'skills',
            'sql_query': f'''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE {' OR '.join(skill_conditions)}
            ''',
            'vector_search_terms': f"{' '.join(found_skills)} skills programming development",
            'reasoning': f'Finding employees with {found_skills} skills'
        }
    
    def _handle_location_query(self, query: str) -> Dict[str, Any]:
        """Handle location-based queries"""
        found_locations = [loc for loc in self.keywords['locations'] if loc in query]
        location = found_locations[0] if found_locations else 'unknown'
        
        return {
            'action': 'sql_only',
            'query_type': 'location',
            'sql_query': f'''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.emp_location ILIKE '%{location}%'
            ''',
            'reasoning': f'Finding employees in {location}'
        }
    
    def _handle_experience_query(self, query: str) -> Dict[str, Any]:
        """Handle experience-based queries"""
        exp_min, exp_max = self._extract_experience(query)
        
        return {
            'action': 'combined',
            'query_type': 'experience',
            'sql_query': '''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.total_exp IS NOT NULL
            ''',
            'vector_search_terms': query,
            'reasoning': f'Finding employees with experience criteria: min={exp_min}, max={exp_max}',
            'experience_filter': {'min': exp_min, 'max': exp_max}
        }
    
    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries"""
        return {
            'action': 'combined',
            'query_type': 'general',
            'sql_query': '''
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status, ep.deployment, ep.role, ep.occupancy
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            ''',
            'vector_search_terms': query,
            'reasoning': 'General search query'
        }

class EnhancedSearchService:
    """Enhanced search service with RAG + Hybrid Search capabilities"""
    
    def __init__(self):
        # Keep original router for backward compatibility
        self.router = IntelligentQueryRouter()
        self.llm_service = LLMService()
        
        # Initialize components at startup to avoid lazy loading during search
        from ..config.settings import settings
        
        # Initialize hybrid search components at startup
        try:
            if settings.use_hybrid_search.lower() == 'true':
                logger.info("🚀 Initializing hybrid search components at startup...")
                self._hybrid_engine = HybridSearchEngine(settings.gemini_api_key)
                self._use_hybrid_search = getattr(self._hybrid_engine, 'available', False)
                logger.info(f"✅ Hybrid search initialized: {self._use_hybrid_search}")
            else:
                self._hybrid_engine = None
                self._use_hybrid_search = False
                logger.info("⚠️ Hybrid search disabled in settings")
        except Exception as e:
            logger.warning(f"❌ Hybrid search initialization failed: {e}")
            self._hybrid_engine = None
            self._use_hybrid_search = False
        

        
        logger.info("✅ EnhancedSearchService initialized")
    

    
    @property
    def hybrid_engine(self):
        """Get hybrid engine (already initialized at startup)"""
        return self._hybrid_engine
    
    @property
    def use_hybrid_search(self):
        """Get hybrid search status (already determined at startup)"""
        return self._use_hybrid_search
    
    async def process_query(self, query: str, top_k: int = None, search_type: str = "combined") -> ChatResponse:
        """Process query with fast routing and minimal initialization"""
        try:
            # Use hybrid search if enabled, otherwise fallback to original logic
            if self.use_hybrid_search:
                return await self._process_with_hybrid_search(query, top_k, search_type)
            else:
                return await self._process_with_original_logic(query, top_k, search_type)
            
        except Exception as e:
            logger.error(f"Search processing error: {e}")
            # Return error response
            return ChatResponse(
                action="search",
                response="Search temporarily unavailable",
                data=[],
                ui_suggestions=[],
                search_metadata={"search_type": "error", "results_count": 0}
            )
    
    async def _process_with_hybrid_search(self, query: str, top_k: int, search_type: str) -> ChatResponse:
        """Process query using new RAG + Hybrid Search engine"""
        try:
            # Execute hybrid search
            hybrid_results = await self.hybrid_engine.search(query, top_k)
            
            # Extract enriched employee data in the exact format requested
            employee_results = []
            for i, result in enumerate(hybrid_results['results']):
                emp_data = result['employee_data']
                
                # Get projects for this employee
                projects = await self._get_employee_projects(emp_data.get('employee_id', ''))
                
                # Create response in exact format specified (removed all project-level fields from employee level)
                enriched_data = {
                    'employee_id': emp_data.get('employee_id', ''),
                    'display_name': emp_data.get('display_name', ''),
                    'employee_department': emp_data.get('employee_department', ''),
                    'total_exp': emp_data.get('total_exp', ''),
                    'vvdn_exp': emp_data.get('vvdn_exp', ''),
                    'designation': emp_data.get('designation', ''),
                    'tech_group': emp_data.get('tech_group', ''),
                    'emp_location': emp_data.get('emp_location', ''),
                    'skill_set': emp_data.get('skill_set', ''),
                    'selection_reason': emp_data.get('selection_reason', f"Matches search criteria with score {result['final_score']:.3f}"),
                    'ai_rank': i + 1,
                    'ranking_reason': f"This employee matches your search criteria with a confidence score of {result['final_score']:.3f}",
                    'match_score_percentage': int(result['final_score'] * 100),
                    'ai_confidence': result['final_score'],
                    'current_projects': projects
                }
                employee_results.append(enriched_data)
            
            # Build response in original format for UI compatibility
            response_text = self._build_hybrid_response_text(hybrid_results, len(employee_results))
            
            return ChatResponse(
                action="search",
                response=response_text,
                data=employee_results,  # Direct array of employee data
                ui_suggestions=self._build_hybrid_ui_suggestions(hybrid_results, len(employee_results)),
                search_metadata={
                    "search_type": "hybrid_rag",
                    "routing_strategy": "ai_powered",
                    "query_category": "semantic_search",
                    "results_count": len(employee_results),
                    "confidence_score": self._calculate_confidence(hybrid_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fallback to original logic
            return await self._process_with_original_logic(query, top_k, search_type)
    
    async def _process_with_original_logic(self, query: str, top_k: int, search_type: str) -> ChatResponse:
        """Original search logic with semantic classification enhancement"""
        # Use simple router by default for fast response
        routing_decision = self.router.route_query(query)
        
        # Semantic classification removed - using simple router only
        
        # Execute search based on routing
        sql_results = []
        vector_results = []
        
        if routing_decision['action'] in ['sql_only', 'combined']:
            sql_results = await self._execute_sql_search(routing_decision)
            
            # Apply experience filtering if needed
            if routing_decision.get('experience_filter'):
                sql_results = self._filter_by_experience(sql_results, routing_decision['experience_filter'])
        
        # Vector search removed - using only SQL and hybrid search
        
        # Build response (preserves original response format)
        response_text = self._build_response_text(routing_decision, len(sql_results))
        
        # Format results in the exact structure requested
        formatted_results = []
        fused_results = self._fuse_results(sql_results, vector_results)
        
        for i, result in enumerate(fused_results):
            # Get projects for this employee
            projects = await self._get_employee_projects(result.get('employee_id', ''))
            
            formatted_data = {
                'employee_id': result.get('employee_id', ''),
                'display_name': result.get('display_name', ''),
                'employee_department': result.get('employee_department', ''),
                'total_exp': result.get('total_exp', ''),
                'vvdn_exp': result.get('vvdn_exp', ''),
                'designation': result.get('designation', ''),
                'tech_group': result.get('tech_group', ''),
                'emp_location': result.get('emp_location', ''),
                'skill_set': result.get('skill_set', ''),
                'selection_reason': f"Matches search criteria for {routing_decision['query_type']} query",
                'ai_rank': i + 1,
                'ranking_reason': f"Matches search criteria for {routing_decision['query_type']} query",
                'match_score_percentage': 75,
                'ai_confidence': 0.75,
                'current_projects': projects
            }
            formatted_results.append(formatted_data)
        
        return ChatResponse(
            action="search",
            response=response_text,
            data=formatted_results,  # Direct array of employee data
            ui_suggestions=self._build_ui_suggestions(routing_decision, len(sql_results)),
            search_metadata={
                "search_type": search_type,
                "routing_strategy": routing_decision['action'],
                "query_category": routing_decision['query_type'],
                "results_count": len(formatted_results)
            }
        )
    

    
    async def _execute_sql_search(self, routing_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SQL search with performance optimization"""
        try:
            sql_query = routing_decision.get('sql_query')
            if not sql_query:
                return []
            
            # Remove any existing LIMIT to get all employees for ranking
            sql_query = re.sub(r'\s+LIMIT\s+\d+', '', sql_query, flags=re.IGNORECASE)
            
            with get_db_session() as session:
                result = session.execute(text(sql_query))
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"SQL search error: {e}")
            return []
    

    
    def _validate_and_clean_sql(self, sql: str) -> str:
        """Validate and clean SQL query"""
        if not sql or not sql.strip():
            return "SELECT * FROM employees LIMIT 10"
        
        # Remove VectorDB references and other malformed parts
        sql = sql.strip()
        if "OR VectorDB:" in sql:
            sql = sql.split("OR VectorDB:")[0].strip()
        
        # Remove trailing semicolon if present
        if sql.endswith(";"):
            sql = sql[:-1]
        
        # Basic SQL validation
        sql_upper = sql.upper()
        if not any(keyword in sql_upper for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
            return "SELECT * FROM employees LIMIT 10"
        
        return sql
    
    async def _execute_llm_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute LLM-generated SQL query"""
        try:
            if not sql_query or not sql_query.strip():
                return []
            
            # Validate and clean SQL
            clean_sql = self._validate_and_clean_sql(sql_query)
            logger.info(f"Executing cleaned SQL: {clean_sql}")
            
            with get_db_session() as session:
                result = session.execute(text(clean_sql))
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"LLM SQL execution error: {e}")
            return []
    
    def _filter_by_experience(self, results: List[Dict], exp_filter: Dict) -> List[Dict]:
        """Filter results by experience"""
        filtered = []
        exp_min = exp_filter.get('min')
        exp_max = exp_filter.get('max')
        
        for result in results:
            exp_str = result.get('total_exp', '')
            exp_years = self._parse_experience(exp_str)
            
            include = True
            if exp_min is not None and exp_years < exp_min:
                include = False
            if exp_max is not None and exp_years > exp_max:
                include = False
            
            if include:
                result['parsed_experience'] = exp_years
                filtered.append(result)
        
        return filtered
    
    def _parse_experience(self, exp_string: str) -> float:
        """Parse experience string to years"""
        if not exp_string:
            return 0.0
        
        numbers = re.findall(r'(\d+\.?\d*)', str(exp_string).lower())
        return float(numbers[0]) if numbers else 0.0
    
    def _fuse_results(self, sql_results: List[Dict], vector_results: List[Dict]) -> List[Dict]:
        """Fuse SQL and vector results"""
        # For now, just return SQL results
        # TODO: Implement proper result fusion
        return sql_results
    
    def _build_response_text(self, routing_decision: Dict[str, Any], result_count: int) -> str:
        """Build response text based on query type"""
        query_type = routing_decision['query_type']
        
        responses = {
            'single_employee': f"Found employee details" if result_count > 0 else "No employee found with that name",
            'free_employees': f"Found {result_count} employees in free pool" if result_count > 0 else "No free pool employees found",
            'free_pool': f"Found {result_count} available employees" if result_count > 0 else "No available employees found",
            'billable_employees': f"Found {result_count} billable employees" if result_count > 0 else "No billable employees found",
            'budgeted_employees': f"Found {result_count} budgeted employees" if result_count > 0 else "No budgeted employees found",
            'support_employees': f"Found {result_count} support employees" if result_count > 0 else "No support employees found",
            'skills': f"Found {result_count} employees with matching skills" if result_count > 0 else "No employees found with these skills",
            'location': f"Found {result_count} employees in this location" if result_count > 0 else "No employees found in this location",
            'experience': f"Found {result_count} employees matching experience criteria" if result_count > 0 else "No employees found with this experience",
            'multi_condition': f"Found {result_count} employees matching your criteria" if result_count > 0 else "No employees found matching your criteria",
            'list_all': f"Found {result_count} employees in total",
            'general': f"Found {result_count} employees matching your query"
        }
        
        return responses.get(query_type, f"Found {result_count} employees")
    
    def _build_ui_suggestions(self, routing_decision: Dict[str, Any], result_count: int) -> List[Dict[str, Any]]:
        """Build UI suggestions"""
        suggestions = []
        
        if result_count > 0:
            suggestions.extend([
                {"type": "view_employees", "title": "View Employees"},
                {"type": "export_data", "title": "Export Results"}
            ])
        
        return suggestions
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics including AI capabilities"""
        try:
            with get_db_session() as session:
                employee_count = session.execute(text("SELECT COUNT(*) FROM employees")).scalar()
                project_count = session.execute(text("SELECT COUNT(*) FROM employee_projects")).scalar()
                
                dept_stats = session.execute(text("""
                    SELECT employee_department, COUNT(*) as count 
                    FROM employees 
                    GROUP BY employee_department
                """)).fetchall()
                
                location_stats = session.execute(text("""
                    SELECT emp_location, COUNT(*) as count 
                    FROM employees 
                    GROUP BY emp_location
                """)).fetchall()
                
                deployment_stats = session.execute(text("""
                    SELECT ep.deployment, COUNT(DISTINCT e.employee_id) as count 
                    FROM employees e
                    LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
                    WHERE ep.deployment IS NOT NULL
                    GROUP BY ep.deployment
                """)).fetchall()
                
                # AI system statistics
                from ..config.settings import settings
                ai_stats = {
                    "hybrid_search_enabled": self.use_hybrid_search,
                    "gemini_api_configured": bool(settings.gemini_api_key),
                    "vector_db_status": "unknown"
                }
                
                # Check vector database status
                if self.use_hybrid_search:
                    try:
                        # Try to get collection info
                        collection_count = self.hybrid_engine.collection.count()
                        ai_stats["vector_db_status"] = "connected"
                        ai_stats["indexed_employees"] = collection_count
                    except:
                        ai_stats["vector_db_status"] = "error"
                        ai_stats["indexed_employees"] = 0
                
                return {
                    "total_employees": employee_count,
                    "total_projects": project_count,
                    "department_distribution": {dept: count for dept, count in dept_stats},
                    "location_distribution": {loc: count for loc, count in location_stats},
                    "deployment_distribution": {deploy: count for deploy, count in deployment_stats},
                    "ai_capabilities": ai_stats
                }
                
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {"error": str(e)}
    
    async def process_advanced_query(self, request) -> 'QueryResponse':
        """Process advanced query using hybrid search or fallback to LLM integration"""
        try:
            from ..models.schemas import QueryResponse, EmployeeData
            
            # Use hybrid search if enabled
            if self.use_hybrid_search:
                # Execute hybrid search
                hybrid_results = await self.hybrid_engine.search(
                    request.query, 
                    getattr(request, 'max_results', None)
                )
                
                # Apply additional filters if provided
                filtered_results = hybrid_results['results']
                
                if hasattr(request, 'required_skills') and request.required_skills:
                    filtered_results = [
                        r for r in filtered_results 
                        if self._has_required_skills(r['employee_data'], request.required_skills)
                    ]
                
                if hasattr(request, 'min_experience') and request.min_experience:
                    filtered_results = [
                        r for r in filtered_results 
                        if self._meets_min_experience(r['employee_data'], request.min_experience)
                    ]
                
                # Convert to enriched format with ALL employee fields
                employee_data = []
                for result in filtered_results:
                    emp = result['employee_data']
                    
                    # Get projects for this employee
                    projects = await self._get_employee_projects(emp.get('employee_id', ''))
                    
                    # Include ALL available employee fields (removed all project-level fields from employee level)
                    enriched_emp = {
                        'employee_id': emp.get('employee_id', ''),
                        'display_name': emp.get('display_name', ''),
                        'employee_department': emp.get('employee_department', ''),
                        'tech_group': emp.get('tech_group', ''),
                        'vvdn_exp': emp.get('vvdn_exp', ''),
                        'total_exp': emp.get('total_exp', ''),
                        'skill_set': emp.get('skill_set', ''),
                        'emp_location': emp.get('emp_location', ''),
                        'designation': emp.get('designation', ''),
                        'selection_reason': emp.get('selection_reason', ''),
                        'ai_rank': filtered_results.index(result) + 1,
                        'ranking_reason': f"AI-powered match with score {result.get('final_score', 0):.3f}",
                        'match_score_percentage': int(result.get('final_score', 0) * 100),
                        'ai_confidence': result.get('final_score', 0),
                        'current_projects': projects
                    }
                    employee_data.append(enriched_emp)
                
                # Generate AI-powered response
                chat_response = f"Found {len(employee_data)} employees using AI-powered search. "
                if hybrid_results.get('ranking_explanation'):
                    chat_response += f"Key insights: {'; '.join(hybrid_results['ranking_explanation'][:2])}"
                
                return QueryResponse(
                    chat_response=chat_response,
                    data=employee_data,
                    ui_actions=["view_results", "export_data", "refine_search"]
                )
            
            else:
                # Fallback to original LLM integration logic
                llm_response = await self.llm_service.process_query(request.query)
                
                # Check if LLM suggests vector search but hybrid is disabled
                if llm_response.search_strategy == "vector_only" and not self.use_hybrid_search:
                    # Convert to a basic SQL query for free pool
                    if "free" in request.query.lower():
                        llm_response.sql = "SELECT * FROM employees WHERE deployment ILIKE '%free%' LIMIT 20"
                    else:
                        llm_response.sql = "SELECT * FROM employees LIMIT 20"
                
                sql_results = await self._execute_llm_sql(llm_response.sql)
                
                # Apply additional filters if provided
                if hasattr(request, 'required_skills') and request.required_skills:
                    sql_results = self._filter_by_skills(sql_results, request.required_skills)
                
                if hasattr(request, 'min_experience') and request.min_experience:
                    sql_results = self._filter_by_min_experience(sql_results, request.min_experience)
                
                # Limit results
                max_results = getattr(request, 'max_results', 20)
                sql_results = sql_results[:max_results]
                
                # Convert to comprehensive employee data format (removed role and status from employee level)
                employee_data = []
                for result in sql_results:
                    # Get projects for this employee
                    projects = await self._get_employee_projects(result.get('employee_id', ''))
                    
                    # Include ALL available employee fields (removed all project-level fields from employee level)
                    enriched_emp = {
                        'employee_id': result.get('employee_id', ''),
                        'display_name': result.get('display_name', ''),
                        'employee_department': result.get('employee_department', ''),
                        'tech_group': result.get('tech_group', ''),
                        'vvdn_exp': result.get('vvdn_exp', ''),
                        'total_exp': result.get('total_exp', ''),
                        'skill_set': result.get('skill_set', ''),
                        'emp_location': result.get('emp_location', ''),
                        'designation': result.get('designation', ''),
                        'selection_reason': f"Matches query criteria",
                        'ai_rank': sql_results.index(result) + 1,
                        'ranking_reason': f"Matches query criteria",
                        'match_score_percentage': 70,
                        'ai_confidence': 0.70,
                        'current_projects': projects
                    }
                    employee_data.append(enriched_emp)
                
                return QueryResponse(
                    chat_response=llm_response.chat_response,
                    data=employee_data,
                    ui_actions=llm_response.ui_actions
                )
            
        except Exception as e:
            logger.error(f"Advanced query processing error: {e}")
            from ..models.schemas import QueryResponse
            return QueryResponse(
                chat_response=f"Error processing query: {str(e)}",
                data=[],
                ui_actions=["error"]
            )
    
    def _has_required_skills(self, emp_data: Dict, required_skills: List[str]) -> bool:
        """Check if employee has required skills"""
        emp_skills = (emp_data.get('skill_set', '') + ' ' + emp_data.get('tech_group', '')).lower()
        return all(skill.lower() in emp_skills for skill in required_skills)
    
    def _meets_min_experience(self, emp_data: Dict, min_exp: float) -> bool:
        """Check if employee meets minimum experience requirement"""
        exp_str = emp_data.get('total_exp', '')
        exp_years = self._parse_experience(exp_str)
        return exp_years >= min_exp
    
    def _filter_by_skills(self, results: List[Dict], required_skills: List[str]) -> List[Dict]:
        """Filter results by required skills"""
        filtered = []
        for result in results:
            skill_set = result.get('skill_set', '').lower()
            tech_group = result.get('tech_group', '').lower()
            
            has_skills = all(
                skill.lower() in skill_set or skill.lower() in tech_group 
                for skill in required_skills
            )
            
            if has_skills:
                filtered.append(result)
        
        return filtered
    
    def _filter_by_min_experience(self, results: List[Dict], min_exp: float) -> List[Dict]:
        """Filter results by minimum experience"""
        filtered = []
        for result in results:
            exp_str = result.get('total_exp', '')
            exp_years = self._parse_experience(exp_str)
            
            if exp_years >= min_exp:
                filtered.append(result)
        
        return filtered
    
    def _build_hybrid_response_text(self, hybrid_results: Dict, result_count: int) -> str:
        """Build response text for hybrid search results"""
        if result_count == 0:
            return "No employees found matching your criteria using AI-powered search."
        
        strategy = hybrid_results.get('search_strategy', 'hybrid')
        explanations = hybrid_results.get('ranking_explanation', [])
        
        response = f"Found {result_count} employees using AI-powered hybrid search."
        
        if explanations:
            response += f" Top matches: {'; '.join(explanations[:2])}"
        
        return response
    
    def _build_hybrid_ui_suggestions(self, hybrid_results: Dict, result_count: int) -> List[Dict[str, Any]]:
        """Build UI suggestions for hybrid search"""
        suggestions = []
        
        if result_count > 0:
            suggestions.extend([
                {"type": "view_employees", "title": "View AI-Ranked Employees"},
                {"type": "export_data", "title": "Export Results"},
                {"type": "refine_search", "title": "Refine Search Criteria"}
            ])
            
            # Add AI-specific suggestions
            if hybrid_results.get('parsed_query'):
                suggestions.append({
                    "type": "view_ai_insights", 
                    "title": "View AI Search Insights"
                })
        
        return suggestions
    
    def _calculate_confidence(self, hybrid_results: Dict) -> float:
        """Calculate confidence score for hybrid search results"""
        results = hybrid_results.get('results', [])
        if not results:
            return 0.0
        
        # Average of top 3 scores
        top_scores = [r.get('final_score', 0.5) for r in results[:3]]
        return sum(top_scores) / len(top_scores) if top_scores else 0.5
    
    async def _get_employee_projects(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get projects for a specific employee"""
        try:
            if not employee_id:
                return []
            
            # Add VVDN prefix if not present
            full_employee_id = f"VVDN/{employee_id}" if not employee_id.startswith("VVDN/") else employee_id
            
            with get_db_session() as session:
                projects_result = session.execute(
                    text("""
                        SELECT project_name, customer, project_department, 
                               project_industry, project_status, occupancy,
                               start_date, end_date, role, deployment, project_extended_end_date, project_committed_end_date
                        FROM employee_projects 
                        WHERE employee_id = :employee_id
                        ORDER BY created_at DESC
                    """),
                    {"employee_id": full_employee_id}
                )
                
                projects = []
                for row in projects_result:
                    projects.append({
                        "project_name": row.project_name,
                        "customer": row.customer,
                        "project_department": row.project_department,
                        "project_industry": row.project_industry,
                        "project_status": row.project_status,
                        "occupancy": row.occupancy or 0,
                        "role": row.role,
                        "deployment": row.deployment,
                        "start_date": str(row.start_date) if row.start_date else None,
                        "end_date": str(row.end_date) if row.end_date else None,
                        "project_extended_end_date": str(row.project_extended_end_date) if row.project_extended_end_date else None,
                        "project_committed_end_date": str(row.project_committed_end_date) if row.project_committed_end_date else None
                    })
                
                return projects
                
        except Exception as e:
            logger.error(f"Error getting employee projects: {e}")
            return []
    
    async def index_employees_for_search(self) -> Dict[str, Any]:
        """Index employees in vector database for semantic search"""
        try:
            result = await self.hybrid_engine.index_employees()
            return result
        except Exception as e:
            logger.error(f"Employee indexing error: {e}")
            return {"status": "error", "message": str(e)}
    

    
    async def get_debug_data(self) -> Dict[str, Any]:
        """Get debug data including hybrid search status"""
        try:
            with get_db_session() as session:
                employees = session.execute(text("SELECT * FROM employees LIMIT 5")).fetchall()
                
                from ..config.settings import settings
                debug_data = {
                    "employees_sample": [dict(emp._mapping) for emp in employees],
                    "sample_count": len(employees),
                    "hybrid_search_enabled": False,  # Disabled for search operations
                    "gemini_api_configured": bool(settings.gemini_api_key)
                }
                
                return debug_data
                
        except Exception as e:
            return {"error": str(e)}