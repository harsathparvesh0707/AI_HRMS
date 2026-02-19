"""
AI Search Service - Main orchestrator for AI-powered search
"""
import logging
import time
from typing import Dict, Any, List
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.project_repository import ProjectRepository
from .ai_ranking_service import AIRankingService
from .compression_service import compression_service
from .query_parsing_service import QueryParsingService
from .hybrid_search_engine import HybridSearchEngine
from ..config.settings import get_settings
from .cache_manager import cache_manager
from ..celery.tasks import save_ranked_search_cache


import asyncio
from difflib import SequenceMatcher
import json

logger = logging.getLogger(__name__)  

class AISearchService:
    """Main AI search orchestrator - replaces EnhancedSearchService"""
    
    def __init__(self):
        self.employee_repo = EmployeeRepository()
        self.project_repo = ProjectRepository()
        self.ranking_service = AIRankingService()
        self.compression_service = compression_service
        self.query_parser = QueryParsingService()
        
        # Initialize hybrid engine with Gemini API key
        settings = get_settings()
        self.hybrid_engine = HybridSearchEngine(gemini_api_key=settings.gemini_api_key)

    
    async def process_query(self, query: str, top_k: int = None, search_type: str = "combined") -> Dict[str, Any]:
        """Hybrid approach: Enhanced search + AI ranking"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting Hybrid AI search for query: '{query}' (top_k: {top_k})")
            
            # Step 1: Semantic Understanding - Parse query into structured format
            parsed_query = await self.hybrid_engine._parse_query_with_llm(query)
            
            # Step 2: Multi-Modal Retrieval
            sql_results = await self.hybrid_engine._sql_search(parsed_query)
            
            # For skill+experience queries, use only SQL results (strict filtering)
            if (parsed_query.get('strict_filter') or parsed_query.get('deployment') or 
                parsed_query.get('project_search') or 
                (parsed_query.get('skills') and parsed_query.get('experience_min'))):
                merged_results = sql_results
            else:
                vector_results = await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
                # Step 3: Merge and deduplicate results
                merged_results = self.hybrid_engine._merge_results(vector_results, sql_results, [])
            
            logger.info(f"✅ Step 1-2 Complete: Found {len(merged_results)} employees without business ranking")
            
            if not merged_results:
                logger.warning("No employees found by multi-modal retrieval")
                return self._build_response([], {})
            
            # Step 3: Extract employee data from search results
            employee_data_list = [result['employee_data'] for result in merged_results if 'employee_data' in result]
            logger.info(f"📊 Extracted {len(employee_data_list)} employee records from search results")
            
            # Step 4: Compress filtered employees for AI processing
            # Extract employee IDs and get compressed batch
            employee_ids = [emp.get('employee_id', '').replace('VVDN/', '') for emp in employee_data_list]
            compressed_employees = await self.compression_service.get_compressed_batch(employee_ids)
            logger.info(f"✅ Step 4 Complete: Compressed {len(compressed_employees)} filtered profiles")
            
            # Step 5: AI-powered final ranking
            logger.info(f"🤖 Step 5 Starting: AI ranking {len(compressed_employees)} filtered employees")
            if top_k:
                logger.info(f"📊 Will return top {top_k} results after AI ranking")
            
            final_ranked_results = await self.ranking_service.rank_employees(
                query=query,
                parsed_query=parsed_query,
                compressed_employees=compressed_employees,
                top_k=top_k
            )
            logger.info(f"✅ Step 5 Complete: AI ranking produced {len(final_ranked_results)} final results")
            
            # Step 6: Build response
            response = self._build_response(final_ranked_results, parsed_query)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Step 6 Complete: Response built with {len(final_ranked_results)} results")
            logger.info(f"🏁 Hybrid AI Search Complete: '{query}' processed in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Hybrid AI search error: {e}")
            raise
    
    async def process_search_only(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Search-only (no ranking): 
        Decides between SQL-only, Vector-only, or Hybrid modes based on query structure.
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting search-only for query: '{query}'")

            # Step 1️⃣: Parse query (cached LLM result)
            parsed_query = await self._cached_parse_query(query)
            if not parsed_query:
                logger.warning("⚠️ Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            # Step 2️⃣: Always start with SQL search (fast recall)
            sql_results = await self.hybrid_engine._sql_search_loose(parsed_query)

            # Step 3️⃣: Decide Search Mode -----------------------------------
            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            # Generic heuristic — if user asked something vague or conversational
            is_generic_query = not has_structured_filters and len(query.split()) <= 5

            if has_structured_filters:
                search_mode = "sql"
            elif is_generic_query:
                search_mode = "vector"
            else:
                search_mode = "hybrid"

            logger.info(f"🧩 Search mode decided: {search_mode.upper()} for query='{query}'")

            # Step 4️⃣: Execute based on mode
            if search_mode == "sql":
                merged_results = sql_results

            elif search_mode == "vector":
                vector_results = await self.hybrid_engine._vector_search(
                    query, (top_k * 2) if top_k else None
                )
                merged_results = vector_results  # no merge needed

            else:  # hybrid
                vector_results = await self.hybrid_engine._vector_search(
                    query, (top_k * 2) if top_k else None
                )
                merged_results = self.hybrid_engine._merge_results(
                    vector_results, sql_results, []
                )

            # Step 5️⃣: Extract employee data
            employee_data_list = [
                result["employee_data"]
                for result in merged_results
                if "employee_data" in result
            ]

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Search-only complete: {len(employee_data_list)} results in {duration}s")

            return {
                "action": f"search_only_results_{search_mode}",
                "response": f"Found {len(employee_data_list)} employees ({search_mode.upper()} mode)",
                "data": employee_data_list,
                "total_results": len(employee_data_list),
                "parsed_query": parsed_query,
                "processing_time": duration
            }

        except Exception as e:
            logger.error(f"❌ process_search_only error: {e}")
            return {
                "action": "search_only_results_error",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }
        

    async def process_search_and_rank(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Search-only (no ranking): 
        Decides between SQL-only, Vector-only, or Hybrid modes based on query structure.
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting search-only for query: '{query}'")

            # Step 1️⃣: Parse query (cached LLM result)
            parsed_query = await self._cached_parse_query(query)
            if not parsed_query:
                logger.warning("⚠️ Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            # Step 2️⃣: Always start with SQL search (fast recall)
            sql_results = await self.hybrid_engine._sql_search_loose(parsed_query)

            # Step 3️⃣: Decide Search Mode -----------------------------------
            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = sql_results if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            # Step 6️⃣: Fetch compressed representations
            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)

             # Step 5️⃣ Rule-based pre-ranking

            logger.info(f"🧠 Starting full PDP-based reasoning rank for {len(enriched)} employees...")
            final_ranked = await self.ranking_service.llm_progressive_rank_single(query, parsed_query, enriched, top_k)

            # Map ranked employee IDs back to full employee details
            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []
            
            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()
                    
                    # Remove unwanted fields
                    fields_to_remove = ['pm', 'deployments', 'selection_reason']
                    for field in fields_to_remove:
                        full_emp_data.pop(field, None)
                    
                    # Add projects list with details
                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)
                    
                    # Add ranking metadata to employee data
                    full_emp_data.update({
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_score": ranked_emp.get("ai_score")
                    })
                    ranked_with_details.append(full_emp_data)

            # Sort by ai_score in descending order
            ranked_with_details.sort(key=lambda x: x.get('ai_score', 0), reverse=True)

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full ranking pipeline complete in {duration:.2f}s")

            return {
            "action": f"search_with_rank_{mode}",
            "response": f"Ranked {len(ranked_with_details)} employees",
            "data": ranked_with_details,
            "total_results": len(ranked_with_details),
            "parsed_query": parsed_query,
            "processing_time": duration
        }

        except Exception as e:
            logger.error(f"❌ process_search_and_rank error: {e}")
            return {
                "action": "search_only_results_error",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }


    async def process_search_and_rank_with_criteria(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Full search + LLM-based ranking with multi-criteria reasoning.
        Combines SQL/Hybrid search, compression, and PDP reasoning in one flow.
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🔍 Starting search-with-rank for query: '{query}'")

            # Step 1️⃣: Parse query (cached LLM result)
            parsed_query = await self._cached_parse_query(query)
            if not parsed_query:
                logger.warning("⚠️ Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            # Step 2️⃣: Always start with SQL search (fast recall)
            sql_results = await self.hybrid_engine._sql_search_loose(parsed_query)



            # Step 3️⃣: Mode decision
            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = sql_results if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            # 🧭 Step 5️⃣: Shortcut — employee_name-only queries
            has_only_name = (
                parsed_query.get("employee_name")
                and all(
                    not parsed_query.get(k)
                    for k in [
                        "skills", "context", "department", "deployment",
                        "project", "project_search", "location"
                    ]
                )
            )

            if has_only_name:
                logger.info("🧭 Employee name-only search detected — skipping compression & ranking.")
                enriched_results = []

                for emp in employee_data_list:
                    emp_copy = emp.copy()
                    emp_id = emp_copy.get("employee_id")

                    # Add projects directly
                    emp_copy["projects"] = self.ranking_service._get_employee_projects(emp_id)

                    # Remove unnecessary heavy fields
                    for f in ['pm', 'deployments', 'selection_reason']:
                        emp_copy.pop(f, None)

                    enriched_results.append(emp_copy)

                duration = round(time.time() - start_time, 2)
                logger.info(f"✅ Employee-only lookup complete in {duration:.2f}s")

                return {
                    "action": "search_employee_details",
                    "response": f"Found {len(enriched_results)} matching employee(s)",
                    "data": enriched_results,
                    "total_results": len(enriched_results),
                    "parsed_query": parsed_query,
                    "processing_time": duration,
                    "employee_search": True
                }

            # Step 4️⃣: Fetch compressed representations
            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)

            # Step 5️⃣: LLM reasoning rank with criteria
            logger.info(f"🧠 Starting PDP-based multi-criteria ranking for {len(enriched)} employees...")
            final_ranked = await self.ranking_service.llm_progressive_rank_single_with_criteria_fix(
                query, parsed_query, enriched, top_k
            )

            # Step 6️⃣: Merge full employee details
            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []

            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()

                    # Remove unnecessary fields
                    for f in ['pm', 'deployments', 'selection_reason']:
                        full_emp_data.pop(f, None)

                    # Add projects
                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)

                    # Attach AI metadata
                    full_emp_data.update({
                        "ai_score": ranked_emp.get("ai_score"),
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_criteria": ranked_emp.get("ai_criteria", {})
                    })
                    ranked_with_details.append(full_emp_data)

            # Sort descending by AI score
            ranked_with_details.sort(key=lambda x: x.get('ai_score', 0), reverse=True)

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full search + ranking pipeline complete in {duration:.2f}s")

            return {
                "action": f"Employee search_with_rank_{mode}",
                "response": f"Ranked {len(ranked_with_details)} employees",
                "data": ranked_with_details,
                "total_results": len(ranked_with_details),
                "parsed_query": parsed_query,
                "processing_time": duration,
                "employee_search": False
            }

        except Exception as e:
            logger.error(f"❌ process_search_and_rank error: {e}", exc_info=True)
            return {
                "action": "search_with_rank_error",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }


    async def process_search_only_enhanced(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        PARALLEL Enhanced search-only pipeline with optimized performance.
        Uses parallel processing for maximum speed.
        """
        start_time = time.time()
        try:
            logger.info(f"⚡ Starting PARALLEL enhanced search-only for query: '{query}'")

            # Step 1: Cached parse (calls your existing LLM parse internally)
            parsed_query = await self._cached_parse_query(query)

            # Step 2: PARALLEL Multi-Modal Retrieval
            import asyncio
            
            # Always start SQL search
            sql_task = asyncio.create_task(self.hybrid_engine._sql_search(parsed_query))
            
            # Decide whether to use vector search based on conditions
            if (parsed_query.get('strict_filter') or parsed_query.get('deployment') or
                parsed_query.get('project_search') or
                (parsed_query.get('skills') and parsed_query.get('experience_min'))):
                # Strict filtering: only SQL results
                sql_results = await sql_task
                merged_results = sql_results
            else:
                # PARALLEL: Run vector search concurrently with SQL
                vector_task = asyncio.create_task(self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None))
                
                # Wait for both searches to complete in parallel
                sql_results, vector_results = await asyncio.gather(sql_task, vector_task)
                
                # Merge results
                merged_results = self.hybrid_engine._merge_results(vector_results, sql_results, [], parsed_query)

            # Step 3: PARALLEL Post-filtering
            filter_task = asyncio.create_task(self._async_filter_merged_results(merged_results, parsed_query))
            relevance_task = asyncio.create_task(self._async_apply_skill_group_relevance(merged_results, parsed_query))
            
            # Wait for both filtering operations to complete
            filtered_results, relevance_results = await asyncio.gather(filter_task, relevance_task)
            
            # Combine filtering results (intersection of both filters)
            final_results = []
            filtered_ids = {r['employee_data']['employee_id'] for r in filtered_results if 'employee_data' in r}
            
            for result in relevance_results:
                if result.get('employee_data', {}).get('employee_id') in filtered_ids:
                    final_results.append(result)

            # Step 4: Optionally trim to top_k (if requested)
            if top_k:
                final_results = final_results[:top_k]

            processing_time = time.time() - start_time
            logger.info(f"⚡ PARALLEL Enhanced search-only complete: {len(final_results)} results in {processing_time:.2f}s")

            # Return same schema as your existing method
            employee_data_list = [item['employee_data'] for item in final_results if 'employee_data' in item]
            return {
                "action": "search_only_results_parallel",
                "response": f"Found {len(employee_data_list)} employees from parallel enhanced search filtering",
                "data": employee_data_list,
                "total_results": len(employee_data_list),
                "parsed_query": parsed_query,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Parallel Enhanced search-only error: {e}")
            raise


    async def process_search_only_enhanced2(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Step 1: Optimized Query → SQL → Filter → Output
        Streamlined (no vector search): relies on smart SQL + reasoning-based ranking.
        """
        start_time = time.time()
        try:
            logger.info(f"⚡ Enhanced SQL-only search start: '{query}'")

            # 1️⃣ Parse query (with Redis cache)
            parsed_query = await self._cached_parse_query(query)
            if not parsed_query:
                return {"data": [], "total_results": 0, "parsed_query": {}, "processing_time": 0}

            # 2️⃣ Expand context/skills once (shared cache)
            expansions = await self._get_combined_expansions(parsed_query)
            parsed_query["expansions"] = expansions

            # 3️⃣ SQL search only
            sql_results = await self.hybrid_engine._sql_search_optimized(parsed_query)

            # 4️⃣ Optional: post-filter results (removes non-technical, unrelated)
            final_results = await self._async_filter_merged_results_new(sql_results, parsed_query)

            # 5️⃣ Trim results
            if top_k:
                final_results = final_results[:top_k]

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Enhanced SQL-only search complete: {len(final_results)} results in {duration}s")

            return {
                "action": "search_only_results_sql",
                "response": f"Found {len(final_results)} employees",
                "data": [r["employee_data"] for r in final_results],
                "total_results": len(final_results),
                "parsed_query": parsed_query,
                "processing_time": duration
            }

        except Exception as e:
            logger.error(f"❌ process_search_only_enhanced2 error: {e}")
            return {"data": [], "total_results": 0, "error": str(e)}

    async def _async_filter_merged_results(self, merged_results: List[Dict], parsed_query: Dict) -> List[Dict]:
        """Async wrapper for filtering merged results"""
        return self._filter_merged_results(merged_results, parsed_query)
    
    async def _async_filter_merged_results_new(self, merged_results: List[Dict], parsed_query: Dict) -> List[Dict]:
        """Async wrapper for filtering merged results"""
        return self._filter_merged_results_new(merged_results, parsed_query)
    
    async def _async_apply_skill_group_relevance(self, merged_results: List[Dict], parsed_query: Dict) -> List[Dict]:
        """Async wrapper for applying skill group relevance"""
        return self._apply_skill_group_relevance(merged_results, parsed_query)
    
    async def process_advanced_query(self, request) -> Dict[str, Any]:
        """Advanced query processing"""
        return await self.process_query(
            query=request.query,
            top_k=request.max_results or 50
        )
    
    def _build_response(self, ranked_results: List[Dict], parsed_query: Dict) -> Dict[str, Any]:
        """Build search response"""
        response_msg = self._generate_response_message(ranked_results, parsed_query)
        
        return {
            "action": "search_results",
            "response": response_msg,
            "data": ranked_results,
            "total_results": len(ranked_results),
            "query_type": parsed_query.get("query_type", "general"),
            "ui_suggestions": self._generate_ui_suggestions(parsed_query),
            "search_metadata": {
                "search_strategy": "ai_ranking",
                "parsed_query": parsed_query,
                "processing_time": "fast"
            }
        }
    
    def _generate_response_message(self, results: List[Dict], parsed_query: Dict) -> str:
        """Generate intelligent response message"""
        count = len(results)
        query_type = parsed_query.get("query_type", "general")
        
        if query_type == "skill_search":
            skills = ", ".join(parsed_query.get("required_skills", []))
            return f"Found {count} employees with {skills} skills using AI-powered ranking"
        elif query_type == "project_search":
            domain = parsed_query.get("project_domain", "relevant")
            return f"Found {count} employees with {domain} project experience"
        elif query_type == "availability_search":
            return f"Found {count} available employees matching your capacity requirements"
        elif parsed_query.get("multi_intent"):
            return f"Found {count} employees matching your multi-criteria search using 4-stage AI analysis"
        else:
            return f"Found {count} employees using intelligent AI ranking"
    
    def _generate_ui_suggestions(self, parsed_query: Dict) -> List[Dict[str, str]]:
        """Generate UI suggestions based on query analysis"""
        suggestions = []
        
        if parsed_query.get("required_skills"):
            suggestions.append({
                "type": "refine_skills",
                "text": "Refine by specific skill level",
                "action": "add_experience_filter"
            })
        
        if parsed_query.get("project_domain"):
            suggestions.append({
                "type": "expand_domain",
                "text": "Include related domains",
                "action": "broaden_domain_search"
            })
        
        if not parsed_query.get("availability_required"):
            suggestions.append({
                "type": "add_availability",
                "text": "Filter by availability",
                "action": "add_capacity_filter"
            })
        
        return suggestions
    

    async def _cached_parse_query(self, query: str) -> Dict[str, Any]:
        """
        Use existing Redis cache system for LLM query parsing.
        """
        if not query:
            return {}
        
        # Use existing Redis cache through embedding service
        if hasattr(self.hybrid_engine, 'embedding_cache') and self.hybrid_engine.embedding_cache and self.hybrid_engine.embedding_cache.available:
            try:
                # Check Redis cache for parsed query
                import hashlib
                cache_key = f"parsed_query:{hashlib.md5(query.lower().encode()).hexdigest()}"
                
                cached_result = self.hybrid_engine.embedding_cache.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"🎯 Redis parse cache HIT: {query[:30]}...")
                    return json.loads(cached_result)
                
                # Cache miss - call LLM
                logger.info(f"🔄 Redis parse cache MISS - calling LLM: {query[:30]}...")
                parsed = await self.hybrid_engine._parse_query_with_llm(query)
                
                # Cache in Redis with 5 minute TTL
                self.hybrid_engine.embedding_cache.redis_client.setex(
                    cache_key, 300, json.dumps(parsed)
                )
                
                return parsed
                
            except Exception as e:
                logger.warning(f"Redis cache failed, falling back to direct LLM: {e}")
        
        # Fallback to direct LLM call if Redis unavailable
        return await self.hybrid_engine._parse_query_with_llm(query)


    def _compute_relevance(self, skill: str, tech_group: str) -> float:
        """
        Lightweight fuzzy similarity between skill and tech_group keywords.
        Returns 0..1 score. Use only for quick pre-filtering.
        """
        if not skill or not tech_group:
            return 0.0
        skill = skill.lower().strip()
        tech_group = tech_group.lower().replace('-', ' ').strip()
        parts = [p for p in tech_group.split() if p]
        if not parts:
            return 0.0
        scores = [SequenceMatcher(None, skill, p).ratio() for p in parts]
        return max(scores)


    def _is_skill_relevant(self, employee: Dict[str, Any], query_skills: List[str], threshold: float = 0.45) -> bool:
        """
        Decide if this employee is relevant to the query skills.
        Rules:
        - Employee must have at least one of the query skills in their skill_set (fast check).
        - AND tech_group fuzzy similarity must be above threshold OR employee has exact skill token.
        This avoids hardcoding skill->tech_group maps.
        """
        if not query_skills:
            # if no skill in query, we keep the employee (other filters may apply)
            return True

        emp_skill_text = (employee.get("skill_set") or "").lower()
        tech_group = (employee.get("tech_group") or "").lower()

        # quick token check: if employee doesn't even have any query skill tokens, reject early
        has_any_skill_token = any(q.lower() in emp_skill_text for q in query_skills)
        if not has_any_skill_token:
            return False

        # compute fuzzy relevance for each query skill against tech_group and against skill tokens
        for q in query_skills:
            q_low = q.lower().strip()
            # exact in skill_set is a strong signal
            if q_low in emp_skill_text:
                return True
            # fuzzy match with tech_group
            rel = self._compute_relevance(q_low, tech_group)
            if rel >= threshold:
                return True

        # fallback: if skill token present but tech_group low similarity, still accept if skill_token exists
        return has_any_skill_token


    def _determine_primary_deployment_from_projects(self, employee_row: Dict[str, Any], projects: List[Dict[str, Any]] = None) -> str:
        """
        Determine primary deployment status based on attached projects (if available).
        Priority order: Billable > Budgeted > Shadow > FreePool
        If `projects` not provided, try to find project info inside employee_row (if joined).
        Returns one of: 'billable', 'budgeted', 'shadow', 'free', 'unknown'
        """
        try:
            if projects is None:
                projects = employee_row.get("projects") or []

            priority_order = ["billable", "budgeted", "shadow", "free", "support"]

            found = {}
            for p in projects:
                dep = str(p.get("deployment", "") or "").lower().strip()
                if not dep:
                    continue
                # normalize common labels
                if "bill" in dep:
                    key = "billable"
                elif "budget" in dep:
                    key = "budgeted"
                elif "shadow" in dep:
                    key = "shadow"
                elif "free" in dep or "pool" in dep:
                    key = "free"
                elif "support" in dep:
                    key = "support"
                else:
                    key = dep
                found[key] = found.get(key, 0) + 1

            # pick highest priority that is present
            for p in priority_order:
                if found.get(p):
                    return p
            # fallback: if nothing matched, attempt to read a top-level field
            top = (employee_row.get("deployment") or "").lower()
            if top:
                if "bill" in top:
                    return "billable"
                elif "budget" in top:
                    return "budgeted"
                elif "shadow" in top:
                    return "shadow"
                elif "free" in top:
                    return "free"
            return "unknown"
        except Exception as e:
            self.logger = getattr(self, "logger", logging.getLogger(__name__))
            self.logger.error(f"determine_primary_deployment error: {e}")
            return "unknown"

    def _apply_skill_group_relevance(self, filtered_results: List[Dict[str, Any]], parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Optional post-filter: further narrows results based on query skill <-> tech_group relevance map.
        Works dynamically (no hardcoding specific query).
        """
        query_skills = parsed_query.get("skills") or []
        if isinstance(query_skills, str):
            query_skills = [query_skills]
        if not query_skills:
            return filtered_results

        # universal map: skill keyword -> relevant tech group tags
        skill_group_map = {
            "java": ["backend", "fullstack", "spring", "microservice", "android"],
            "python": ["backend", "ml", "data", "ai"],
            "react": ["frontend", "fullstack"],
            "angular": ["frontend", "fullstack"],
            "node": ["backend", "fullstack"],
            "flutter": ["mobile", "frontend"],
            "kotlin": ["mobile", "android"],
            "sql": ["backend", "data"],
            "c++": ["embedded", "firmware", "vision"],
        }

        # derive relevant tags dynamically
        relevant_tags = set()
        for skill in query_skills:
            for key, tags in skill_group_map.items():
                if key in skill.lower():
                    relevant_tags.update(tags)

        if not relevant_tags:
            return filtered_results

        def is_relevant(emp):
            tg = (emp.get("tech_group") or "").lower()
            return any(tag in tg for tag in relevant_tags)

        refined = [r for r in filtered_results if is_relevant(r.get("employee_data", {}))]
        return refined if refined else filtered_results


    def _filter_merged_results(self, merged_results: List[Dict[str, Any]], parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Post-filter merged results by:
        - skill relevance (dynamic)
        - optionally location (exact/ILIKE style)
        - remove non-technical roles
        Returns filtered list preserving original structure.
        """
        filtered = []
        query_skills = parsed_query.get("skills") or parsed_query.get("skill") or []
        # ensure list
        if isinstance(query_skills, str):
            query_skills = [query_skills]

        for item in merged_results:
            emp = item.get("employee_data") or {}
            designation = (emp.get("designation") or "").lower().strip()
            # filter out obvious non-technical roles
            if designation in ['manager', 'director', 'vp', 'ceo', 'cto', 'admin', 'hr', 'receptionist']:
                continue

            # skill relevance
            if not self._is_skill_relevant(emp, query_skills):
                continue

            # location filter if present in parsed query
            loc = parsed_query.get("location")
            if loc:
                emp_loc = (emp.get("emp_location") or "").lower()
                if loc.lower() not in emp_loc:
                    continue

            # determine primary deployment from detected project info (if employee_data includes list of projects)
            projects = emp.get("projects") or emp.get("employee_projects") or []
            primary_dep = self._determine_primary_deployment_from_projects(emp, projects)
            emp['primary_deployment'] = primary_dep

            # nice to have: attach selection_reason if not present
            if not item.get("match_score"):
                item["match_score"] = 1.0

            # if not emp.get("selection_reason"):
            #     emp["selection_reason"] = self._generate_selection_reason(emp, parsed_query) if hasattr(self, "_generate_selection_reason") else ""

            # keep the original item but update employee_data reference
            new_item = dict(item)
            new_item["employee_data"] = emp
            filtered.append(new_item)

        return filtered


    async def _get_combined_expansions(self, parsed_query: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        One-stop expansion for both skills & context.
        Avoids duplicate semantic + alias lookups.
        """
        skills = parsed_query.get("skills", [])
        context = parsed_query.get("context")

        if not skills and not context:
            return {}

        # Run expansions in parallel
        import asyncio
        tasks = []
        if skills:
            tasks.append(asyncio.create_task(self.hybrid_engine._get_semantic_skills(skills)))
        if context:
            tasks.append(asyncio.create_task(self.hybrid_engine._expand_context(context)))

        results = await asyncio.gather(*tasks)
        semantic_skills = results[0] if skills else []
        context_terms = results[-1] if context else []

        return {"semantic_skills": semantic_skills, "context_terms": context_terms}



    def _filter_merged_results_new(
    self, merged_results: List[Dict[str, Any]], parsed_query: Dict[str, Any]
) -> List[Dict[str, Any]]:
        """
        Post-filter results safely with semantic/core-context fallback.
        Prevents dropping valid employees (e.g., Java backend devs when query = 'Spring Boot').
        """
        filtered = []
        query_skills = parsed_query.get("skills") or []
        semantic_skills = parsed_query.get("expansions", {}).get("semantic_skills", []) or []
        derived_core = parsed_query.get("derived_core", []) or []
        context = (parsed_query.get("context") or "").lower()
        location = parsed_query.get("location", "").lower() if parsed_query.get("location") else ""

        for item in merged_results:
            emp = item.get("employee_data", {})
            if not emp:
                continue

            emp_name = emp.get("display_name", "Unknown")
            emp_id = emp.get("employee_id", "N/A")
            emp_skills = (emp.get("skill_set") or "").lower()
            emp_context = (emp.get("tech_group") or "").lower()

            # Skip non-technical designations (extra safety)
            designation = (emp.get("designation") or "").lower()
            if any(x in designation for x in ["manager", "director", "vp", "hr", "admin"]):
                logger.debug(f"🚫 DROP {emp_name} ({emp_id}) — non-tech designation: {designation}")
                continue

            # === Skill relevance ===
            if query_skills:
                # direct match check
                if not self._is_skill_relevant(emp, query_skills):
                    # semantic or core-context fallback
                    sem_match = any(s in emp_skills for s in semantic_skills)
                    core_ctx_match = (
                        any(dc in emp_skills for dc in derived_core)
                        and (not context or context in emp_context)
                    )

                    if not (sem_match or core_ctx_match):
                        logger.debug(
                            f"🚫 DROP {emp_name} ({emp_id}) — no semantic/core-context match; "
                            f"skills={emp_skills[:80]} context={emp_context}"
                        )
                        continue
                    else:
                        logger.debug(
                            f"✅ KEEP {emp_name} ({emp_id}) via semantic/core fallback "
                            f"(skills={emp_skills[:60]} context={emp_context})"
                        )

            # === Location relevance ===
            if location and location not in (emp.get("emp_location") or "").lower():
                logger.debug(f"🚫 DROP {emp_name} ({emp_id}) — location mismatch")
                continue

            filtered.append(item)

        logger.info(f"🧹 Filtered down to {len(filtered)} employees after post-filtering")
        return filtered


    async def _get_or_compress_employees(
    self,
    employee_data_list: List[Dict[str, Any]],
    parsed_query: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
        """
        Prepare minimal, ranking-ready employee records.
        - Fetch compression from cache or generate it.
        - Merge query-relevant skills into compact form.
        Returns a list of objects like:
            {
                "employee_id": "VVDN/16117",
                "compression": "16117|ES|CAMA|KOC|2.8|2|MIX|java,spring boot",
                "skills_norm": ["java", "spring boot", "redis", ...]
            }
        """
        try:
            from ..services.compression_service import compression_service

            emp_ids = []
            emp_lookup = {}
            for emp in employee_data_list:
                emp_id_full = emp.get("employee_id")
                if not emp_id_full:
                    continue
                emp_id = emp_id_full.replace("VVDN/", "") if emp_id_full.startswith("VVDN/") else emp_id_full
                emp_ids.append(emp_id)
                emp_lookup[emp_id] = emp_id_full

            if not emp_ids:
                logger.warning("⚠️ No employee IDs found for compression fetch.")
                return []

            cached_batch = await compression_service.get_compressed_batch(emp_ids)
            compressed_ids = {c["id"] for c in cached_batch}

            query_skills = set()
            if parsed_query:
                raw_skills = parsed_query.get("semantic_skills") or parsed_query.get("skills") or []
                query_skills = {s.lower().strip() for s in raw_skills if s}

            missing = [eid for eid in emp_ids if eid not in compressed_ids]
            if missing:
                logger.info(f"🧩 {len(missing)} employees missing compression — generating on the fly...")
                for emp in employee_data_list:
                    emp_id = emp.get("employee_id", "").replace("VVDN/", "")
                    if emp_id in missing:
                        try:
                            payload = await compression_service.generate_compression(emp)
                            await cache_manager.set(f"compression:{payload['id']}", payload)
                            await cache_manager.sadd("comp:ids", payload["id"])
                            cached_batch.append(payload)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed realtime compression for {emp_id}: {e}")

            compressed_map = {c["id"]: c for c in cached_batch}

            enriched = []
            for emp_id in emp_ids:
                c = compressed_map.get(emp_id)
                if not c:
                    continue

                skills_norm = c.get("skills_norm", [])
                intersect_skills = [s for s in skills_norm if any(qs in s.lower() for qs in query_skills)] if query_skills else skills_norm
                SK_part = ",".join(intersect_skills) if intersect_skills else ""

                compact = (
                    f"{c['id']}|{c['role_code']}|{c['tech_group']}|"
                    f"{c['loc_code']}|{c['exp']}|{c['proj_count']}|"
                    f"{c['dept_code']}|{c['dep_summary']}|{c.get('dep_detail','')}|{SK_part}"
                )

                enriched.append({
                    "employee_id": emp_lookup[emp_id],
                    "compression": compact,
                    "skills_norm": skills_norm
                })

            logger.info(f"✅ Prepared {len(enriched)} ranking-ready employee records.")
            return enriched

        except Exception as e:
            logger.error(f"❌ Error in _get_or_compress_employees: {e}")
            return []


    async def rule_based_prerank(self, parsed_query: Dict[str, Any], employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deterministic pre-ranking based on simple rule weights.
        Used before LLM ranking for efficiency and rough ordering.
        """
        if not employees:
            return []

        def _deployment_priority(dep: str) -> int:
            dep = dep.upper() if dep else "UK"
            if dep in ("FP", "FREE"): return 1
            if dep in ("BB", "CB", "SPB"): return 2
            if dep in ("SH", "RD", "SP"): return 3
            if dep in ("BU", "PL", "IB"): return 4
            if dep in ("BIL", "CF"): return 5
            if dep in ("BS", "MK"): return 6
            return 7

        query_skills = set((parsed_query.get("semantic_skills") or parsed_query.get("skills") or []))
        query_loc = (parsed_query.get("location") or "").lower()
        query_ctx = (parsed_query.get("context") or "").lower()

        scored = []
        for e in employees:
            try:
                parts = e["compression"].split("|")
                emp_id, role, dept, loc, exp, proj_count, dep_summary, *_ = (parts + [""] * 8)[:8]

                dep_score = _deployment_priority(dep_summary)
                loc_penalty = 0 if query_loc in loc.lower() else 1
                skill_match = sum(
                    1 for s in e["skills_norm"]
                    if any(qs in s or s in qs for qs in query_skills)
                )

                exp_val = float(exp) if exp.replace('.', '', 1).isdigit() else 0.0

                # Weighted scoring (tuned empirically)
                score = (skill_match * 3.0) - (dep_score * 2.0) - loc_penalty + (exp_val * 0.2)

                # Human-style reasoning string
                reason_parts = []
                if skill_match > 0:
                    reason_parts.append(f"Matched {skill_match} skills")
                if dep_score <= 2:
                    reason_parts.append("high availability")
                elif dep_score == 3:
                    reason_parts.append("moderate availability")
                elif dep_score >= 5:
                    reason_parts.append("currently billable")
                if loc_penalty == 0:
                    reason_parts.append("same location")
                reason = ", ".join(reason_parts) or "basic profile match"

                tier = (
                    "Tier1" if score >= 4
                    else "Tier2" if score >= 2
                    else "Tier3" if score >= 0
                    else "Tier4"
                )

                scored.append({
                    **e,
                    "score": round(score, 2),
                    "tier": tier,
                    "pre_reason": reason
                })

            except Exception as ex:
                logger.warning(f"⚠️ Pre-rank error for {e.get('employee_id')}: {ex}")
                continue

        ranked = sorted(scored, key=lambda x: x["score"], reverse=True)
        logger.info(f"✅ Rule-based pre-ranking done for {len(ranked)} employees.")
        return ranked

    async def process_search_and_rank_with_criteria_simplified(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Full search + LLM-based ranking with multi-criteria reasoning using simplified parsing.
        Uses general tech categories (backend, frontend) instead of specific ones (backend-java, frontend-angular).
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🔍 Starting simplified search-with-rank for query: '{query}'")

            parsed_query = await self._cached_parse_query_simplified(query)
            if not parsed_query:
                logger.warning("Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            sql_results = await self.hybrid_engine._sql_search_loose_simplified(parsed_query)

            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = sql_results if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            has_only_name = (
                parsed_query.get("employee_name")
                and all(
                    not parsed_query.get(k)
                    for k in [
                        "skills", "context", "department", "deployment",
                        "project", "project_search", "location"
                    ]
                )
            )

            if has_only_name:
                logger.info("🧭 Employee name-only search detected — skipping compression & ranking.")
                enriched_results = []

                for emp in employee_data_list:
                    emp_copy = emp.copy()
                    emp_id = emp_copy.get("employee_id")

                    emp_copy["projects"] = self.ranking_service._get_employee_projects(emp_id)

                    for f in ['pm', 'deployments', 'selection_reason']:
                        emp_copy.pop(f, None)

                    enriched_results.append(emp_copy)

                duration = round(time.time() - start_time, 2)
                logger.info(f"✅ Employee-only lookup complete in {duration:.2f}s")

                return {
                    "action": "search_employee_details_simplified",
                    "response": f"Found {len(enriched_results)} matching employee(s)",
                    "data": enriched_results,
                    "total_results": len(enriched_results),
                    "parsed_query": parsed_query,
                    "processing_time": duration,
                    "employee_search": True
                }

            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)

            logger.info(f"🧠 Starting PDP-based multi-criteria ranking for {len(enriched)} employees...")
            final_ranked = await self.ranking_service.llm_progressive_rank_single_with_criteria_simplified_fix(
                query, parsed_query, enriched, top_k
            )

            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []

            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()

                    for f in ['pm', 'deployments', 'selection_reason']:
                        full_emp_data.pop(f, None)

                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)

                    full_emp_data.update({
                        "ai_score": ranked_emp.get("ai_score"),
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_tier": ranked_emp.get("ai_tier"),
                        "ai_criteria": ranked_emp.get("ai_criteria", {})
                    })
                    ranked_with_details.append(full_emp_data)

            ranked_with_details.sort(key=lambda x: x.get('ai_score', 0), reverse=True)

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full simplified search + ranking pipeline complete in {duration:.2f}s")

            return {
                "action": f"Employee search_with_rank_{mode}_simplified",
                "response": f"Ranked {len(ranked_with_details)} employees using simplified parsing",
                "data": ranked_with_details,
                "total_results": len(ranked_with_details),
                "parsed_query": parsed_query,
                "processing_time": duration,
                "employee_search": False
            }

        except Exception as e:
            logger.error(f"❌ process_search_and_rank_simplified error: {e}", exc_info=True)
            return {
                "action": "search_with_rank_error_simplified",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }

    async def _cached_parse_query_simplified(self, query: str) -> Dict[str, Any]:
        """
        Use existing Redis cache system for simplified LLM query parsing.
        """
        if not query:
            return {}
        
        if hasattr(self.hybrid_engine, 'embedding_cache') and self.hybrid_engine.embedding_cache and self.hybrid_engine.embedding_cache.available:
            try:
                # Check Redis cache for parsed query
                import hashlib
                cache_key = f"parsed_query_simplified:{hashlib.md5(query.lower().encode()).hexdigest()}"
                
                cached_result = self.hybrid_engine.embedding_cache.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"🎯 Redis simplified parse cache HIT: {query[:30]}...")
                    return json.loads(cached_result)
                
                logger.info(f"🔄 Redis simplified parse cache MISS - calling LLM: {query[:30]}...")
                parsed = await self.hybrid_engine._parse_query_with_llm_simplified_fix(query)
                
                # Cache in Redis with 5 minute TTL
                self.hybrid_engine.embedding_cache.redis_client.setex(
                    cache_key, 300, json.dumps(parsed)
                )
                
                return parsed
                
            except Exception as e:
                logger.warning(f"Redis cache failed, falling back to direct simplified LLM: {e}")
        
        # Fallback to direct LLM call if Redis unavailable
        return await self.hybrid_engine._parse_query_with_llm_simplified(query)

    
    async def process_search_and_rank_with_criteria_simplified_new(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Full search + ranking pipeline with:
        - SQL / vector / hybrid search
        - Python pre-ranking of heavy external (billable/budgeted) employees
        - LLM-based PDP ranking ONLY for remaining employees (internal / more available)
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🔍 Starting simplified search-with-rank for query: '{query}'")

            parsed_query = await self._cached_parse_query_simplified_semantic(query)
            if not parsed_query:
                logger.warning("Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            # -------------------------------------------------------
            # 1) Search phase (same as before)
            # -------------------------------------------------------
            # sql_results = await self.hybrid_engine._sql_search_loose_simplified_semantic(parsed_query)

            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = (await self.hybrid_engine._sql_search_loose_simplified_semantic(parsed_query)) if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            # -------------------------------------------------------
            # 2) Name-only (direct lookup) fast path
            # -------------------------------------------------------
            has_only_name = (
                parsed_query.get("employee_name")
                and all(
                    not parsed_query.get(k)
                    for k in [
                        "skills", "context", "department", "deployment",
                        "project", "project_search", "location"
                    ]
                )
            )

            if has_only_name:
                logger.info("🧭 Employee name-only search detected — skipping compression & ranking.")
                enriched_results = []

                for emp in employee_data_list:
                    emp_copy = emp.copy()
                    emp_id = emp_copy.get("employee_id")

                    emp_copy["projects"] = self.ranking_service._get_employee_projects(emp_id)

                    for f in ['pm', 'deployments', 'selection_reason']:
                        emp_copy.pop(f, None)

                    enriched_results.append(emp_copy)

                duration = round(time.time() - start_time, 2)
                logger.info(f"✅ Employee-only lookup complete in {duration:.2f}s")

                return {
                    "action": "search_employee_details_simplified",
                    "response": f"Found {len(enriched_results)} matching employee(s)",
                    "data": enriched_results,
                    "total_results": len(enriched_results),
                    "parsed_query": parsed_query,
                    "processing_time": duration,
                    "employee_search": True
                }

            # -------------------------------------------------------
            # 3) Compression / enrichment
            # -------------------------------------------------------
            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)
            logger.info(f"🧠 Prepared {len(enriched)} compressed employees for ranking.")

            employee_data_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}

            # -------------------------------------------------------
            # 4) Python pre-ranking for heavy external employees
            # -------------------------------------------------------
            pre_ranked, llm_candidates = self.ranking_service.pre_rank_employees_simplified_enhanced(
                query=query,
                parsed_query=parsed_query,
                employees=enriched,
                employee_data_lookup=employee_data_lookup,
            )

            logger.info(
                f"🧮 Pre-ranking result: {len(pre_ranked)} employees pre-ranked without LLM, "
                f"{len(llm_candidates)} employees will go through LLM PDP ranking."
            )

            # -------------------------------------------------------
            # 5) LLM-based PDP ranking for remaining employees
            # -------------------------------------------------------
            llm_ranked = []
            if llm_candidates:
                logger.info(f"🧠 Starting LLM PDP ranking for {len(llm_candidates)} candidates...")
                llm_ranked = await self.ranking_service.llm_rank_candidates_simplified(
                    query, parsed_query, llm_candidates, top_k
                )
                logger.info(f"🧠 LLM PDP ranking finished for {len(llm_ranked)} employees.")
            else:
                logger.info("🧠 No employees require LLM PDP ranking in this query.")

            # Combine pre-ranked + LLM-ranked
            final_ranked = pre_ranked + llm_ranked

            # -------------------------------------------------------
            # 6) Attach full employee details + projects
            # -------------------------------------------------------
            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []

            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()

                    for f in ['pm', 'deployments', 'selection_reason']:
                        full_emp_data.pop(f, None)

                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)

                    full_emp_data.update({
                        "ai_score": ranked_emp.get("ai_score"),
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_tier": ranked_emp.get("ai_tier"),
                        "ai_criteria": ranked_emp.get("ai_criteria", {})
                    })
                    ranked_with_details.append(full_emp_data)

            # Final sort: you can sort by tier then score, or just score.
            # Here: primary = tier (asc), secondary = score (desc)
            ranked_with_details.sort(
                key=lambda x: (x.get('ai_tier', 4), -x.get('ai_score', 0))
            )

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full simplified search + pre-rank + LLM pipeline complete in {duration:.2f}s")

            return {
                "action": f"Employee search_with_rank_{mode}_simplified",
                "response": f"Ranked {len(ranked_with_details)} employees using simplified parsing",
                "data": ranked_with_details,
                "total_results": len(ranked_with_details),
                "parsed_query": parsed_query,
                "processing_time": duration,
                "employee_search": False
            }

        except Exception as e:
            logger.error(f"❌ process_search_and_rank_simplified error: {e}", exc_info=True)
            return {
                "action": "search_with_rank_error_simplified",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }


    async def process_search_and_rank_with_criteria_simplified_new_llm(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Full search + ranking pipeline with:
        - SQL / vector / hybrid search
        - Python pre-ranking of heavy external (billable/budgeted) employees
        - LLM-based PDP ranking ONLY for remaining employees (internal / more available)
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🔍 Starting simplified search-with-rank for query: '{query}'")

            parsed_query = await self._cached_parse_query_simplified(query)
            if not parsed_query:
                logger.warning("Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }
            logger.info(parsed_query)
            if parsed_query.get("ranking") == False:
                has_only_name = (
                    parsed_query.get("employee_name")
                    and all(
                        not parsed_query.get(k)
                        for k in [
                            "skills", "context", "department", "deployment",
                            "project", "project_search", "location"
                        ]
                    )
                )
                if not has_only_name:
                    sql_query = await self.hybrid_engine._listing_query_generation(parsed_query, query)
                    return await self.hybrid_engine._fetch_data_from_db(sql_query)

            # -------------------------------------------------------
            # 1) Search phase (same as before)
            # -------------------------------------------------------
            # sql_results = await self.hybrid_engine._sql_search_loose_simplified(parsed_query)

            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
                parsed_query.get('experience_min'),
                parsed_query.get('experience_max')
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = (await self.hybrid_engine._sql_search_loose_simplified(parsed_query)) if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            # -------------------------------------------------------
            # 2) Name-only (direct lookup) fast path
            # -------------------------------------------------------
            has_only_name = (
                parsed_query.get("employee_name")
                and all(
                    not parsed_query.get(k)
                    for k in [
                        "skills", "context", "department", "deployment",
                        "project", "project_search", "location"
                    ]
                )
            )

            if has_only_name:
                logger.info("🧭 Employee name-only search detected — skipping compression & ranking.")
                enriched_results = []

                for emp in employee_data_list:
                    emp_copy = emp.copy()
                    emp_id = emp_copy.get("employee_id")

                    emp_copy["projects"] = self.ranking_service._get_employee_projects(emp_id)

                    for f in ['pm', 'deployments', 'selection_reason']:
                        emp_copy.pop(f, None)

                    enriched_results.append(emp_copy)

                duration = round(time.time() - start_time, 2)
                logger.info(f"✅ Employee-only lookup complete in {duration:.2f}s")

                return {
                    "action": "search_employee_details_simplified",
                    "response": f"Found {len(enriched_results)} matching employee(s)",
                    "data": enriched_results,
                    "total_results": len(enriched_results),
                    "parsed_query": parsed_query,
                    "processing_time": duration,
                    "employee_search": True,
                    "ranking": False
                }
            cache_key = self._make_cache_key(parsed_query)
            logger.info("Checking ranked details in cache...")
            cached_result = await self._get_ranked_cached_result(cache_key)
            if cached_result:
                logger.info("Cache hit for parsed_query")
                return cached_result
            logger.info("No Cache found for this query...")
            # -------------------------------------------------------
            # 3) Compression / enrichment
            # -------------------------------------------------------
            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)
            logger.info(f"🧠 Prepared {len(enriched)} compressed employees for ranking.")

            employee_data_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}

            # -------------------------------------------------------
            # 4) Python pre-ranking for heavy external employees
            # -------------------------------------------------------
            pre_ranked, llm_candidates = self.ranking_service.pre_rank_employees_simplified(
                query=query,
                parsed_query=parsed_query,
                employees=enriched,
                employee_data_lookup=employee_data_lookup,
            )

            logger.info(
                f"🧮 Pre-ranking result: {len(pre_ranked)} employees pre-ranked without LLM, "
                f"{len(llm_candidates)} employees will go through LLM PDP ranking."
            )

            # -------------------------------------------------------
            # 4) PARALLEL LLM processing for both groups
            # -------------------------------------------------------
            pre_ranked_processed = []
            llm_ranked = []

            try:
                # Create tasks for parallel execution
                tasks = []
                
                if pre_ranked:
                    logger.info("🧠 Sending Python pre-ranked employees to LLM for reasoning + score refinement...")
                    tasks.append(self.ranking_service.llm_generate_reason_and_scores(pre_ranked))
                else:
                    # If no pre_ranked, create an empty task
                    async def empty_pre_ranked():
                        return []
                    tasks.append(empty_pre_ranked())
                
                if llm_candidates:
                    logger.info(f"🧠 Starting LLM PDP ranking for {len(llm_candidates)} candidates...")
                    tasks.append(self.ranking_service.llm_rank_candidates_simplified(
                        query, parsed_query, llm_candidates, top_k
                    ))
                else:
                    # If no llm_candidates, create an empty task
                    async def empty_llm_ranked():
                        return []
                    tasks.append(empty_llm_ranked())
                
                # Run both LLM calls in parallel
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results with error handling
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Error in LLM task {i}: {result}")
                        if i == 0 and pre_ranked:
                            # Error in pre_ranked processing, use original pre_ranked without LLM refinement
                            pre_ranked_processed = pre_ranked
                            logger.warning("⚠️ Using pre-ranked employees without LLM refinement due to error")
                        elif i == 1 and llm_candidates:
                            # Error in llm ranking, use empty list
                            llm_ranked = []
                            logger.warning("⚠️ LLM ranking failed, no LLM-ranked employees will be included")
                    else:
                        if i == 0:  # First task was pre_ranked processing
                            pre_ranked_processed = result
                            logger.info(f"✅ LLM refinement completed for {len(pre_ranked_processed)} pre-ranked employees")
                        else:  # Second task was llm ranking
                            llm_ranked = result
                            logger.info(f"✅ LLM PDP ranking completed for {len(llm_ranked)} employees")
                
            except Exception as e:
                logger.error(f"❌ Parallel LLM processing error: {e}")
                # Fallback to sequential processing or original data
                if pre_ranked:
                    pre_ranked_processed = pre_ranked  # Use without LLM refinement
                llm_ranked = []  # Skip LLM ranked

            # Combine pre-ranked + LLM-ranked
            final_ranked = pre_ranked_processed + llm_ranked

            # -------------------------------------------------------
            # 6) Attach full employee details + projects
            # -------------------------------------------------------
            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []

            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()

                    for f in ['pm', 'deployments', 'selection_reason']:
                        full_emp_data.pop(f, None)

                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)

                    full_emp_data.update({
                        "ranked_by": ranked_emp.get("ranked_by"),
                        "ai_score": ranked_emp.get("ai_score"),
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_tier": ranked_emp.get("ai_tier"),
                        "ai_criteria": ranked_emp.get("ai_criteria", {})
                    })
                    ranked_with_details.append(full_emp_data)

            # Final sort: you can sort by tier then score, or just score.
            # Here: primary = tier (asc), secondary = score (desc)
            ranked_with_details.sort(
                key=lambda x: (x.get('ai_tier', 4), -x.get('ai_score', 0))
            )

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full simplified search + pre-rank + LLM pipeline complete in {duration:.2f}s")

            final_response = {
                "action": f"Employee search_with_rank_{mode}_simplified",
                "ranking": True,
                "response": f"Ranked {len(ranked_with_details)} employees using simplified parsing",
                "data": ranked_with_details,
                "total_results": len(ranked_with_details),
                "parsed_query": parsed_query,
                "processing_time": duration,
                "employee_search": False
            }
            if ranked_with_details:
                logger.info("🚀 Sending ranked cache task to Celery")
                save_ranked_search_cache.delay(cache_key, final_response, 300)
                logger.info("Saving to cache...")

            return final_response

        except Exception as e:
            logger.error(f"❌ process_search_and_rank_simplified error: {e}", exc_info=True)
            return {
                "action": "search_with_rank_error_simplified",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }


    async def process_search_and_rank_with_criteria_simplified_new_llm_semantic(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Full search + ranking pipeline with:
        - SQL / vector / hybrid search
        - Python pre-ranking of heavy external (billable/budgeted) employees
        - LLM-based PDP ranking ONLY for remaining employees (internal / more available)
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🔍 Starting simplified search-with-rank for query: '{query}'")

            parsed_query = await self._cached_parse_query_simplified_semantic(query)
            if not parsed_query:
                logger.warning("Empty parsed query - returning empty result set")
                return {
                    "action": "search_only_results",
                    "response": "No results (unrecognized query)",
                    "data": [],
                    "total_results": 0,
                    "parsed_query": {},
                    "processing_time": 0
                }

            # -------------------------------------------------------
            # 1) Search phase (same as before)
            # -------------------------------------------------------
            sql_results = await self.hybrid_engine._sql_search_loose_simplified_semantic(parsed_query)

            has_structured_filters = any([
                parsed_query.get('strict_filter'),
                parsed_query.get('deployment'),
                parsed_query.get('project_search'),
                parsed_query.get('skills'),
                parsed_query.get('context'),
                parsed_query.get('location'),
                parsed_query.get('department'),
                parsed_query.get('employee_name'),
            ])

            is_generic = not has_structured_filters and len(query.split()) <= 5
            mode = "sql" if has_structured_filters else "vector" if is_generic else "hybrid"

            merged_results = sql_results if mode == "sql" else (
                await self.hybrid_engine._vector_search(query, (top_k * 2) if top_k else None)
            )

            employee_data_list = [
                r["employee_data"] for r in merged_results if "employee_data" in r
            ]

            # -------------------------------------------------------
            # 2) Name-only (direct lookup) fast path
            # -------------------------------------------------------
            has_only_name = (
                parsed_query.get("employee_name")
                and all(
                    not parsed_query.get(k)
                    for k in [
                        "skills", "context", "department", "deployment",
                        "project", "project_search", "location"
                    ]
                )
            )

            if has_only_name:
                logger.info("🧭 Employee name-only search detected — skipping compression & ranking.")
                enriched_results = []

                for emp in employee_data_list:
                    emp_copy = emp.copy()
                    emp_id = emp_copy.get("employee_id")

                    emp_copy["projects"] = self.ranking_service._get_employee_projects(emp_id)

                    for f in ['pm', 'deployments', 'selection_reason']:
                        emp_copy.pop(f, None)

                    enriched_results.append(emp_copy)

                duration = round(time.time() - start_time, 2)
                logger.info(f"✅ Employee-only lookup complete in {duration:.2f}s")

                return {
                    "action": "search_employee_details_simplified",
                    "response": f"Found {len(enriched_results)} matching employee(s)",
                    "data": enriched_results,
                    "total_results": len(enriched_results),
                    "parsed_query": parsed_query,
                    "processing_time": duration,
                    "employee_search": True
                }

            # -------------------------------------------------------
            # 3) Compression / enrichment
            # -------------------------------------------------------
            enriched = await self._get_or_compress_employees(employee_data_list, parsed_query)
            logger.info(f"🧠 Prepared {len(enriched)} compressed employees for ranking.")

            employee_data_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}

            # -------------------------------------------------------
            # 4) Python pre-ranking for heavy external employees
            # -------------------------------------------------------
            pre_ranked, llm_candidates = self.ranking_service.pre_rank_employees_simplified_enhanced(
                query=query,
                parsed_query=parsed_query,
                employees=enriched,
                employee_data_lookup=employee_data_lookup,
            )

            logger.info(
                f"🧮 Pre-ranking result: {len(pre_ranked)} employees pre-ranked without LLM, "
                f"{len(llm_candidates)} employees will go through LLM PDP ranking."
            )
            
            if pre_ranked:
                logger.info("🧠 Sending Python pre-ranked employees to LLM for reasoning + score refinement...")
                pre_ranked = await self.ranking_service.llm_generate_reason_and_scores(pre_ranked)

            # -------------------------------------------------------
            # 5) LLM-based PDP ranking for remaining employees
            # -------------------------------------------------------
            llm_ranked = []
            if llm_candidates:
                logger.info(f"🧠 Starting LLM PDP ranking for {len(llm_candidates)} candidates...")
                llm_ranked = await self.ranking_service.llm_rank_candidates_simplified(
                    query, parsed_query, llm_candidates, top_k
                )
                logger.info(f"🧠 LLM PDP ranking finished for {len(llm_ranked)} employees.")
            else:
                logger.info("🧠 No employees require LLM PDP ranking in this query.")

            # Combine pre-ranked + LLM-ranked
            final_ranked = pre_ranked + llm_ranked

            # -------------------------------------------------------
            # 6) Attach full employee details + projects
            # -------------------------------------------------------
            employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
            ranked_with_details = []

            for ranked_emp in final_ranked:
                emp_id = ranked_emp.get("employee_id")
                if emp_id in employee_lookup:
                    full_emp_data = employee_lookup[emp_id].copy()

                    for f in ['pm', 'deployments', 'selection_reason']:
                        full_emp_data.pop(f, None)

                    full_emp_data['projects'] = self.ranking_service._get_employee_projects(emp_id)

                    full_emp_data.update({
                        "ai_score": ranked_emp.get("ai_score"),
                        "ai_reason": ranked_emp.get("ai_reason"),
                        "ai_tier": ranked_emp.get("ai_tier"),
                        "ai_criteria": ranked_emp.get("ai_criteria", {})
                    })
                    ranked_with_details.append(full_emp_data)

            # Final sort: you can sort by tier then score, or just score.
            # Here: primary = tier (asc), secondary = score (desc)
            ranked_with_details.sort(
                key=lambda x: (x.get('ai_tier', 4), -x.get('ai_score', 0))
            )

            duration = round(time.time() - start_time, 2)
            logger.info(f"✅ Full simplified search + pre-rank + LLM pipeline complete in {duration:.2f}s")

            return {
                "action": f"Employee search_with_rank_{mode}_simplified",
                "response": f"Ranked {len(ranked_with_details)} employees using simplified parsing",
                "data": ranked_with_details,
                "total_results": len(ranked_with_details),
                "parsed_query": parsed_query,
                "processing_time": duration,
                "employee_search": False
            }

        except Exception as e:
            logger.error(f"❌ process_search_and_rank_simplified error: {e}", exc_info=True)
            return {
                "action": "search_with_rank_error_simplified",
                "error": str(e),
                "data": [],
                "total_results": 0,
                "processing_time": 0
            }

    async def _cached_parse_query_simplified_semantic(self, query: str) -> Dict[str, Any]:
        """
        Use existing Redis cache system for simplified LLM query parsing.
        """
        if not query:
            return {}
        
        if hasattr(self.hybrid_engine, 'embedding_cache') and self.hybrid_engine.embedding_cache and self.hybrid_engine.embedding_cache.available:
            try:
                # Check Redis cache for parsed query
                import hashlib
                cache_key = f"parsed_query_simplified:{hashlib.md5(query.lower().encode()).hexdigest()}"
                
                cached_result = self.hybrid_engine.embedding_cache.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"🎯 Redis simplified parse cache HIT: {query[:30]}...")
                    return json.loads(cached_result)
                
                logger.info(f"🔄 Redis simplified parse cache MISS - calling LLM: {query[:30]}...")
                parsed = await self.hybrid_engine._parse_query_with_llm_simplified_fix_semantic(query)
                
                # Cache in Redis with 5 minute TTL
                self.hybrid_engine.embedding_cache.redis_client.setex(
                    cache_key, 300, json.dumps(parsed)
                )
                
                return parsed
                
            except Exception as e:
                logger.warning(f"Redis cache failed, falling back to direct simplified LLM: {e}")
        
        # Fallback to direct LLM call if Redis unavailable
        return await self.hybrid_engine._parse_query_with_llm_simplified(query)
    
    def _make_cache_key(self, parsed_query: dict):
        import hashlib
        normalize = json.dumps(parsed_query, sort_keys=True)
        return "ranked_search:" + hashlib.md5(normalize.encode()).hexdigest()
    
    async def _get_ranked_cached_result(self, redis_key: str):
        try:
            data = self.hybrid_engine.embedding_cache.redis_client.get(redis_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis cache failed: {e}")

    