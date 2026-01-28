"""
RAG + Hybrid Search Engine - Core implementation for AI HRMS
Combines semantic search, SQL filtering, and business-aware ranking
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from ..core.database import get_db_session


# Import logging service to ensure file logging is configured
try:
    from .logging_service import logging_service
except ImportError:
    pass

from .embedding_cache_service import EmbeddingCacheService

logger = logging.getLogger(__name__)

# Optional imports for hybrid search
try:
    logger.info("📦 Importing hybrid search dependencies...")
    from sentence_transformers import SentenceTransformer
    logger.info("✅ sentence_transformers imported")
    import chromadb
    logger.info("✅ chromadb imported")
    import numpy as np
    logger.info("✅ numpy imported")
    from sklearn.metrics.pairwise import cosine_similarity
    logger.info("✅ sklearn imported")
    import google.generativeai as genai
    logger.info("✅ google.generativeai imported")
    HYBRID_SEARCH_AVAILABLE = True
    logger.info("🎉 All hybrid search dependencies available!")
except ImportError as e:
    logger.warning(f"❌ Hybrid search dependencies not available: {e}")
    HYBRID_SEARCH_AVAILABLE = False
    SentenceTransformer = None
    chromadb = None
    genai = None

class HybridSearchEngine:
    """
    RAG + Hybrid Search Engine for Employee Matching
    
    Architecture:
    1. Semantic Understanding (LLM) - Parse user query into structured filters
    2. Multi-Modal Retrieval - Vector search + SQL filters + keyword matching  
    3. Business-Aware Ranking - HR-specific scoring and reranking
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        logger.info(f"🚀 Initializing HybridSearchEngine with API key: {'✅ Set' if gemini_api_key else '❌ Missing'}")
        logger.info(f"📦 HYBRID_SEARCH_AVAILABLE: {HYBRID_SEARCH_AVAILABLE}")
        
        if not HYBRID_SEARCH_AVAILABLE:
            logger.error("❌ Hybrid search dependencies not available. Install: pip install sentence-transformers chromadb google-generativeai")
            self.available = False
            return
        
        self.available = True
        logger.info("✅ Dependencies available, proceeding with initialization...")
        
        try:
            # Initialize embedding model for semantic search
            logger.info("📥 Loading SentenceTransformer model...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SentenceTransformer loaded successfully")
            
            # Initialize ChromaDB for vector storage
            logger.info("🗄️ Initializing ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            try:
                self.collection = self.chroma_client.get_collection("employees")
                logger.info("✅ ChromaDB collection 'employees' found")
            except:
                self.collection = self.chroma_client.create_collection("employees")
                logger.info("✅ ChromaDB collection 'employees' created")
            
            # Initialize Gemini 2.5 Flash-Lite for ultra-fast query understanding
            if gemini_api_key:
                logger.info("🤖 Configuring Gemini API...")
                genai.configure(api_key=gemini_api_key)
                self.llm = genai.GenerativeModel('gemini-2.5-flash-lite')
                logger.info("✅ Gemini 2.5 Flash-Lite enabled - ULTRA FAST query parsing (~200ms)")
            else:
                self.llm = None
                logger.warning("⚠️ No Gemini API key provided, query parsing disabled")
                
            # Initialize semantic enhancement service

            logger.info("✅ Semantic enhancement service initialized")
            
            logger.info("✅ Core services initialized")
            
            # Initialize embedding cache service for 10x faster search
            self.embedding_cache = EmbeddingCacheService()
            if self.embedding_cache.available:
                logger.info("🚀 Embedding cache service initialized - ULTRA FAST mode enabled")
            else:
                logger.warning("⚠️ Embedding cache service not available - using standard mode")
            
            # Initialize skill embeddings cache (lazy-loaded)
            self.skill_embeddings = {}
            self.skill_embeddings_initialized = False
            
            # HR Business Rules for ranking - Correct deployment priority
            self.availability_scores = {
                # Highest priority - immediately available
                'free': 1.0,
                
                # High priority - support roles
                'shadow': 0.95,
                'support': 0.90,
                'mfg support backup': 0.85,
                'mfg randd shadow': 0.85,
                'r and d shadow': 0.85,
                
                # Medium-high priority - research and development
                'randd internal budgeted': 0.80,
                'mfg randd internal budgeted': 0.80,
                'internal budgeted': 0.75,
                
                # Medium priority - planned and trainee
                'planned': 0.70,
                'trainee': 0.65,
                
                # Lower priority - backup roles
                'billable backup': 0.60,
                'client backup': 0.55,
                
                # Low priority - budgeted projects
                'budgeted': 0.45,
                'bu common': 0.40,
                
                # Lowest priority - actively billable
                'billable': 0.25,
                'customer facing': 0.20,
                'mfg support billable': 0.15,
                'business': 0.10,
                'marketing': 0.10
            }
            
            # Enhanced skill categories with contextual matching
            self.skill_categories = {
                'backend': {
                    'core_skills': ['java', 'python', 'spring', 'django', 'nodejs', 'golang', 'c++'],
                    'context_indicators': ['spring boot', 'microservices', 'rest api', 'hibernate', 'jpa', 'maven', 'gradle', 'backend']
                },
                'frontend': {
                    'core_skills': ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css'],
                    'context_indicators': ['reactjs', 'frontend', 'ui', 'dom', 'webpack', 'npm']
                },
                'mobile': {
                    'core_skills': ['android', 'ios', 'flutter', 'react native', 'swift', 'kotlin'],
                    'context_indicators': ['android studio', 'xcode', 'mobile app', 'jetpack', 'android']
                },
                'devops': {
                    'core_skills': ['docker', 'kubernetes', 'aws', 'azure', 'jenkins', 'terraform'],
                    'context_indicators': ['ci/cd', 'deployment', 'infrastructure', 'devops', 'pipeline']
                },
                'database': {
                    'core_skills': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
                    'context_indicators': ['database', 'sql', 'nosql', 'db']
                }
            }
            
            logger.info(f"🎉 HybridSearchEngine initialized successfully! Available: {self.available}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize hybrid search: {e}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            self.available = False
            # Initialize fallback services
            self.embedding_cache = None
        
    async def _ensure_skill_embeddings_cache(self):
        """Load skill embeddings from Redis cache or rebuild if missing"""
        if self.skill_embeddings_initialized:
            return
            
        try:
            if not self.available or not hasattr(self, 'embedder') or not self.embedding_cache or not self.embedding_cache.available:
                return
            
            # Try to load from Redis first
            cached_skills = await self._load_skill_embeddings_from_redis()
            if cached_skills:
                self.skill_embeddings = cached_skills
                self.skill_embeddings_initialized = True
                logger.info(f"✅ Loaded {len(cached_skills)} skill embeddings from Redis cache")
                return
            
            # Cache miss - rebuild from database
            logger.info("🔄 Building skill embeddings cache from database...")
            await self._rebuild_skill_embeddings_cache()
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure skill embeddings cache: {e}")
            self.skill_embeddings = {}
    
    async def _load_skill_embeddings_from_redis(self) -> Dict[str, Any]:
        """Load skill embeddings from Redis"""
        try:
            cached_data = self.embedding_cache.redis_client.get("skill_embeddings_cache")
            if cached_data:
                import json
                import numpy as np
                data = json.loads(cached_data)
                # Convert lists back to numpy arrays
                skill_embeddings = {}
                for skill, embedding_list in data.get('embeddings', {}).items():
                    skill_embeddings[skill] = np.array(embedding_list)
                return skill_embeddings
        except Exception as e:
            logger.warning(f"Failed to load skill embeddings from Redis: {e}")
        return {}
    
    async def _rebuild_skill_embeddings_cache(self):
        """Rebuild skill embeddings cache from database and store in Redis"""
        try:
            # Check if we have employee data
            with get_db_session() as session:
                count_result = session.execute(text("SELECT COUNT(*) FROM employees"))
                employee_count = count_result.scalar()
                
                if employee_count == 0:
                    logger.info("⚠️ No employee data found, skipping skill embeddings cache")
                    return
                
                # Extract all unique skills from database
                result = session.execute(text("""
                    SELECT DISTINCT skill_set, tech_group 
                    FROM employees 
                    WHERE skill_set IS NOT NULL AND tech_group IS NOT NULL
                """))
                
                all_skills = set()
                for row in result:
                    skills = row.skill_set or ''
                    tech_group = row.tech_group or ''
                    
                    # Extract skill tokens
                    skill_tokens = skills.lower().replace(',', ' ').replace(';', ' ').split()
                    tech_tokens = tech_group.lower().replace('-', ' ').split()
                    
                    for token in skill_tokens + tech_tokens:
                        clean_token = token.strip().lower()
                        if len(clean_token) > 2 and clean_token.replace(' ', '').isalpha():
                            all_skills.add(clean_token)
            
            if not all_skills:
                logger.info("⚠️ No skills found in employee data")
                return
            
            # Pre-compute embeddings for all skills
            logger.info(f"📊 Computing embeddings for {len(all_skills)} unique skills...")
            
            skill_embeddings = {}
            for skill in all_skills:
                try:
                    skill_embeddings[skill] = self.embedder.encode(skill)
                except Exception as e:
                    logger.warning(f"Failed to encode skill '{skill}': {e}")
            
            # Store in Redis
            await self._save_skill_embeddings_to_redis(skill_embeddings)
            
            # Update in-memory cache
            self.skill_embeddings = skill_embeddings
            self.skill_embeddings_initialized = True
            logger.info(f"✅ Skill embeddings cache built and cached: {len(skill_embeddings)} skills")
            
        except Exception as e:
            logger.error(f"❌ Failed to rebuild skill embeddings cache: {e}")
            self.skill_embeddings = {}
    
    async def _save_skill_embeddings_to_redis(self, skill_embeddings: Dict[str, Any]):
        """Save skill embeddings to Redis"""
        try:
            import json
            from datetime import datetime
            
            # Convert numpy arrays to lists for JSON serialization
            serializable_embeddings = {}
            for skill, embedding in skill_embeddings.items():
                serializable_embeddings[skill] = embedding.tolist()
            
            cache_data = {
                'embeddings': serializable_embeddings,
                'generated_at': datetime.now().isoformat(),
                'total_skills': len(skill_embeddings)
            }
            
            # Store with 7 day TTL (same as employee embeddings)
            self.embedding_cache.redis_client.setex(
                "skill_embeddings_cache",
                604800,  # 7 days
                json.dumps(cache_data)
            )
            
            logger.info(f"✨ Saved {len(skill_embeddings)} skill embeddings to Redis cache")
            
        except Exception as e:
            logger.error(f"Failed to save skill embeddings to Redis: {e}")
    
    async def refresh_skill_embeddings_cache(self):
        """Refresh skill embeddings cache after data upload"""
        logger.info("🔄 Refreshing skill embeddings cache after data update...")
        
        # Clear Redis cache
        if self.embedding_cache and self.embedding_cache.available:
            try:
                self.embedding_cache.redis_client.delete("skill_embeddings_cache")
                logger.info("🗑️ Cleared skill embeddings from Redis")
            except Exception as e:
                logger.warning(f"Failed to clear skill embeddings from Redis: {e}")
        
        # Clear in-memory cache
        self.skill_embeddings = {}
        self.skill_embeddings_initialized = False
        
        # Rebuild cache
        await self._ensure_skill_embeddings_cache()
    
    async def search(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Main hybrid search function with performance monitoring
        
        Flow:
        1. Parse query using LLM to extract structured filters
        2. Execute multi-modal retrieval (vector + SQL + keyword)
        3. Apply business-aware ranking
        4. Return top results with explanations
        """
        if not self.available:
            return {
                'results': [],
                'total_found': 0,
                'search_strategy': 'unavailable',
                'parsed_query': {},
                'ranking_explanation': ['Hybrid search not available']
            }
        
        try:
            
            # Step 1: Semantic Understanding - Parse query into structured format
            parsed_query = await self._parse_query_with_llm(query)
            
            # Step 2: PARALLEL Multi-Modal Retrieval
            import asyncio
            
            # Always start SQL search
            sql_task = asyncio.create_task(self._sql_search(parsed_query))
            
            # For strict filtering queries, use only SQL results
            if parsed_query.get('strict_filter') or parsed_query.get('deployment') or parsed_query.get('project_search'):
                sql_results = await sql_task
                merged_results = sql_results
            else:
                # PARALLEL: Run vector and keyword search concurrently with SQL
                vector_task = asyncio.create_task(self._vector_search(query, (top_k * 2) if top_k else None))
                keyword_task = asyncio.create_task(self._keyword_search(query))
                
                # Wait for all searches to complete in parallel
                sql_results, vector_results, keyword_results = await asyncio.gather(
                    sql_task, vector_task, keyword_task
                )
                
                # Step 3: Merge and deduplicate results
                merged_results = self._merge_results(vector_results, sql_results, keyword_results)
            
            # Step 4: Business-Aware Ranking
            ranked_results = self._business_rerank(merged_results, query, parsed_query)
            
            # Step 5: Return top results (all if top_k not specified)
            final_results = ranked_results[:top_k] if top_k else ranked_results
                        
            return {
                'results': final_results,
                'total_found': len(merged_results),
                'search_strategy': 'hybrid_rag',
                'parsed_query': parsed_query,
                'ranking_explanation': self._explain_ranking(final_results)
            }
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Return error result instead of fallback
            return {
                'results': [],
                'total_found': 0,
                'search_strategy': 'error',
                'parsed_query': {},
                'ranking_explanation': [f'Search failed: {str(e)}']
            }
    
    async def _parse_query_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Optimized Gemini 2.0 Flash Lite parsing — fast JSON output mode
        Converts a natural language HR query into structured filters.

        Example:
        "Java developers with 3+ years in free pool"
        → {"skills": ["java"], "experience_min": 3, "deployment": "free"}
        """
        if not self.llm:
            return {}

        try:

           # ✅ Dynamically fetch valid tech groups from DB
            from hrms_ai.repositories.employee_repository import EmployeeRepository
            repo = EmployeeRepository()
            tech_groups = repo.get_all_tech_groups()

            # Convert to set for deduplication
            tech_group_set = {tg.strip() for tg in tech_groups if tg}

            # ✅ Add fallback mappings for known domains
            fallback_mappings = {
                "flutter": "Android",
                "react native": "Hybrid Apps",
                "kotlin multiplatform": "Hybrid Apps",
                "swift": "IoS",
                "ios": "IoS",
                "android": "Android",
                "aws": "CloudOps",
                "azure": "CloudOps",
                "gcp": "CloudOps",
                "kubernetes": "CloudOps",
                "terraform": "CloudOps",
                "sql": "Backend",
                "postgres": "Backend",
                "mysql": "Backend",
                "java": "Backend",
                "python": "Backend",
                "node": "Back End",
                "react": "Frontend",
                "angular": "Frontend",
                "html": "Frontend",
                "css": "Frontend",
                "full stack": "Full Stack",
                "ai": "Ops - AI/ML",
                "ml": "Ops - AI/ML",
                "machine learning": "Ops - AI/ML",
                "data": "Backend - DB",
                "embedded": "Embedded SW"
            }

            # Merge DB tech groups with known fallback contexts
            tech_group_set.update(fallback_mappings.values())

            logger.info(f"🧩 Loaded {len(tech_group_set)} unique tech groups (with fallbacks)")

            prompt = f"""
            Parse this HR-related search query into a JSON object.
            Query: "{query}"

            You are parsing for an enterprise HR database that uses the following TECH GROUPS:
            {tech_groups}

            Your task: interpret the query and map it to the most relevant tech_group context above.


            Extract and infer the following keys if mentioned or implied:
            - skills: [list of skills/technologies]
            - context: the closest matching TECH GROUP name from the list above, only if the query involves a technical skill, role, or project type.  Do not include 'context' if the query only mentions a person's name or non-technical term.


            - experience_min: integer years
            - experience_max: integer years
            - deployment: one of [free, billable, support, budgeted]
            - location: city or work location
            - department: department name
            - designation: like engineer, sr engineer etc.
            - project: project name/code if mentioned
            - project_search: true if looking for people who worked on a project
            - employee_name: name if specific person requested
            - skill_precision: "strict" if user specifies exact skill or says "exact match"

            Rules:
            1. Use your understanding of tech domains and the given TECH GROUPS to infer 'context' if not explicitly mentioned.
            - Always prefer a matching TECH GROUP name from the list if possible.
            - If no direct match exists, reason naturally like a human and infer the most appropriate one.

            Examples:
            - Skills like Java, Python, Node, .NET → context="Backend - Java" or "Backend - Dot Net"
            - Skills like React, Angular, Vue → context="Frontend - ReactJS" or "Frontend - Angular"
            - Skills like Android → context="Android"
            - Skills like iOS, Swift → context="IoS"
            - Skills like Flutter → context="Android" (cross-platform mobile developer)
            - Skills like Kotlin Multiplatform or React Native → context="Hybrid Apps"
            - Skills like AWS, Azure, GCP, Kubernetes, Terraform → context="CloudOps" or "Cloud Backend"
            - Skills like TensorFlow, PyTorch, ML, AI → context="Ops - AI/ML"
            - Skills like SQL, Postgres, MySQL → context="Backend - DB"
            - Skills like HTML, CSS, JS, full stack → context="Full Stack"
            - If it involves both frontend and backend → context="Full Stack"
            - If nothing fits any TECH GROUP, set context="general".

            2. For skills that could belong to multiple tech_groups (e.g. Flutter, React Native, or hybrid frameworks),
            select the most common or likely category (for example, "Flutter" → "Android", "React Native" → "Hybrid Apps").

            3. Never invent new tech_group names. Always use one from the TECH GROUP list if possible.
            4. Extract only real city names for 'location' (ignore frontend/backend etc.).
            5. Phrases like 'free', 'free pool', 'available' → deployment='free'
            6. If query mentions project/team/assigned/worked → project_search=true
            7. Respond ONLY with valid JSON, no extra text or comments.
            """


            # ✅ Direct JSON response mode (faster and cleaner)
            response = self.llm.generate_content(
                contents=prompt,
               generation_config = {
                    "temperature": 0,
                    "max_output_tokens": 512,
                    "response_mime_type": "application/json"
                    }
            )

            if not response or not hasattr(response, "text") or not response.text:
                logger.error("❌ LLM returned no response or invalid object")
                return {}

            # ✅ Parse JSON response with error handling
            response_text = response.text.strip()
            
            # Handle incomplete JSON responses
            if not response_text.endswith('}'):
                logger.warning(f"Incomplete JSON response: {response_text}")
                # Try to fix common incomplete patterns
                if response_text.endswith('"skills'):
                    response_text = '{"skills": []}'
                elif response_text.count('{') > response_text.count('}'):
                    response_text += '}' * (response_text.count('{') - response_text.count('}'))
            
            parsed = json.loads(response_text)

            # ✅ Validate and normalize
            validated = self._validate_parsed_query(parsed)

            # 🧹 Clean up unnecessary context for name-only queries
            if (
                validated.get("employee_name")
                and not any(validated.get(k) for k in ["skills", "department", "deployment", "project", "location"])
            ):
                if "context" in validated:
                    logger.info(f"🧹 Removing irrelevant context '{validated['context']}' for name-only query")
                    validated.pop("context", None)

            # 🔍 Detect free pool / availability
            query_lower = (query or "").lower()
            if any(term in query_lower for term in ['free pool', 'freepool', 'free', 'available', 'who are available']):
                validated['deployment'] = 'free'
                validated['strict_filter'] = True

            # 🔧 Fix location issues using your DB-aware logic
            if 'location' in validated:
                logger.info(f"🔧 Before location fix: {validated.get('location')}")
                validated = self._fix_location_parsing(validated, query_lower)
                logger.info(f"🔧 After location fix: {validated.get('location', 'REMOVED')}")

            # 🧠 Project search detection fallback
            project_indicators = ['worked', 'project', 'team', 'assigned', 'members']
            if any(indicator in query_lower for indicator in project_indicators) and 'project' not in validated:
                words = query.split()
                for word in words:
                    clean_word = word.strip('.,!?')
                    if len(clean_word) >= 3 and (clean_word.isupper() or '_' in clean_word or clean_word.isdigit()):
                        validated['project'] = clean_word.upper()
                        validated['project_search'] = True
                        break

            # 🧩 Optional semantic enhancement toggle
            if hasattr(self, 'semantic_service') and validated.get('skill_precision') != 'strict':
                logger.info(f"🧠 Semantic enhancement: {validated.get('search_intent', 'generic')} intent detected")
            elif validated.get('skill_precision') == 'strict':
                logger.info(f"🎯 Strict skill matching enabled")

            return validated

        except Exception as e:
            logger.error(f"LLM query parsing failed: {e}")
            logger.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            return {}

    
    def _validate_parsed_query(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean parsed query safely (null-tolerant version)"""
        validated = {}

        # --- Skills ---
        skills = parsed.get('skills')
        if isinstance(skills, list):
            validated['skills'] = [str(s).lower().strip() for s in skills if s]

        # --- Experience ---
        exp_min = parsed.get('experience_min')
        if exp_min is not None:
            try:
                validated['experience_min'] = float(exp_min)
            except Exception:
                validated['experience_min'] = 0.0

        exp_max = parsed.get('experience_max')
        if exp_max is not None:
            try:
                validated['experience_max'] = float(exp_max)
            except Exception:
                validated['experience_max'] = 0.0

        # --- Deployment ---
        dep_val = (parsed.get('deployment') or '').strip().lower()
        if dep_val and hasattr(self, 'availability_scores') and dep_val in self.availability_scores:
            validated['deployment'] = dep_val

        # --- Other string fields ---
        for key in ['location', 'department', 'project', 'employee_name', 'context', 'skill_precision']:
            val = parsed.get(key)
            if isinstance(val, str):
                validated[key] = val.strip().lower()
            elif val is not None:
                validated[key] = str(val).strip().lower()

        # --- Project Search Flag ---
        validated['project_search'] = bool(parsed.get('project_search', False))

        return validated

    
    def _fix_location_parsing(self, validated: Dict[str, Any], query_lower: str) -> Dict[str, Any]:
        """Fix location parsing using cached locations for performance"""
        try:
            # Use cached locations instead of database query for performance
            if not hasattr(self, '_cached_locations'):
                self._cached_locations = ['bangalore', 'kochi', 'noida', 'gurgaon', 'pune', 'chennai', 'hyderabad', 'mumbai', 'delhi', 'remote', 'onsite', 'wfh', 'hybrid']
            
            current_location = validated.get('location', '').lower()
            skill_contexts = ['frontend', 'backend', 'mobile', 'angular', 'react', 'java', 'python', 'nodejs', 'docker', 'kubernetes']
            
            # If current location is a skill context, find actual location
            if current_location in skill_contexts:
                logger.info(f"🔍 Detected skill context as location: {current_location}")
                
                for location in self._cached_locations:
                    if location in query_lower:
                        validated['location'] = location
                        logger.info(f"✅ Fixed location parsing: {current_location} -> {location}")
                        return validated
                
                # Remove invalid location if no match found
                del validated['location']
                logger.info(f"❌ Removed invalid location: {current_location} (no city found in query)")
            
            return validated
            
        except Exception as e:
            logger.error(f"Location parsing fix error: {e}")
            return validated
    
    async def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        ULTRA-FAST semantic vector search using cached embeddings
        10x faster than real-time embedding generation
        """
        try:
            # Try cached embedding approach first (10x faster)
            if self.embedding_cache and self.embedding_cache.available:
                return await self._cached_vector_search(query, top_k)
            
            # No fallback - return empty if cache unavailable
            return []
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def _cached_vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Ultra-fast vector search using pre-cached embeddings
        """
        try:
            logger.info(f"🚀 Using CACHED vector search for: {query[:50]}...")
            
            # Get all cached employee embeddings first (quick check)
            cache_data = await self.embedding_cache.get_cached_employee_embeddings()
            if not cache_data.get('embeddings'):
                logger.warning("⚠️ No cached employee embeddings found, skipping vector search")
                return []  # Return empty instead of falling back to slow ChromaDB
            
            # Get cached query embedding (or generate and cache)
            query_embedding = await self.embedding_cache.get_cached_query_embedding(query)
            if query_embedding is None:
                logger.warning("⚠️ Failed to get query embedding, skipping vector search")
                return []  # Return empty instead of falling back to slow ChromaDB
            
            embeddings = cache_data['embeddings']
            employee_data = cache_data['employee_data']
            
            # Calculate similarities efficiently
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Prepare employee embeddings matrix
            emp_ids = list(embeddings.keys())
            emp_embeddings = np.array([embeddings[emp_id] for emp_id in emp_ids])
            
            # Calculate cosine similarities
            similarities = cosine_similarity([query_embedding], emp_embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            vector_results = []
            for idx in top_indices:
                emp_id = emp_ids[idx]
                similarity = float(similarities[idx])
                
                # Only include results with reasonable similarity
                if similarity > 0.1:  # Minimum threshold
                    vector_results.append({
                        'employee_data': employee_data[emp_id],
                        'similarity_score': similarity,
                        'search_type': 'cached_vector'
                    })
            
            logger.info(f"✨ Cached vector search found {len(vector_results)} results")
            return vector_results
            
        except Exception as e:
            logger.error(f"❌ Cached vector search error: {e}")
            # Return empty instead of falling back to slow ChromaDB
            return []
    

    
    async def _sql_search(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Semantic SQL search with vector-based skill matching
        Uses embeddings to find related technologies instead of hardcoded patterns
        """
        try:
            logger.info(f"🔍 SQL SEARCH START: parsed_query={parsed_query}")
            
            if not parsed_query:
                logger.info("❌ Empty parsed_query, returning empty results")
                return []
            
            # Log which execution path will be taken
            has_skills = 'skills' in parsed_query
            has_context = 'context' in parsed_query
            print(f"🛤️ EXECUTION PATH: has_skills={has_skills}, has_context={has_context}")
            logger.info(f"🛤️ EXECUTION PATH: has_skills={has_skills}, has_context={has_context}")
            
            # Build dynamic SQL query
            conditions = []
            params = {}
            
            # Combined Skills + Context filter with PARALLEL processing
            if 'skills' in parsed_query and 'context' in parsed_query:
                logger.info("🔀 BRANCH: Skills + Context (using ORIGINAL skills for context filtering)")
                original_skills = parsed_query['skills']
                context = parsed_query['context'].lower()
                logger.info(f"🎯 Skills: {original_skills}, Context: {context}")
                
                if original_skills:
                    # PARALLEL: Run context expansion (no semantic expansion for context-based searches)
                    import asyncio
                    context_task = asyncio.create_task(self._expand_context(context))
                    
                    # Framework mapping (synchronous, fast)
                    framework_to_core = {
                        'spring': 'java', 'spring boot': 'java', 'springboot': 'java', 'hibernate': 'java', 'maven': 'java', 'gradle': 'java',
                        'django': 'python', 'flask': 'python', 'fastapi': 'python',
                        'react': 'javascript', 'reactjs': 'javascript', 'angular': 'javascript', 'angularjs': 'javascript', 'vue': 'javascript', 'vue.js': 'javascript',
                        'nodejs': 'javascript', 'node.js': 'javascript', 'express': 'javascript', 'next.js': 'javascript', 'typescript': 'javascript'
                    }
                    
                    # Wait for context expansion to complete
                    context_terms = await context_task
                    logger.info(f"🌍 Context expansion result: {context_terms}")
                    
                    if len(context_terms) == 1 and context_terms[0] == context:
                        # Fallback to hardcoded aliases
                        context_aliases = {
                            'backend': ['java', 'python', 'nodejs', 'spring', 'django', 'flask'],
                            'frontend': ['react', 'angular', 'vue', 'javascript', 'typescript'],
                            'mobile': ['android', 'ios', 'flutter', 'react native'],
                            'devops': ['docker', 'kubernetes', 'jenkins', 'aws', 'terraform'],
                            'cloud': ['aws', 'gcp', 'azure', 'lambda', 'eks']
                        }
                        context_terms = context_aliases.get(context, [context])
                    
                    combined_conditions = []
                    
                    # Use ORIGINAL skills for context-based filtering to prevent cross-contamination
                    for i, skill in enumerate(original_skills):
                        skill_lower = skill.lower()
                        
                        # Framework/library: match context in tech_group + (exact skill OR core technology)
                        if skill_lower in framework_to_core:
                            core_tech = framework_to_core[skill_lower]
                            # Look for either the exact framework OR the core technology in appropriate context
                            combined_conditions.append(f"(e.tech_group ILIKE :context_{i} AND (e.skill_set ~* :skill_{i} OR e.skill_set ~* :core_{i}))")
                            params[f'context_{i}'] = f'%{context}%'
                            params[f'core_{i}'] = f'\\y{re.escape(core_tech)}\\y'
                        else:
                            # Core technology: match BOTH skill AND context in tech_group
                            tech_conditions = []
                            for j, term in enumerate(context_terms):
                                tech_conditions.append(f"e.tech_group ILIKE :ctx_term_{i}_{j}")
                                params[f'ctx_term_{i}_{j}'] = f'%{term}%'
                            # IMPORTANT: Also check that the skill exists in skill_set
                            combined_conditions.append(f"(({' OR '.join(tech_conditions)}) AND e.skill_set ~* :skill_{i})")
                        
                        # Use regex word boundary matching instead of ILIKE
                        params[f'skill_{i}'] = f'\\y{re.escape(skill.lower())}\\y'
                    
                    if combined_conditions:
                        conditions.append(f"({' OR '.join(combined_conditions)})")
            
            # Skills only filter (when no context provided) - PARALLEL semantic expansion
            elif 'skills' in parsed_query:
                logger.info("🔀 BRANCH: Skills Only (semantic expansion WILL be called)")
                # PARALLEL: Start semantic expansion as background task
                import asyncio
                semantic_task = asyncio.create_task(self._get_semantic_skills(parsed_query['skills']))
                
                # Wait for semantic expansion to complete
                semantic_skills = await semantic_task
                logger.info(f"🧠 Semantic expansion result: {semantic_skills}")
                if semantic_skills:
                    skill_conditions = []
                    for i, skill in enumerate(semantic_skills):
                        skill_conditions.append(f"e.skill_set ~* :skill_{i}")
                        params[f'skill_{i}'] = f'\\y{re.escape(skill.lower())}\\y'
                    
                    if skill_conditions:
                        conditions.append(f"({' OR '.join(skill_conditions)})")
            
            # Context only filter (when no skills provided) - PARALLEL expansion
            elif 'context' in parsed_query:
                logger.info("🔀 BRANCH: Context Only")
                context = parsed_query['context'].lower()
                
                # PARALLEL: Start context expansion as background task
                import asyncio
                context_task = asyncio.create_task(self._expand_context(context))
                
                # Wait for context expansion to complete
                context_terms = await context_task
                if len(context_terms) == 1 and context_terms[0] == context:
                    # Fallback to hardcoded aliases
                    context_aliases = {
                        'backend': ['java', 'python', 'nodejs', 'spring', 'django', 'flask'],
                        'frontend': ['react', 'angular', 'vue', 'javascript', 'typescript'],
                        'mobile': ['android', 'ios', 'flutter', 'react native'],
                        'devops': ['docker', 'kubernetes', 'jenkins', 'aws', 'terraform'],
                        'cloud': ['aws', 'gcp', 'azure', 'lambda', 'eks']
                    }
                    context_terms = context_aliases.get(context, [context])
                
                context_conditions = []
                for i, term in enumerate(context_terms):
                    context_conditions.append(f"e.tech_group ILIKE :context_{i}")
                    params[f'context_{i}'] = f"%{term}%"
                
                if context_conditions:
                    conditions.append(f"({' OR '.join(context_conditions)})")
            
            # Base query with SQL-level filtering for non-technical roles
            base_query = """
            SELECT DISTINCT e.employee_id, e.display_name, e.employee_department, 
                   e.total_exp, e.skill_set, e.emp_location, e.designation, 
                   e.tech_group, e.vvdn_exp, e.pm
            FROM employees e
            WHERE e.designation NOT ILIKE ANY(ARRAY['%manager%', '%director%', '%vp%', '%ceo%', '%cto%', '%admin%', '%hr%'])
            """
            
            # Track if we already have WHERE clause
            has_where_clause = True
            
            # Deployment status filter - STRICT MATCHING (now in projects table)
            if 'deployment' in parsed_query:
                deployment = parsed_query['deployment']
                base_query = base_query.replace("FROM employees e", "FROM employees e LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id")
                if deployment == 'free':
                    conditions.append("(ep.deployment ILIKE '%free%' OR ep.deployment = 'Free')")
                else:
                    conditions.append("ep.deployment ILIKE :deployment")
                    params['deployment'] = f"%{deployment}%"
            
            # Location filter
            if 'location' in parsed_query:
                conditions.append("e.emp_location ILIKE :location")
                params['location'] = f"%{parsed_query['location']}%"
            
            # Department filter
            if 'department' in parsed_query:
                conditions.append("e.employee_department ILIKE :department")
                params['department'] = f"%{parsed_query['department']}%"
            
            # Employee name filter
            if 'employee_name' in parsed_query:
                conditions.append("e.display_name ILIKE :emp_name")
                params['emp_name'] = f"%{parsed_query['employee_name']}%"

            if 'designation' in parsed_query:
                conditions.append("e.designation ILIKE :designation")
                params['designation'] = f"%{parsed_query['designation']}%"
            
            # Project filter - search in employee_projects table
            if 'project' in parsed_query:
                project_name = parsed_query['project']
                if "LEFT JOIN employee_projects ep" not in base_query:
                    base_query = base_query.replace("FROM employees e", "FROM employees e LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id")
                conditions.append("ep.project_name IS NOT NULL")
                conditions.append("(ep.project_name ILIKE :project OR ep.customer ILIKE :project OR ep.project_department ILIKE :project)")
                params['project'] = f"%{project_name}%"
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            logger.info(f"⚡ PARALLEL SQL SEARCH: {parsed_query.get('skills', [])} with context: {parsed_query.get('context', 'None')}")
            
            # Execute query with error handling
            with get_db_session() as session:
                try:
                    result = session.execute(text(base_query), params)
                    sql_results = []
                except Exception as db_error:
                    logger.error(f"❌ Database execution error: {db_error}")
                    return []
                
                for row in result:
                    row_dict = dict(row._mapping)
                    
                    # Apply experience filter (designation filtering now done in SQL)
                    if 'experience_min' in parsed_query:
                        total_exp_years = self._parse_experience_years(row_dict.get('total_exp', ''))
                        vvdn_exp_years = self._parse_experience_years(row_dict.get('vvdn_exp', ''))
                        exp_years = total_exp_years if total_exp_years > 0 else vvdn_exp_years
                        if exp_years < parsed_query['experience_min']:
                            continue
                    
                    row_dict['selection_reason'] = self._generate_selection_reason(row_dict, parsed_query)
                    
                    sql_results.append({
                        'employee_data': row_dict,
                        'match_score': 1.0,
                        'search_type': 'semantic_sql'
                    })
                
                logger.info(f"📈 Parallel SQL Results: Found {len(sql_results)} employees")
                return sql_results
            
        except Exception as e:
            logger.error(f"❌ Parallel SQL search error: {e}")
            return []
        

    async def _sql_search_loose(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Dynamic SQL Search (fully semantic, non-hardcoded)
        - Strict skill matching (no partials)
        - Context/location/deployment filters
        - No hardcoded framework maps
        - Prevents Java ↔ JavaScript and HR/admin noise
        """
        try:
            logger.info(f"🔍 DYNAMIC SQL SEARCH START: parsed_query={parsed_query}")

            if not parsed_query:
                logger.warning("❌ Empty parsed_query — returning empty results")
                return []

            import re
            from sqlalchemy import text

            # === Extract parsed fields ===
            skills = parsed_query.get("skills", [])
            context = parsed_query.get("context")
            location = parsed_query.get("location")
            department = parsed_query.get("department")
            deployment = parsed_query.get("deployment")
            project = parsed_query.get("project")
            experience_min = parsed_query.get("experience_min")
            employee_name = parsed_query.get("employee_name")

            # === Step 1: Semantic skill expansion ===
            semantic_skills = []
            if skills:
                semantic_skills = await self._get_semantic_skills(skills)
                parsed_query["semantic_skills"] = semantic_skills

                logger.info(f"🧠 Semantic skill expansion → {semantic_skills}")

            # === Step 2: Build SQL conditions ===
            conditions = []
            params = {}

            # --- Skill filtering ---
            if semantic_skills:
                skill_subconds = []
                for i, skill in enumerate(semantic_skills):
                    safe_skill = skill.lower().strip()
                    # Match complete tokens separated by comma, space, semicolon, or start/end
                    # pattern = fr"(^|[,\s;|]){re.escape(safe_skill)}([,\s;|]|$)"
                    # pattern = fr"\b{re.escape(safe_skill)}\b(?![a-z])"
                    # skill_subconds.append(f"e.skill_set ~* :skill_{i}")
                    # params[f"skill_{i}"] = pattern
                    pattern = fr"(^|[,\s;|()_-]){re.escape(safe_skill)}([,\s;|()_-]|$)"
                    skill_subconds.append(f"e.skill_set ~* :skill_{i}")
                    params[f"skill_{i}"] = pattern


                if skill_subconds:
                    conditions.append("(" + " OR ".join(skill_subconds) + ")")

            # --- Context filter (direct from parsed_query) ---
            # if context:
            #     context_value = context.lower()
            #     conditions.append("e.tech_group ILIKE :ctx_primary")
            #     params["ctx_primary"] = f"%{context_value}%"

            # --- Context filter (direct from parsed_query) ---
            # --- Context filter (intelligent + adaptive) ---
            if context:
                context_value = context.lower().strip()

                # Normalize for safe regex
                context_pattern = fr"(^|[,\s;|()_-]){re.escape(context_value)}([,\s;|()_-]|$)"

                # Adaptive context logic
                # 1️⃣ If skills exist, make context a soft booster (optional relevance)
                # 2️⃣ If no skills, keep it as a strict filter
                if skills:
                    # Use CASE WHEN to make context soft if skills already strong match
                    conditions.append(f"""
                        (
                            e.tech_group ILIKE :ctx_primary
                            OR e.skill_set ~* :ctx_primary_regex
                            OR (
                                e.tech_group ~* '(backend|frontend|mobile|cloud|data|ai|ml|devops)'
                                AND :ctx_primary IN ('backend','frontend','mobile','cloud','data','ai','ml','devops')
                            )
                        )
                    """)
                    params["ctx_primary"] = f"%{context_value}%"
                    params["ctx_primary_regex"] = context_pattern
                    logger.info(f"🧠 Adaptive context match enabled for '{context_value}' (soft mode)")
                else:
                    # Strict mode for context-only queries
                    conditions.append("e.tech_group ILIKE :ctx_primary")
                    params["ctx_primary"] = f"%{context_value}%"
                    logger.info(f"🧠 Strict context filter applied for '{context_value}' (no explicit skills)")

            # --- Location filter ---
            if location:
                conditions.append("e.emp_location ILIKE :loc")
                params["loc"] = f"%{location}%"

            # --- Department filter ---
            if department:
                conditions.append("e.employee_department ILIKE :dept")
                params["dept"] = f"%{department}%"

            # --- Deployment filter ---
            if deployment:
                conditions.append("ep.deployment ILIKE :dep")
                params["dep"] = f"%{deployment}%"

            # Employee name filter (case-insensitive + punctuation/space tolerant)
            # --- Employee name filter (simple + reliable) ---
            if employee_name:
                emp_name = employee_name.strip()
                if emp_name:
                    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", emp_name).strip()
                    params["emp_name"] = f"%{clean_name}%"
                    
                    # Simple name search with fallback built-in
                    conditions.append("""
                        (
                            e.display_name ILIKE :emp_name
                            OR
                            LOWER(REPLACE(REGEXP_REPLACE(e.display_name, '[^a-zA-Z0-9\\s]', '', 'g'), ' ', ''))
                            LIKE LOWER(REPLACE(REGEXP_REPLACE(:emp_name, '[^a-zA-Z0-9\\s]', '', 'g'), ' ', ''))
                        )
                    """)
                    
                    logger.info(f"🧠 Added smart name filter for: {emp_name}")


            # --- Project filter ---
            if project:
                conditions.append("(ep.project_name ILIKE :proj OR ep.customer ILIKE :proj OR ep.project_department ILIKE :proj)")
                params["proj"] = f"%{project}%"


                conditions.append("""
                (
                REGEXP_REPLACE(LOWER(e.designation), '[^a-z0-9 ]', '', 'g')
                NOT LIKE ANY(ARRAY[
                    'director%',
                    'associate director%',
                    'manager%',
                    '%director%',
                    '%associate director%',
                    '%vp%',
                    '%vice president%',
                    '%manager%',
                    '%product marketing%',
                    '%business partner%',
                    '%talent acquisition%',
                    '%human resource%',
                    '%hr%',
                    '%admin%',
                    '%operations%',
                    '%coordinator%'
                ])
                )
                """)

                # Also exclude HR/Admin/Business tech groups
                conditions.append("""
                (
                REGEXP_REPLACE(LOWER(e.tech_group), '[^a-z0-9 ]', '', 'g')
                NOT LIKE ANY(ARRAY[
                    '%hr%',
                    '%human resource%',
                    '%admin%',
                    '%business%',
                    '%operations%',
                    '%support%'
                ])
                )
                """)


            # --- Ensure non-empty skill sets ---
            conditions.append("COALESCE(e.skill_set, '') <> ''")

            # === Step 3: Construct query ===
            base_query = """
            SELECT DISTINCT e.employee_id, e.display_name, e.employee_department, 
                e.total_exp, e.skill_set, e.emp_location, e.designation, 
                e.tech_group, e.vvdn_exp, e.pm,
                string_agg(DISTINCT ep.project_name, ', ') AS projects,
                string_agg(DISTINCT ep.deployment, ', ') AS deployments
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE TRUE
            """

            if conditions:
                base_query += " AND " + " AND ".join(conditions)

            base_query += " GROUP BY e.employee_id"

            # === Step 4: Execute query ===
            logger.info(f"⚡ Executing dynamic SQL search with {len(conditions)} conditions")

            sql_results = []
            with get_db_session() as session:
                result = session.execute(text(base_query), params)
                for row in result:
                    emp = dict(row._mapping)

                    # --- Optional experience filtering ---
                    if experience_min:
                        exp = self._parse_experience_years(emp.get("total_exp", "")) or 0
                        if exp < experience_min:
                            continue

                    emp["selection_reason"] = self._generate_selection_reason(emp, parsed_query)
                    sql_results.append({
                        "employee_data": emp,
                        "match_score": 1.0,
                        "search_type": "dynamic_sql"
                    })

            logger.info(f"📈 Dynamic SQL found {len(sql_results)} employees")
            return sql_results

        except Exception as e:
            logger.error(f"❌ Dynamic SQL search error: {e}")
            return []


    
    async def _keyword_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Traditional keyword search for fallback
        Useful for catching edge cases that vector/SQL might miss
        """
        try:
            # Simple keyword-based search
            keywords = query.lower().split()
            keyword_conditions = []
            
            for keyword in keywords:
                if len(keyword) > 2:  # Skip very short words
                    keyword_conditions.append(f"""
                        (e.display_name ILIKE '%{keyword}%' OR 
                         e.skill_set ILIKE '%{keyword}%' OR 
                         e.tech_group ILIKE '%{keyword}%' OR
                         e.employee_department ILIKE '%{keyword}%' OR
                         e.emp_location ILIKE '%{keyword}%')
                    """)
            
            if not keyword_conditions:
                return []
            
            sql_query = f"""
            SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department, 
                   ep.project_industry, ep.project_status
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE {' OR '.join(keyword_conditions)}
            """
            
            with get_db_session() as session:
                result = session.execute(text(sql_query))
                keyword_results = []
                
                for row in result:
                    keyword_results.append({
                        'employee_data': dict(row._mapping),
                        'keyword_score': 0.7,  # Medium confidence
                        'search_type': 'keyword'
                    })
                
                return keyword_results
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    def _merge_results(self, vector_results: List, sql_results: List, keyword_results: List, parsed_query: Dict = None) -> List[Dict[str, Any]]:
        """
        Merge results from different search methods and remove duplicates
        Priority: SQL > Vector > Keyword (for same employee)
        For deployment queries, SQL results are FINAL - no additional results added
        """
        merged = {}  # Use employee_id as key to deduplicate
        
        # Add SQL results first (highest priority) - SQL already has location filtering
        for result in sql_results:
            emp_id = result['employee_data'].get('employee_id')
            if emp_id:
                merged[emp_id] = result
        
        # For deployment status queries, return only SQL results (strict filtering)
        # Check if this is a deployment-specific query by looking at the first few results
        if sql_results:
            # If we have SQL results and they all have deployment status, this is likely a deployment query
            deployment_statuses = [r.get('employee_data', {}).get('deployment', '').lower() for r in sql_results[:5]]
            if any(status and ('free' in status or 'billable' in status or 'budgeted' in status or 'support' in status) for status in deployment_statuses):
                logger.info(f"Deployment query detected, returning only SQL results: {len(sql_results)} employees")
                return list(merged.values())
        
        # Apply location filtering to vector results if location specified
        if parsed_query and 'location' in parsed_query:
            required_location = parsed_query['location'].lower()
            filtered_vector_results = []
            for result in vector_results:
                emp_location = result['employee_data'].get('emp_location', '').lower()
                # Exact location matching to avoid partial matches (e.g., kochi vs pollachi)
                if emp_location == required_location or required_location in emp_location.split():
                    filtered_vector_results.append(result)
            vector_results = filtered_vector_results
            logger.info(f"🎯 Location filter applied: {len(vector_results)} employees match '{required_location}'")
        
        # Add vector results (if not already present)
        for result in vector_results:
            emp_id = result['employee_data'].get('employee_id')
            if emp_id and emp_id not in merged:
                merged[emp_id] = result
        
        # Add keyword results (lowest priority)
        for result in keyword_results:
            emp_id = result['employee_data'].get('employee_id')
            if emp_id and emp_id not in merged:
                merged[emp_id] = result
        
        return list(merged.values())
    
    def _business_rerank(self, results: List[Dict], query: str, parsed_query: Dict) -> List[Dict[str, Any]]:
        """
        Apply rule-based business ranking with tech group priority
        """
        for result in results:
            emp_data = result['employee_data']
            
            # Rule-based ranking with detailed breakdown
            designation_score = self._calculate_designation_score(emp_data)
            availability_score = self._calculate_availability_score(emp_data)
            skill_score = self._calculate_skill_relevance(emp_data, parsed_query)
            location_score = self._calculate_location_preference(emp_data, parsed_query)
            experience_score = self._calculate_experience_relevance(emp_data, parsed_query)
            
            tech_group_score = self._calculate_tech_group_relevance(emp_data, parsed_query)
            
            # TECH GROUP PRIORITY: For skill-based queries, tech group match is critical
            has_skill_query = 'skills' in parsed_query or 'context' in parsed_query
            
            if has_skill_query:
                # Tech group matching is highest priority for skill queries
                rule_score = (
                    tech_group_score * 0.40 +      # Highest weight for tech group match
                    skill_score * 0.25 +           # Skills still important
                    availability_score * 0.15 +    # Availability secondary
                    designation_score * 0.10 +     # Designation less important
                    location_score * 0.05 +        # Location minimal
                    experience_score * 0.05         # Experience minimal
                )
            else:
                # Standard weights for non-skill queries
                deployment_lower = emp_data.get('deployment', '').lower()
                if 'free' in deployment_lower:
                    rule_score = (
                        availability_score * 0.35 +
                        designation_score * 0.20 +
                        tech_group_score * 0.20 +
                        skill_score * 0.15 +
                        location_score * 0.05 +
                        experience_score * 0.05
                    )
                else:
                    rule_score = (
                        designation_score * 0.25 +
                        availability_score * 0.20 +
                        tech_group_score * 0.20 +
                        skill_score * 0.20 +
                        location_score * 0.10 +
                        experience_score * 0.05
                    )
            
            result['final_score'] = rule_score
            result['ranking_method'] = 'rule_based'
            result['score_breakdown'] = {
                'designation': designation_score,
                'availability': availability_score,
                'skills': skill_score,
                'tech_group': tech_group_score,
                'location': location_score,
                'experience': experience_score
            }
        
        # Sort by final score (descending)
        return sorted(results, key=lambda x: x['final_score'], reverse=True)
    
    async def _expand_context(self, context: str, top_k: int = 5) -> List[str]:
        """
        Expands user context (like 'backend', 'frontend', 'cloud') into related skills
        using embeddings rather than hardcoded maps.
        """
        try:
            if not self.embedding_cache or not self.embedding_cache.available:
                return [context]
            
            cache_data = await self.embedding_cache.get_cached_employee_embeddings()
            if not cache_data or not cache_data.get('employee_data'):
                return [context]
            
            # Extract all unique skills and tech_groups from employee data
            all_skills = set()
            for emp_data in cache_data['employee_data'].values():
                skills = emp_data.get('skill_set', '').lower()
                tech_group = emp_data.get('tech_group', '').lower()
                
                # Extract skill tokens
                skill_tokens = skills.replace(',', ' ').replace(';', ' ').split()
                tech_tokens = tech_group.replace('-', ' ').split()
                
                for token in skill_tokens + tech_tokens:
                    clean_token = token.strip().lower()
                    if len(clean_token) > 2 and clean_token.isalpha():
                        all_skills.add(clean_token)
            
            # Ensure skill embeddings are loaded
            await self._ensure_skill_embeddings_cache()
            
            # Use cached embeddings for instant similarity computation
            if hasattr(self, 'embedder') and self.embedder and self.skill_embeddings:
                # Get context vector (use cache if available, otherwise encode)
                context_vec = self.skill_embeddings.get(context.lower())
                if context_vec is None:
                    context_vec = self.embedder.encode(context.lower())
                
                similarities = {}
                
                # Use pre-cached skill embeddings for instant similarity
                for skill in all_skills:
                    if skill in self.skill_embeddings:
                        try:
                            skill_vec = self.skill_embeddings[skill]
                            similarity = float(np.dot(context_vec, skill_vec))
                            similarities[skill] = similarity
                        except:
                            continue
                
                # Get top related skills
                top_related = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_k]
                related_skills = [skill for skill, sim in top_related if sim > 0.3]  # Threshold for relevance
                
                if related_skills:
                    cache_status = "cached" if self.skill_embeddings_initialized else "fresh"
                    logger.info(f"⚡ FAST context expansion: '{context}' -> {related_skills[:3]}... ({cache_status})")
                    return related_skills
            
            return [context]
            
        except Exception as e:
            logger.warning(f"Context expansion failed for {context}: {e}")
            return [context]
    
    async def _get_semantic_skills(self, requested_skills: List[str]) -> List[str]:
        """Dynamically expand skills using actual employee data + minimal seed mapping"""
        print(f"🔍 SEMANTIC EXPANSION START: requested_skills={requested_skills}")
        logger.info(f"🔍 SEMANTIC EXPANSION START: requested_skills={requested_skills}")
        
        if not self.available or not requested_skills:
            print(f"❌ Early return: available={self.available}, requested_skills={requested_skills}")
            logger.info(f"❌ Early return: available={self.available}, requested_skills={requested_skills}")
            return requested_skills
        
        try:
            framework_to_core = {
                'spring': 'java', 'hibernate': 'java', 'maven': 'java', 'gradle': 'java',
                'spring boot': 'java', 'springboot': 'java',  # Added spring boot variants
                'django': 'python', 'flask': 'python', 'fastapi': 'python',
                'react': 'javascript', 'angular': 'javascript', 'vue': 'javascript',
                'nodejs': 'javascript', 'typescript': 'javascript'
            }
            
            expanded = set()
            from difflib import get_close_matches

            all_known_skills = set()
            if self.embedding_cache and self.embedding_cache.available:
                try:
                    cache_data = await self.embedding_cache.get_cached_employee_embeddings()
                    if cache_data and cache_data.get("employee_data"):
                        for emp in cache_data["employee_data"].values():
                            skill_str = emp.get("skill_set", "")
                            all_known_skills.update(
                                [s.strip().lower() for s in re.split(r"[,\|;]+", skill_str) if s.strip()]
                            )
                except Exception as e:
                    logger.warning(f"⚠️ Unable to load known skill universe: {e}")

            expanded = set(requested_skills)

            for skill in requested_skills:
                skill_lower = skill.lower().strip()
                expanded.add(skill_lower)

                # Fuzzy expansion: similar tokens from known employee data
                close = get_close_matches(skill_lower, list(all_known_skills), n=5, cutoff=0.75)
                expanded.update(close)

                # Add token-based subword variations
                parts = skill_lower.split()
                if len(parts) > 1:
                    expanded.update(parts)
                simplified = re.sub(r"[^a-z0-9]", "", skill_lower)
                if simplified and simplified != skill_lower:
                    expanded.add(simplified)

            print(f"📋 Initial expanded set: {list(expanded)}")
            logger.info(f"📋 Initial expanded set: {list(expanded)}")
            
            # Employee data-based expansion
            if self.embedding_cache and self.embedding_cache.available:
                print(f"💾 Cache available, starting employee data expansion")
                logger.info(f"💾 Cache available, starting employee data expansion")
                try:
                    cache_data = await self.embedding_cache.get_cached_employee_embeddings()
                    print(f"📊 Cache data keys: {list(cache_data.keys()) if cache_data else 'None'}")
                    logger.info(f"📊 Cache data keys: {list(cache_data.keys()) if cache_data else 'None'}")
                    
                    if cache_data.get('employee_data'):
                        print(f"👥 Found {len(cache_data['employee_data'])} employees in cache")
                        logger.info(f"👥 Found {len(cache_data['employee_data'])} employees in cache")
                        related_skills = set()
                        employees_with_skills = 0
                        
                        # Sample first few employees for debugging
                        sample_employees = list(cache_data['employee_data'].items())[:3]
                        print(f"🔍 Sampling first 3 employees for debugging:")
                        logger.info(f"🔍 Sampling first 3 employees for debugging:")
                        
                        for emp_id, emp_data in cache_data['employee_data'].items():
                            emp_skills = emp_data.get('skill_set', '').lower()
                            emp_tech_group = emp_data.get('tech_group', '').lower()
                            combined_emp_skills = f"{emp_skills} {emp_tech_group}"
                            
                            # Debug first few employees
                            if (emp_id, emp_data) in sample_employees:
                                print(f"👤 Employee {emp_id}: skills='{emp_skills}', tech_group='{emp_tech_group}'")
                                logger.info(f"👤 Employee {emp_id}: skills='{emp_skills}', tech_group='{emp_tech_group}'")
                            
                            # Check if this employee has any of our requested skills
                            has_requested_skill = any(req_skill in combined_emp_skills for req_skill in expanded)
                            
                            if has_requested_skill:
                                employees_with_skills += 1
                                
                                # Extract their other skills as semantic neighbors
                                skill_tokens = emp_skills.replace(',', ' ').replace(';', ' ').split()
                                tech_tokens = emp_tech_group.replace('-', ' ').split()
                                all_tokens = skill_tokens + tech_tokens
                                
                               
                        print(f"👥 Found {employees_with_skills} employees with matching skills")
                        print(f"🎯 Related skills found ({len(related_skills)}): {list(related_skills)[:10]}...")
                        logger.info(f"👥 Found {employees_with_skills} employees with matching skills")
                        logger.info(f"🎯 Related skills found ({len(related_skills)}): {list(related_skills)[:10]}...")
                        
                        # Add most relevant related skills (limit to prevent over-expansion)
                        before_count = len(expanded)
                        expanded.update(list(related_skills)[:8])
                        print(f"📈 Expanded from {before_count} to {len(expanded)} skills")
                        logger.info(f"📈 Expanded from {before_count} to {len(expanded)} skills")
                        
                    else:
                        print(f"❌ No employee_data found in cache")
                        logger.warning(f"❌ No employee_data found in cache")
                        
                except Exception as cache_error:
                    print(f"❌ Cache-based expansion failed: {cache_error}")
                    logger.warning(f"Cache-based expansion failed: {cache_error}")
            else:
                print(f"❌ Cache not available: cache={self.embedding_cache}, available={getattr(self.embedding_cache, 'available', None)}")
                logger.info(f"❌ Cache not available: cache={self.embedding_cache}, available={getattr(self.embedding_cache, 'available', None)}")
            
            # Dynamic expansion limit based on query size
            limit = max(5, min(12, len(requested_skills) * 3))
            result = list(expanded)[:limit]
            
            print(f"🧠 FINAL EXPANSION RESULT: {requested_skills} -> {result}")
            logger.info(f"🧠 FINAL EXPANSION RESULT: {requested_skills} -> {result}")
            return result
            
        except Exception as e:
            print(f"❌ Dynamic skill expansion error: {e}")
            logger.error(f"Dynamic skill expansion error: {e}")
            return requested_skills
    
    async def _get_semantic_skills_new(self, requested_skills: List[str]) -> List[str]:
        """
        Semantic expansion for skills:
        - Strong language-family mapping (JS, Java, Python, etc.)
        - Uses DB skill universe if available
        - Fuzzy expansion
        - Token expansion
        """
        logger.info(f"🔍 SEMANTIC EXPANSION START: requested_skills={requested_skills}")

        if not requested_skills:
            return []

        try:
            # Normalize input
            requested_skills = [s.lower().strip() for s in requested_skills]
            expanded = set(requested_skills)

            # -------------------------------------------------------------
            # 1️⃣ STRONG LANGUAGE-FAMILY SEMANTIC MAP  (MAIN POWER FEATURE)
            # -------------------------------------------------------------
            family_map = {
                # JavaScript ecosystem
                "js": ["javascript", "java script", "nodejs", "node js",
                    "react", "reactjs", "angular", "vue",
                    "typescript", "express", "expressjs", "nextjs", "nestjs"],

                "javascript": ["js", "java script", "nodejs", "reactjs",
                            "angular", "vue", "typescript", "express",
                            "nextjs", "nestjs"],

                "nodejs": ["javascript", "js", "typescript",
                        "express", "nextjs", "nestjs"],

                "react": ["javascript", "js", "reactjs", "typescript"],
                "reactjs": ["javascript", "js", "react", "typescript"],
                "angular": ["javascript", "js", "typescript"],
                "vue": ["javascript", "js", "typescript"],

                # Java ecosystem
                "java": ["spring", "spring boot", "springboot",
                        "core java", "j2ee", "microservices"],

                "spring": ["java", "spring boot"],
                "spring boot": ["java", "spring"],

                # Python ecosystem
                "python": ["django", "flask", "fastapi"],
                "django": ["python"],
                "flask": ["python"],
                "fastapi": ["python"],

                # Mobile dev
                "android": ["kotlin", "java"],
                "kotlin": ["android"],
                "ios": ["swift"],
                "swift": ["ios"],

                # Hybrid
                "flutter": ["dart", "android", "ios"],
                "react native": ["javascript", "react", "android", "ios"],
            }

            # Apply family expansion
            for skill in requested_skills:
                if skill in family_map:
                    expanded.update(family_map[skill])

            # -------------------------------------------------------------
            # 2️⃣ TOKEN EXPANSION (Subwords, "java script" → "javascript")
            # -------------------------------------------------------------
            for skill in list(expanded):
                simple = re.sub(r"[^a-z0-9]", "", skill)
                if simple:
                    expanded.add(simple)

                # split multi-word skills
                for part in skill.replace("-", " ").replace("_", " ").split():
                    if len(part) > 2:
                        expanded.add(part)

            # -------------------------------------------------------------
            # 3️⃣ FUZZY MATCHING USING KNOWN SKILLS FROM DB CACHE (if any)
            # -------------------------------------------------------------
            all_known_skills = set()
            if self.embedding_cache and self.embedding_cache.available:
                try:
                    cache_data = await self.embedding_cache.get_cached_employee_embeddings()
                    for emp in cache_data.get("employee_data", {}).values():
                        skill_str = emp.get("skill_set", "")
                        for token in re.split(r"[,\|; ]+", skill_str.lower()):
                            if token.strip():
                                all_known_skills.add(token.strip())
                except Exception as e:
                    logger.warning(f"⚠️ Failed loading known skills: {e}")

            if all_known_skills:
                from difflib import get_close_matches

                for skill in list(expanded):
                    fuzzy = get_close_matches(skill, list(all_known_skills), n=5, cutoff=0.78)
                    expanded.update(fuzzy)

            result = sorted(list(expanded))


            logger.info(f"🧠 FINAL EXPANSION RESULT: {requested_skills} -> {result}")

            return result

        except Exception as e:
            logger.error(f"❌ Semantic expansion error: {e}")
            return requested_skills

    
    def _are_conflicting_skills(self, skill: str, requested_skills: List[str]) -> bool:
        """Check if a skill conflicts with requested skills using vector similarity"""
        skill_lower = skill.lower()
        
        # Hard conflicts that should never be mixed
        hard_conflicts = {
            'java': ['javascript'],
            'javascript': ['java'],
            'android': ['ios'],
            'ios': ['android'],
            'frontend': ['backend'],
            'backend': ['frontend']
        }
        
        for requested in requested_skills:
            requested_lower = requested.lower()
            
            if requested_lower in hard_conflicts and skill_lower in hard_conflicts[requested_lower]:
                return True
            if skill_lower in hard_conflicts and requested_lower in hard_conflicts[skill_lower]:
                return True
        
        return False

    
    def _calculate_skill_relevance(self, emp_data: Dict, parsed_query: Dict) -> float:
        """Calculate how well employee skills match the query with semantic understanding"""
        if 'skills' not in parsed_query:
            return 0.8
        
        emp_skills = emp_data.get('skill_set', '').lower()
        emp_tech_group = emp_data.get('tech_group', '').lower()
        combined_skills = f"{emp_skills} {emp_tech_group}"
        
        requested_skills = parsed_query['skills']
        
        # Calculate semantic skill relevance
        skill_score = 0.0
        for skill in requested_skills:
            if skill.lower() in combined_skills:
                skill_score += 1.0
        
        return min(1.0, skill_score / len(requested_skills)) if requested_skills else 0.8
    
    def _calculate_tech_group_relevance(self, emp_data: Dict, parsed_query: Dict) -> float:
        """Calculate how well employee's tech group matches the query context"""
        emp_tech_group = emp_data.get('tech_group', '').lower()
        
        # Check for skills that indicate tech group preference
        skills = parsed_query.get('skills', [])
        context = parsed_query.get('context', '')
        
        # STRICT CONTEXT FILTERING: If context is specified, strongly penalize mismatches
        if context:
            context_lower = context.lower()
            
            # Backend context should exclude Android/Mobile developers
            if context_lower == 'backend':
                if 'android' in emp_tech_group or 'mobile' in emp_tech_group:
                    return 0.1  # Strong penalty for Android in backend search
                elif 'backend' in emp_tech_group:
                    return 1.0  # Perfect match
                elif 'java' in emp_tech_group and 'backend' not in emp_tech_group:
                    return 0.3  # Partial match for Java without backend
            
            # Frontend context should exclude Backend/Android
            elif context_lower == 'frontend':
                if 'android' in emp_tech_group or 'backend' in emp_tech_group:
                    return 0.1  # Strong penalty
                elif 'frontend' in emp_tech_group:
                    return 1.0  # Perfect match
            
            # Mobile context should prefer Android/Mobile
            elif context_lower in ['mobile', 'android']:
                if 'android' in emp_tech_group or 'mobile' in emp_tech_group:
                    return 1.0  # Perfect match
                else:
                    return 0.2  # Strong penalty for non-mobile
        
        # Spring Boot should strongly prefer Backend - Java
        if any('spring' in skill.lower() for skill in skills):
            if 'android' in emp_tech_group:
                return 0.1  # Strong penalty for Android
            elif 'backend' in emp_tech_group and 'java' in emp_tech_group:
                return 1.0  # Perfect match
            elif 'java' in emp_tech_group:
                return 0.8   # Good match
            elif 'backend' in emp_tech_group:
                return 0.6   # Partial match
            else:
                return 0.2   # Poor match for Spring Boot
        
        # Java with backend context should exclude Android
        if any('java' in skill.lower() for skill in skills) and context and context.lower() == 'backend':
            if 'android' in emp_tech_group:
                return 0.1  # Strong penalty for Android Java in backend search
            elif 'backend' in emp_tech_group and 'java' in emp_tech_group:
                return 1.0
            elif 'java' in emp_tech_group:
                return 0.5  # Reduced score for Java without backend
            else:
                return 0.3
        
        # React/Angular should prefer Frontend
        if any(skill.lower() in ['react', 'angular', 'vue', 'javascript', 'typescript'] for skill in skills):
            if 'frontend' in emp_tech_group:
                return 1.0
            else:
                return 0.3
        
        # Default neutral score if no specific tech group preference detected
        return 0.5
    
    def _calculate_context_match(self, emp_skills: str, skill: str, context: str) -> float:
        """Calculate context-aware skill matching score"""
        context_lower = context.lower()
        
        # Check if employee has context indicators for the requested domain
        for domain, skill_data in self.skill_categories.items():
            if context_lower in domain or any(ctx in context_lower for ctx in ['backend', 'frontend', 'mobile', 'android', 'devops']):
                context_indicators = skill_data.get('context_indicators', [])
                
                # Boost score if employee has relevant context indicators
                context_matches = sum(1 for indicator in context_indicators if indicator in emp_skills)
                if context_matches > 0:
                    return 1.2  # 20% boost for context match
                
        
        return 1.0  # Neutral score if no clear context indicators
    
    
    def _calculate_experience_relevance(self, emp_data: Dict, parsed_query: Dict) -> float:
        """Calculate experience match score"""
        if 'experience_min' not in parsed_query:
            return 0.8  # Neutral score
        
        total_exp_years = self._parse_experience_years(emp_data.get('total_exp', ''))
        vvdn_exp_years = self._parse_experience_years(emp_data.get('vvdn_exp', ''))
        # Use total_exp if available, otherwise use vvdn_exp
        emp_exp = total_exp_years if total_exp_years > 0 else vvdn_exp_years
        required_exp = parsed_query['experience_min']
        
        if emp_exp >= required_exp:
            # Bonus for having more experience, but diminishing returns
            excess = emp_exp - required_exp
            return min(1.0, 0.8 + (excess * 0.05))  # Max 1.0
        else:
            # Penalty for insufficient experience
            deficit = required_exp - emp_exp
            return max(0.2, 0.8 - (deficit * 0.1))  # Min 0.2
    
    def _calculate_designation_score(self, emp_data: Dict) -> float:
        """Calculate designation-based score"""
        designation = emp_data.get('designation', '').lower().strip()
        
        # Designation hierarchy scoring - Engineer/Sr Engineer are main focus
        designation_scores = {
            'senior engineer': 1.0,      # Main focus - highest priority
            'engineer': 0.95,            # Main focus - second highest
            'senior tech lead': 0.85,    # Secondary focus
            'tech lead': 0.80,           # Secondary focus
            'senior principal engineer': 0.75,  # Lower priority for searches
            'principal engineer': 0.70,  # Lower priority for searches
            'trainee': 0.40              # Lower score for trainees
        }
        
        # If no designation, give neutral score (0.75) to not penalize existing employees
        return designation_scores.get(designation, 0.75)
    
    def _calculate_availability_score(self, emp_data: Dict) -> float:
        """Calculate availability score based on actual deployment status"""
        current_projects = emp_data.get('current_projects', [])
        if not current_projects:
            return 0.9  # No projects = potentially available
        
        # Get actual deployment from projects
        deployment_scores = []
        for project in current_projects:
            deployment = project.get('deployment', '').lower().strip()
            # Normalize deployment names for matching
            normalized_deployment = deployment.replace(' ', '').replace('&', 'and')
            
            # Try exact match first
            score = self.availability_scores.get(deployment, None)
            if score is None:
                score = self.availability_scores.get(normalized_deployment, None)
            
            # Fallback matching for partial matches
            if score is None:
                for key, value in self.availability_scores.items():
                    if key in deployment or deployment in key:
                        score = value
                        break
                score = score or 0.3  # Default low score for unknown deployments
            
            deployment_scores.append(score)
        
        # Use the highest deployment score (best availability)
        return max(deployment_scores) if deployment_scores else 0.3
    
    
    def _calculate_location_preference(self, emp_data: Dict, parsed_query: Dict) -> float:
        """Calculate location preference score using case-insensitive matching"""
        emp_location = emp_data.get('emp_location', '').lower().strip()
        
        # Check if location is mentioned in parsed query
        if 'location' in parsed_query:
            requested_location = parsed_query['location'].lower().strip()
            
            # Exact match (case-insensitive)
            if requested_location == emp_location:
                return 1.0
            
            # Partial match (contains) - case-insensitive
            if requested_location in emp_location or emp_location in requested_location:
                return 0.9
            
            # No match
            return 0.3
        
        # If no specific location in parsed query, return neutral score
        return 0.8
    
    def _parse_experience_years(self, exp_string: str) -> float:
        """Parse experience string to numeric years"""
        if not exp_string:
            return 0.0
        
        # Extract first number from experience string
        numbers = re.findall(r'(\d+\.?\d*)', str(exp_string))
        return float(numbers[0]) if numbers else 0.0
    
    def _generate_selection_reason(self, emp_data: Dict, parsed_query: Dict) -> str:
        """Generate reason for selecting this employee"""
        reasons = []
        
        # Designation reason
        designation = emp_data.get('designation', '')
        if designation:
            designation_lower = designation.lower().strip()
            if designation_lower in ['tech lead', 'senior tech lead', 'principal engineer', 'senior principal engineer']:
                reasons.append(f"Senior level ({designation}) - can handle multiple projects")
            elif designation_lower == 'trainee':
                reasons.append(f"Trainee level - suitable for support roles")
            else:
                reasons.append(f"Designation: {designation}")
        
        # Deployment status reason
        deployment = emp_data.get('deployment', '').lower()
        occupancy = emp_data.get('occupancy', '100')
        if 'deployment' in parsed_query:
            if deployment == 'free':
                reasons.append("Available for new projects")
            elif deployment == 'billable':
                reasons.append(f"Currently billable (occupancy: {occupancy}%)")
            elif deployment == 'budgeted':
                reasons.append(f"Allocated to internal project (occupancy: {occupancy}%)")
        else:
            if deployment == 'free':
                reasons.append("Available for new projects")
            elif deployment:
                reasons.append(f"Status: {deployment} (occupancy: {occupancy}%)")
        
        # Skills match reason
        if 'skills' in parsed_query:
            emp_skills = (emp_data.get('skill_set', '') + ' ' + emp_data.get('tech_group', '')).lower()
            matched_skills = [skill for skill in parsed_query['skills'] if skill in emp_skills]
            if matched_skills:
                reasons.append(f"Has required skills: {', '.join(matched_skills)}")
        
        # Experience reason
        total_exp = emp_data.get('total_exp', '')
        if total_exp:
            reasons.append(f"Experience: {total_exp}")
        
        # Location reason
        location = emp_data.get('emp_location', '')
        if location:
            reasons.append(f"Located in {location}")
        
        # Project status and history
        project = emp_data.get('project_name', '')
        if 'project_search' in parsed_query and parsed_query['project_search']:
            if project:
                reasons.append(f"Worked on project: {project}")
            else:
                reasons.append("Project experience found in history")
        elif project:
            reasons.append(f"Currently on project: {project}")
        else:
            reasons.append("No current project assignment")
        
        return '; '.join(reasons) if reasons else 'Matches search criteria'
    
    def _explain_ranking(self, results: List[Dict]) -> List[str]:
        """Generate human-readable explanations for ranking"""
        explanations = []
        
        for i, result in enumerate(results[:3]):  # Top 3 explanations
            emp_data = result['employee_data']
            scores = result.get('score_breakdown', {})
            
            name = emp_data.get('display_name', 'Employee')
            deployment = emp_data.get('deployment', 'Unknown')
            tech_group = emp_data.get('tech_group', '')
            total_exp = emp_data.get('total_exp', '')
            project = emp_data.get('project_name', 'No project')
            
            explanation = f"{name} ranked #{i+1}: "
            
            # Add detailed reasoning
            reasons = []
            if scores.get('availability', 0) > 0.8:
                reasons.append(f"High availability ({deployment})")
            if scores.get('skills', 0) > 0.8:
                reasons.append(f"Strong skill match ({tech_group})")
            if scores.get('experience', 0) > 0.8:
                reasons.append(f"Good experience fit ({total_exp})")
            if project and project != 'No project':
                reasons.append(f"Currently on {project}")
            
            if reasons:
                explanation += ', '.join(reasons)
            else:
                explanation += f"Available ({deployment}), Skills: {tech_group}, Experience: {total_exp}"
            
            explanations.append(explanation)
        
        return explanations
    
    
    async def index_employees(self) -> Dict[str, Any]:
        """
        Index all employees in vector database for semantic search
        Call this after uploading new employee data
        """
        try:
            # Clear existing collection
            self.chroma_client.delete_collection("employees")
            self.collection = self.chroma_client.create_collection("employees")
            
            # Fetch all employees from database
            with get_db_session() as session:
                result = session.execute(text("""
                    SELECT DISTINCT e.*, ep.project_name, ep.customer, ep.project_department
                    FROM employees e
                    LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
                """))
                
                employees = [dict(row._mapping) for row in result]
            
            if not employees:
                return {"status": "error", "message": "No employees found to index"}
            
            # Create searchable text for each employee
            documents = []
            metadatas = []
            ids = []
            
            for emp in employees:
                # Create rich text representation for embedding
                text_parts = [
                    emp.get('display_name', ''),
                    emp.get('skill_set', ''),
                    emp.get('tech_group', ''),
                    emp.get('employee_department', ''),
                    emp.get('emp_location', ''),
                    emp.get('deployment', ''),
                    emp.get('role', ''),
                    emp.get('project_name', ''),
                    f"Experience: {emp.get('total_exp', '')}"
                ]
                
                searchable_text = ' '.join(filter(None, text_parts))
                
                documents.append(searchable_text)
                metadatas.append(emp)
                ids.append(str(emp.get('employee_id', len(ids))))
            
            # Add to ChromaDB in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
            return {
                "status": "success", 
                "message": f"Indexed {len(employees)} employees for semantic search",
                "indexed_count": len(employees)
            }
            
        except Exception as e:
            logger.error(f"Employee indexing error: {e}")
            return {"status": "error", "message": f"Indexing failed: {str(e)}"}
        
    
    async def _sql_search_optimized(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Smart SQL Search – fully enhanced.
        ✅ Handles Java↔JavaScript ambiguity
        ✅ Context-aware skill normalization
        ✅ Framework-to-core inference
        ✅ Multi-project aggregation (no duplicates)
        ✅ Regex-safe (no substring leaks)
        """
        try:
            # === Step 1: Enrich query with inferred context/core ===
            parsed_query = await self._infer_context_and_core(parsed_query)
            skills = parsed_query.get("skills", [])
            semantic_skills = parsed_query.get("expansions", {}).get("semantic_skills", skills)
            derived_core = list(set(parsed_query.get("derived_core", [])))
            context = parsed_query.get("context", "")
            experience_min = parsed_query.get("experience_min")
            location = parsed_query.get("location")
            department = parsed_query.get("department")
            deployment = parsed_query.get("deployment")
            project = parsed_query.get("project")

            # === Step 2: Lock or infer context ===
            if parsed_query.get("context"):
                context_terms = [parsed_query["context"]]
            else:
                context_terms = parsed_query.get("expansions", {}).get("context_terms", [])

            logger.info(f"🧩 SQL_SEARCH_SMART: skills={skills}, context={context}, core={derived_core}, loc={location}")

            # === Step 3: Framework map ===
            framework_map = {
                # Java / Python / JS frameworks
                "spring boot": ("java", "backend"),
                "spring": ("java", "backend"),
                "hibernate": ("java", "backend"),
                "django": ("python", "backend"),
                "flask": ("python", "backend"),
                "fastapi": ("python", "backend"),
                "react": ("javascript", "frontend"),
                "angular": ("javascript", "frontend"),
                "vue": ("javascript", "frontend"),
                "nodejs": ("javascript", "backend"),
                "express": ("javascript", "backend"),
                
                # Mobile
                "android": ("java", "mobile"),
                "kotlin": ("java", "mobile"),
                "swift": ("ios", "mobile"),
                "flutter": ("dart", "mobile"),
                
                # DevOps
                "terraform": ("cloud", "devops"),
                "docker": ("cloud", "devops"),
            }


            # === Step 4: Canonical normalization helpers ===
            import re
            canonical_map = {
                "javascript": ["js", "java script", "java-script"],
                "typescript": ["type script", "type-script"],
                "springboot": ["spring boot", "spring-boot"],
                "nodejs": ["node js", "node-js"],
                "c++": ["cpp", "c plus plus"],
                "c#": ["c sharp"],
                "postgresql": ["postgre sql", "postgre-sql", "postgres"],
                "html": ["html5"],
                "css": ["css3"],
                "reactjs": ["react js", "react-js"],
                "angularjs": ["angular js", "angular-js"],
            }

            def normalize_skill(skill: str) -> str:
                s = skill.lower().strip().replace("-", " ").replace("_", " ")
                for canon, variants in canonical_map.items():
                    if s in [canon] + variants:
                        return canon
                return s

            def regex_clause(skill_key: str) -> str:
                """Case-insensitive regex clause with word boundaries"""
                return f"e.skill_set ~* :{skill_key}"

            # === Step 5: Sort – frameworks first, then cores ===
            normalized_skills = list(set([normalize_skill(s) for s in semantic_skills]))
            normalized_skills.sort(key=lambda s: 0 if s in framework_map else 1)

            conditions, params, skill_conditions = [], {}, []

            # === Step 6: Skill + Context clause builder ===
            for i, skill in enumerate(normalized_skills):
                s_norm = skill
                skill_key = f"skill_{i}"

                # Regex word-boundary match (no substring leaks)
                clause = regex_clause(skill_key)
                params[skill_key] = fr"\y{s_norm}\y"

                # Core-language with explicit context constraint
                if s_norm in derived_core and context:
                    clause = f"({regex_clause(skill_key)} AND e.tech_group ILIKE :ctx_{i})"
                    params[f"ctx_{i}"] = f"%{context}%"

                # Framework fallback (e.g., Spring Boot → Java backend)
                if s_norm in framework_map:
                    core, ctx = framework_map[s_norm]
                    params[f"core_{i}_fw"] = fr"\y{core}\y"
                    params[f"ctx2_{i}_fw"] = f"%{ctx}%"
                    clause = (
                        f"({clause} OR "
                        f"(e.skill_set ~* :core_{i}_fw AND e.tech_group ILIKE :ctx2_{i}_fw))"
                    )

                skill_conditions.append(f"({clause})")

            if skill_conditions:
                conditions.append("(" + " OR ".join(skill_conditions) + ")")

            # === Step 7: Context terms ===
            if context_terms:
                ctx_cond = " OR ".join([f"e.tech_group ILIKE :ctx_term_{i}" for i in range(len(context_terms))])
                for i, term in enumerate(context_terms):
                    params[f"ctx_term_{i}"] = f"%{term}%"
                conditions.append(f"({ctx_cond})")

            # === Step 8: Generic filters ===
            if location:
                conditions.append("e.emp_location ILIKE :loc")
                params["loc"] = f"%{location}%"
            if department:
                conditions.append("e.employee_department ILIKE :dept")
                params["dept"] = f"%{department}%"
            if deployment:
                conditions.append("ep.deployment ILIKE :dep")
                params["dep"] = f"%{deployment}%"
            if project:
                conditions.append(
                    "(ep.project_name ILIKE :proj OR ep.customer ILIKE :proj OR ep.project_department ILIKE :proj)"
                )
                params["proj"] = f"%{project}%"

            # === Step 9: Context constraints & exclusions ===
            # === Step 9: Context constraints & exclusions (fixed) ===
            if context == "backend":
                conditions.append("(e.tech_group ILIKE '%backend%' OR e.tech_group ILIKE '%fullstack%')")
                conditions.append("e.tech_group NOT ILIKE ANY(ARRAY['%android%', '%mobile%', '%ios%'])")

            elif context == "frontend":
                conditions.append("(e.tech_group ILIKE '%frontend%' OR e.tech_group ILIKE '%fullstack%')")
                conditions.append("e.tech_group NOT ILIKE ANY(ARRAY['%backend%', '%api%', '%server%'])")

            elif context in ["cloud", "devops"]:
                conditions.append("(e.tech_group ILIKE ANY(ARRAY['%cloud%', '%devops%', '%infrastructure%']))")
                conditions.append("e.tech_group NOT ILIKE ANY(ARRAY['%android%', '%mobile%', '%ios%', '%frontend%'])")

            elif context == "mobile":
                conditions.append("e.tech_group ILIKE ANY(ARRAY['%android%', '%mobile%', '%ios%'])")
                conditions.append("e.tech_group NOT ILIKE ANY(ARRAY['%backend%', '%frontend%', '%cloud%', '%devops%'])")

            else:
                # Default – if no context, be permissive
                conditions.append("e.tech_group NOT ILIKE '%admin%'")

            # === Step 10: Base Query with aggregation ===
            base_query = """
            SELECT e.employee_id,
                e.display_name,
                e.employee_department,
                e.total_exp,
                e.skill_set,
                e.emp_location,
                e.designation,
                e.tech_group,
                e.vvdn_exp,
                e.pm,
                string_agg(DISTINCT ep.project_name, ', ') AS projects,
                string_agg(DISTINCT ep.deployment, ', ') AS deployments
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE e.designation NOT ILIKE ANY(ARRAY[
                '%manager%', '%director%', '%vp%', '%ceo%', '%cto%', '%admin%', '%hr%'
            ])
            """
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            base_query += " GROUP BY e.employee_id"

            # === Step 11: Execute ===
            with get_db_session() as session:
                result = session.execute(text(base_query), params)
                sql_results = []
                for row in result:
                    emp = dict(row._mapping)
                    if experience_min:
                        exp = self._parse_experience_years(emp.get("total_exp", "")) or 0
                        if exp < experience_min:
                            continue
                    emp["selection_reason"] = self._generate_selection_reason(emp, parsed_query)
                    sql_results.append({
                        "employee_data": emp,
                        "match_score": 1.0,
                        "search_type": "smart_sql"
                    })

            logger.info(f"📈 Smart SQL found {len(sql_results)} employees")
            return sql_results

        except Exception as e:
            logger.error(f"❌ Smart SQL search error: {e}")
            return []



    async def _infer_context_and_core(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infers core tech + context (backend/frontend/mobile/cloud) from framework skill.
        Uses embeddings to find nearest known framework if missing.
        """
        if not parsed_query.get("skills"):
            return parsed_query

        framework_map = {
            # Java / Python / JS frameworks
            "spring boot": ("java", "backend"),
            "spring": ("java", "backend"),
            "hibernate": ("java", "backend"),
            "django": ("python", "backend"),
            "flask": ("python", "backend"),
            "fastapi": ("python", "backend"),
            "react": ("javascript", "frontend"),
            "angular": ("javascript", "frontend"),
            "vue": ("javascript", "frontend"),
            "nodejs": ("javascript", "backend"),
            "express": ("javascript", "backend"),
            
            # Mobile
            "android": ("java", "mobile"),
            "kotlin": ("java", "mobile"),
            "swift": ("ios", "mobile"),
            "flutter": ("dart", "mobile"),
            
            # DevOps
            "terraform": ("cloud", "devops"),
            "docker": ("cloud", "devops"),
        }


        parsed_query.setdefault("derived_core", [])
        known_frameworks = list(framework_map.keys())
        skills = parsed_query["skills"]

        for skill in skills:
            s_lower = skill.lower().strip()

            # Case 1: Known framework
            if s_lower in framework_map:
                core, ctx = framework_map[s_lower]
                parsed_query["derived_core"].append(core)
                parsed_query.setdefault("context", ctx)
                continue

            # Case 2: Unknown framework → Embedding fallback
            try:
                self._ensure_skill_embeddings_cache()

                # Encode unknown skill if not cached
                if s_lower not in self.skill_embeddings:
                    vec = self.embedder.encode(s_lower)
                else:
                    vec = self.skill_embeddings[s_lower]

                best_match, best_score = None, 0.0
                for known_fw in known_frameworks:
                    known_vec = self.skill_embeddings.get(known_fw)
                    if known_vec is None:
                        continue
                    sim = float(np.dot(vec, known_vec) /
                                (np.linalg.norm(vec) * np.linalg.norm(known_vec)))
                    if sim > best_score:
                        best_match, best_score = known_fw, sim

                if best_match and best_score > 0.35:
                    core, ctx = framework_map[best_match]
                    parsed_query["derived_core"].append(core)
                    parsed_query.setdefault("context", ctx)
                    logger.info(f"🧠 Inferred via embedding: {s_lower} ≈ {best_match} → ({core}, {ctx})")

            except Exception as e:
                logger.warning(f"⚠️ Embedding inference failed for {skill}: {e}")

        return parsed_query

    
    async def _parse_query_with_llm_simplified(self, query: str) -> Dict[str, Any]:
        """
        Simplified Gemini 2.0 Flash Lite parsing with general tech groups.
        Uses broader categories like 'backend', 'frontend' instead of specific tech stacks.
        """
        if not self.llm:
            return {}

        try:
            # Get all tech groups from DB
            from hrms_ai.repositories.employee_repository import EmployeeRepository
            repo = EmployeeRepository()
            tech_groups = repo.get_all_tech_groups()

            # Create simplified mapping - only backend/frontend get generalized
            simplified_groups = set()
            for tg in tech_groups:
                tg_lower = tg.lower()
                if any(x in tg_lower for x in ['backend', 'back end', 'java', 'python', 'node', 'dot net', '.net']):
                    simplified_groups.add('backend')
                elif any(x in tg_lower for x in ['frontend', 'front end', 'react', 'angular', 'vue']):
                    simplified_groups.add('frontend')
                elif any(x in tg_lower for x in ['full stack', 'fullstack']):
                    simplified_groups.add('full stack')
                # Keep mobile categories specific
                elif 'android' in tg_lower:
                    simplified_groups.add('android')
                elif 'ios' in tg_lower:
                    simplified_groups.add('ios')
                elif 'hybrid' in tg_lower:
                    simplified_groups.add('hybrid')

            # Add only backend/frontend as general categories
            simplified_groups.update(['backend', 'frontend', 'android', 'ios', 'hybrid', 'full stack'])
            
            logger.info(f"🧩 Using simplified tech groups: {sorted(simplified_groups)}")

            prompt = f"""
            Parse this HR-related search query into a JSON object.
            Query: "{query}"

            You are parsing for an enterprise HR database that uses these GENERAL TECH CATEGORIES:
            {sorted(simplified_groups)}

            Your task: interpret the query and map it to the most relevant general category above.

            Extract and infer the following keys if mentioned or implied:
            - skills: [list of skills/technologies]
            - context: [list of matching categories] from the list above. Can be multiple for cross-platform skills. Only include if the query involves technical skills.
            - experience_min: integer years
            - experience_max: integer years
            - deployment: one of [free, billable, support, budgeted]
            - location: city or work location
            - department: department name
            - designation: like engineer, sr engineer etc.
            - project: project name/code if mentioned
            - project_search: true if looking for people who worked on a project
            - employee_name: name if specific person requested
            - skill_precision: "strict" if user specifies exact skill or says "exact match"

            Rules:
            1. IMPORTANT: Single words that are not technical terms should be treated as employee_name, NOT skills.
            2. Use appropriate categories:
            - Skills like Java, Python, Node, .NET, C# → context=["backend"]
            - Skills like React, Angular, Vue, HTML, CSS → context=["frontend"]
            - Skills like Android, Kotlin → context=["android"]
            - Skills like iOS, Swift → context=["ios"]
            - Skills like Flutter, React Native → context=["android", "ios", "hybrid"]
            - If it involves both frontend and backend → context=["full stack"]

            3. For cross-platform skills (Flutter, React Native), include multiple contexts.
            4. Only use categories from the list above.
            5. Keep backend/frontend general, but mobile categories specific.
            6. If query is a single word and not a known technology, treat it as employee_name.

            Return ONLY a valid JSON object with the extracted keys.
            """

            try:
                response = self.llm.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "max_output_tokens": 1024
                    }
                )
                
                if response and response.text:
                    parsed = json.loads(response.text.strip())
                    
                    # Post-process: Fix single word queries using DB data
                    query_words = query.strip().split()
                    if len(query_words) == 1:
                        word = query_words[0].lower()
                        
                        # Get known skills from DB via repository
                        known_skills = set()
                        for tg in tech_groups:
                            known_skills.update([s.strip().lower() for s in tg.lower().split() if len(s.strip()) > 2])
                        
                        # Add all skills from database
                        try:
                            all_db_skills = repo.get_all_skills()
                            known_skills.update(all_db_skills)
                        except Exception as e:
                            logger.warning(f"Failed to get skills from DB: {e}")
                        
                        if word not in known_skills:
                            parsed = {'employee_name': query.strip()}
                            logger.info(f"👤 Single word detected as name: {query}")
                    
                    logger.info(f"🧩 LLM parsed query (simplified): {parsed}")
                    return parsed
                else:
                    logger.warning("Empty LLM response for simplified query parsing")
                    return {}
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in simplified query parsing: {e}")
                return {}
            except Exception as e:
                logger.error(f"LLM simplified query parsing error: {e}")
                return {}
        
        except Exception as e:
            logger.error(f"Simplified query parsing failed: {e}")
            return {}
        

    async def _parse_query_with_llm_simplified_fix(self, query: str) -> Dict[str, Any]:
        """
        Simplified Gemini 2.0 Flash Lite parsing with general tech groups.
        Uses broader categories like 'backend', 'frontend' instead of specific tech stacks.
        """
        if not self.llm:
            return {}

        try:
            # Get all tech groups from DB
            from hrms_ai.repositories.employee_repository import EmployeeRepository
            repo = EmployeeRepository()
            tech_groups = repo.get_all_tech_groups()

            # Create simplified mapping - only backend/frontend get generalized
            simplified_groups = set()
            for tg in tech_groups:
                tg_lower = tg.lower()
                if any(x in tg_lower for x in ['backend', 'back end', 'java', 'python', 'node', 'dot net', '.net']):
                    simplified_groups.add('backend')
                elif any(x in tg_lower for x in ['frontend', 'front end', 'react', 'angular', 'vue']):
                    simplified_groups.add('frontend')
                elif any(x in tg_lower for x in ['full stack', 'fullstack']):
                    simplified_groups.add('full stack')
                # Keep mobile categories specific
                elif 'android' in tg_lower:
                    simplified_groups.add('android')
                elif 'ios' in tg_lower:
                    simplified_groups.add('ios')
                elif 'hybrid' in tg_lower:
                    simplified_groups.add('hybrid')

            # Add only backend/frontend as general categories
            simplified_groups.update(['backend', 'frontend', 'android', 'ios', 'hybrid', 'full stack'])
            
            logger.info(f"🧩 Using simplified tech groups: {sorted(simplified_groups)}")

            prompt = f"""
            Parse this HR-related search query into a JSON object.
            Query: "{query}"

            You are parsing for an enterprise HR database that uses these GENERAL TECH CATEGORIES:
            {sorted(simplified_groups)}

            Your task: interpret the query and map it to the most relevant general category above.

            Extract and infer the following keys if mentioned or implied:
            - skills: [list of skills/technologies]
            - context: [list of matching categories] from the list above. Can be multiple for cross-platform skills. Only include if the query involves technical skills.
            - experience_min: integer years
            - experience_max: integer years
            - deployment: one of [free, billable, support, budgeted]
            - location: city or work location
            - department: department name
            - designation: like engineer, sr engineer etc.
            - project: project name/code if mentioned
            - project_search: true if looking for people who worked on a project
            - employee_name: name if specific person requested
            - skill_precision: "strict" if user specifies exact skill or says "exact match"

            Rules for interpreting natural-language queries:
            1. Words like “employees”, “people”, “candidates”, “engineers”, “developers”, 
            “team”, “resources”, “backend engineers”, “frontend developers”, etc.
            are NOT names and NOT automatic designation filters.
            They describe a TYPE OF WORK, not a strict filter.

            2. Only infer a designation when the query explicitly restricts it 
            (e.g., “Senior Engineer only”, “show only junior developers”).

            3. Only infer employee_name when the query clearly refers to an actual person 
            (full name or specific name-like phrase). 
            Words like “all”, “anyone”, “everyone”, “people”, “engineers” must NOT be names.

            4. IMPORTANT: Single words that are not technical terms should be treated as employee_name, NOT skills.
            5. Use appropriate categories:
            - Skills like Java, Python, Node, .NET, C# → context=["backend", "full stack"]
            - Skills like React, Angular, Vue, HTML, CSS → context=["frontend", "full stack"]
            - Skills like Android, Kotlin → context=["android", "hybrid", "android"]
            - Skills like iOS, Swift → context=["ios", "hybrid", "android"]
            - Skills like Flutter, React Native → context=["android", "ios", "hybrid"]
            - If it involves both frontend and backend → context=["full stack", "backend", "frontend"]

            6. For cross-platform skills (Flutter, React Native), include multiple contexts.
            7. If query is a single word and not a known technology, treat it as employee_name.

            8. Never treat generic project-related phrases as a project name.
            Phrases such as “project requirement”, “project needs”, “project work”, 
            “project team”, “project hiring”, “project resources”, “project request”,
            or any other generic noun phrase mentioning the word “project”
            must NOT be interpreted as a project code or project name.

            9. If a skill is used in multiple domains (like JavaScript), include all applicable contexts
            (e.g. "js", "javascript" → frontend + backend + Full stack, "react" → frontend + backend + full stack, "dart" -> android + ios + hybrid).

            - If a skill is unknown, the LLM should decide whether it is backend, frontend, or fullstack by its naming pattern or typical industry usage.

            - Do NOT infer unrelated contexts (e.g., do not map backend skills to mobile).


            Only set the fields:
                    project
                    project_search
            when the query clearly refers to an actual, identifiable project name or code 
            (e.g., 'EXNI_CLRQ', 'Netgear IMDV', 'Extreme project', etc.).


            Return ONLY a valid JSON object with the extracted keys.
            """

            try:
                response = self.llm.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "max_output_tokens": 1024
                    }
                )
                
                if response and response.text:
                    parsed = json.loads(response.text.strip())
                    
                    # Post-process: Fix single word queries using DB data
                    query_words = query.strip().split()
                    if len(query_words) == 1:
                        word = query_words[0].lower()
                        
                        # Get known skills from DB via repository
                        known_skills = set()
                        for tg in tech_groups:
                            known_skills.update([s.strip().lower() for s in tg.lower().split() if len(s.strip()) > 2])
                        
                        # Add all skills from database
                        try:
                            all_db_skills = repo.get_all_skills()
                            known_skills.update(all_db_skills)
                        except Exception as e:
                            logger.warning(f"Failed to get skills from DB: {e}")
                        
                        if word not in known_skills:
                            parsed = {'employee_name': query.strip()}
                            logger.info(f"👤 Single word detected as name: {query}")
                    
                    logger.info(f"🧩 LLM parsed query (simplified): {parsed}")
                    return parsed
                else:
                    logger.warning("Empty LLM response for simplified query parsing")
                    return {}
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in simplified query parsing: {e}")
                return {}
            except Exception as e:
                logger.error(f"LLM simplified query parsing error: {e}")
                return {}
        
        except Exception as e:
            logger.error(f"Simplified query parsing failed: {e}")
            return {}
        

    async def _sql_search_loose_simplified(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simplified SQL Search with multiple context support.
        Handles context as list for cross-platform skills like Flutter.
        """
        try:
            logger.info(f"🔍 SIMPLIFIED SQL SEARCH START: parsed_query={parsed_query}")

            if not parsed_query:
                logger.warning("❌ Empty parsed_query — returning empty results")
                return []

            import re
            from sqlalchemy import text

            skills = parsed_query.get("skills", [])
            context = parsed_query.get("context", [])
            if isinstance(context, str):
                context = [context]
            
            location = parsed_query.get("location")
            department = parsed_query.get("department")
            deployment = parsed_query.get("deployment")
            project = parsed_query.get("project")
            experience_min = parsed_query.get("experience_min")
            employee_name = parsed_query.get("employee_name")

            semantic_skills = []
            if skills:
                semantic_skills = await self._get_semantic_skills(skills)
                parsed_query["semantic_skills"] = semantic_skills
                logger.info(f"🧠 Semantic skill expansion → {semantic_skills}")

            conditions = []
            params = {}

            if semantic_skills:
                skill_subconds = []
                for i, skill in enumerate(semantic_skills):
                    safe_skill = skill.lower().strip()
                    # pattern = fr"(^|[,\s;|()_-]){re.escape(safe_skill)}([,\s;|()_-]|$)"
                    # skill_subconds.append(f"e.skill_set ~* :skill_{i}")
                    # params[f"skill_{i}"] = pattern
                    # skill_subconds.append(f"LOWER(e.skill_set) LIKE :skill_{i}")
                    # params[f"skill_{i}"] = f"%{safe_skill}%"
                    pattern = fr"(^|[^a-z0-9]){re.escape(safe_skill)}([^a-z0-9]|$)(?!\s*script)"
                    skill_subconds.append(f"e.skill_set ~* :skill_{i}")
                    params[f"skill_{i}"] = pattern


                if skill_subconds:
                    conditions.append("(" + " OR ".join(skill_subconds) + ")")

            # if context:
            #     context_subconds = []
            #     for i, ctx in enumerate(context):
            #         ctx_value = ctx.lower().strip()
            #         context_subconds.append(f"e.tech_group ILIKE :ctx_{i}")
            #         params[f"ctx_{i}"] = f"%{ctx_value}%"
                
            #     if context_subconds:
            #         conditions.append("(" + " OR ".join(context_subconds) + ")")
            #         logger.info(f"🧠 Multiple context filter applied: {context}")

            # New: Expand context based on skills
            if context:
                context_subconds = []
                for i, ctx in enumerate(set(context)):
                    normalized_ctx = ctx.lower().replace(" ", "")
                    context_subconds.append(
                        f"REPLACE(LOWER(e.tech_group), ' ', '') LIKE :ctx_{i}"
                    )
                    params[f"ctx_{i}"] = f"%{normalized_ctx}%"
                
                conditions.append("(" + " OR ".join(context_subconds) + ")")
                logger.info(f"🧠 Normalized context filter applied: {context}")

            if location:
                conditions.append("e.emp_location ILIKE :loc")
                params["loc"] = f"%{location}%"
            if department:
                conditions.append("e.employee_department ILIKE :dept")
                params["dept"] = f"%{department}%"
            if deployment:
                conditions.append("ep.deployment ILIKE :dep")
                params["dep"] = f"%{deployment}%"
            if project:
                conditions.append("(ep.project_name ILIKE :proj OR ep.customer ILIKE :proj OR ep.project_department ILIKE :proj)")
                params["proj"] = f"%{project}%"

            if employee_name:
                emp_name = employee_name.strip()
                if emp_name:
                    params["emp_name"] = f"%{emp_name}%"
                    conditions.append("e.display_name ILIKE :emp_name")

            if not employee_name:
                conditions.append("""
                    (
                    REGEXP_REPLACE(LOWER(e.designation), '[^a-z0-9 ]', '', 'g')
                    NOT LIKE ANY(ARRAY[
                        'director%', 'associate director%', 'manager%', '%director%',
                        '%associate director%', '%vp%', '%vice president%', '%manager%',
                        '%product marketing%', '%business partner%', '%talent acquisition%',
                        '%human resource%', '%hr%', '%admin%', '%operations%', '%coordinator%'
                    ])
                    )
                """)

                conditions.append("""
                    (
                    REGEXP_REPLACE(LOWER(e.tech_group), '[^a-z0-9 ]', '', 'g')
                    NOT LIKE ANY(ARRAY['%hr%', '%human resource%', '%admin%', '%business%', '%operations%', '%support%'])
                    )
                """)

                conditions.append("COALESCE(e.skill_set, '') <> ''")

            base_query = """
            SELECT e.employee_id, e.display_name, e.employee_department, 
                e.total_exp, e.skill_set, e.emp_location, e.designation, 
                e.tech_group, e.vvdn_exp, e.pm,
                string_agg(DISTINCT ep.project_name, ', ') AS projects,
                string_agg(DISTINCT ep.deployment, ', ') AS deployments
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE TRUE
            """
            
            if not employee_name:
                base_query += """
                AND e.designation NOT ILIKE ANY(ARRAY[
                    '%manager%', '%director%', '%vp%', '%ceo%', '%cto%', '%admin%', '%hr%'
                ])
                """
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            base_query += " GROUP BY e.employee_id"

            logger.info(f"⚡ Executing simplified SQL search with {len(conditions)} conditions")

            sql_results = []
            with get_db_session() as session:
                result = session.execute(text(base_query), params)
                for row in result:
                    emp = dict(row._mapping)
                    if experience_min:
                        exp = self._parse_experience_years(emp.get("total_exp", "")) or 0
                        if exp < experience_min:
                            continue
                    emp["selection_reason"] = self._generate_selection_reason(emp, parsed_query)
                    sql_results.append({
                        "employee_data": emp,
                        "match_score": 1.0,
                        "search_type": "simplified_sql"
                    })

            logger.info(f"📈 Simplified SQL found {len(sql_results)} employees")
            return sql_results

        except Exception as e:
            logger.error(f"❌ Simplified SQL search error: {e}")
            return []
        

    async def _parse_query_with_llm_simplified_fix_semantic(self, query: str) -> Dict[str, Any]:
        """
        Simplified Gemini 2.0 Flash Lite parsing with general tech groups.
        Uses broader categories like 'backend', 'frontend' instead of specific tech stacks.
        """
        if not self.llm:
            return {}

        try:
            # Get all tech groups from DB
            from hrms_ai.repositories.employee_repository import EmployeeRepository
            repo = EmployeeRepository()
            tech_groups = repo.get_all_tech_groups()

            # Create simplified mapping - only backend/frontend get generalized
            simplified_groups = set()
            for tg in tech_groups:
                tg_lower = tg.lower()
                if any(x in tg_lower for x in ['backend', 'back end', 'java', 'python', 'node', 'dot net', '.net']):
                    simplified_groups.add('backend')
                elif any(x in tg_lower for x in ['frontend', 'front end', 'react', 'angular', 'vue']):
                    simplified_groups.add('frontend')
                elif any(x in tg_lower for x in ['full stack', 'fullstack', 'full-stack']):
                    simplified_groups.add('full stack')
                # Keep mobile categories specific
                elif 'android' in tg_lower:
                    simplified_groups.add('android')
                elif 'ios' in tg_lower:
                    simplified_groups.add('ios')
                elif 'hybrid' in tg_lower:
                    simplified_groups.add('hybrid')

            # Add only backend/frontend as general categories
            simplified_groups.update(['backend', 'frontend', 'android', 'ios', 'hybrid', 'full stack'])
            
            logger.info(f"🧩 Using simplified tech groups: {sorted(simplified_groups)}")

            prompt = f"""
            Parse this HR-related search query into a JSON object.
            Query: "{query}"

            You are parsing for an enterprise HR database that uses these GENERAL TECH CATEGORIES:
            {sorted(simplified_groups)}

            Available actual tech groups from database:
            {tech_groups}

            Your task: interpret the query and map it to the most relevant general category above.

            Extract and infer the following keys if mentioned or implied:
            - skills: [list of skills/technologies]
            - context: [list of matching categories] from the list above. Can be multiple for cross-platform skills. Only include if the query involves technical skills.
            - actual_context: [list of actual tech group names from database] that match the skills. Use exact names from the available tech groups list.
            - experience_min: integer years
            - experience_max: integer years
            - deployment: one of [free, billable, support, budgeted]
            - location: city or work location
            - department: department name
            - designation: like engineer, sr engineer etc.
            - project: project name/code if mentioned
            - project_search: true if looking for people who worked on a project
            - employee_name: name if specific person requested
            - skill_precision: "strict" if user specifies exact skill or says "exact match"
            - You MUST always include a field named "semantic_skills".
                - It must be a list.
                - semantic_skills must include related technologies, framework but stay relevant.
                - It must NEVER be empty, unless no skills are provided from query.

            Rules for interpreting natural-language queries:
            1. Words like “employees”, “people”, “candidates”, “engineers”, “developers”, 
            “team”, “resources”, “backend engineers”, “frontend developers”, etc.
            are NOT names and NOT automatic designation filters.
            They describe a TYPE OF WORK, not a strict filter.

            2. Only infer a designation when the query explicitly restricts it 
            (e.g., “Senior Engineer only”, “show only junior developers”).

            3. Only infer employee_name when the query clearly refers to an actual person 
            (full name or specific name-like phrase). 
            Words like “all”, “anyone”, “everyone”, “people”, “engineers” must NOT be names.

            4. IMPORTANT: Single words that are not technical terms should be treated as employee_name, NOT skills.
            5. Use appropriate categories:
            - Skills like Java, Python, Node, .NET, C# → context=["backend", "full stack"]
            - Skills like React, Angular, Vue, HTML, CSS → context=["frontend", "full stack"]
            - Skills like Android, Kotlin → context=["android", "hybrid", "android"]
            - Skills like iOS, Swift → context=["ios", "hybrid", "android"]
            - Skills like Flutter, React Native → context=["android", "ios", "hybrid"]
            - If it involves both frontend and backend → context=["full stack", "backend", "frontend"]

            6. For cross-platform skills (Flutter, React Native), include multiple contexts.
            7. If query is a single word and not a known technology, treat it as employee_name.

            8. Never treat generic project-related phrases as a project name.
            Phrases such as “project requirement”, “project needs”, “project work”, 
            “project team”, “project hiring”, “project resources”, “project request”,
            or any other generic noun phrase mentioning the word “project”
            must NOT be interpreted as a project code or project name.

            9. If a skill is used in multiple domains (like JavaScript), include all applicable contexts
            (e.g. "js", "javascript" → frontend + backend + Full stack, "react" → frontend + backend + full stack, "dart" -> android + ios + hybrid).

            - If a skill is unknown, the LLM should decide whether it is backend, frontend, or fullstack by its naming pattern or typical industry usage.

            - Do NOT infer unrelated contexts (e.g., do not map backend skills to mobile).


            Only set the fields:
                    project
                    project_search
            when the query clearly refers to an actual, identifiable project name or code 
            (e.g., 'EXNI_CLRQ', 'Netgear IMDV', 'Extreme project', etc.).


            Return ONLY a valid JSON object with the extracted keys.
            """

            try:
                llm_resp = self.llm.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "max_output_tokens": 1024
                    }
                )

                if not llm_resp or not llm_resp.text:
                    return {}

                parsed = json.loads(llm_resp.text.strip())

                skills = parsed.get("skills", []) or []
                semantic = parsed.get("semantic_skills", []) or []
                actual_context = parsed.get("actual_context", []) or []

                merged = []
                for s in skills + semantic:
                    s = s.strip().lower()
                    if s and s not in merged:
                        merged.append(s)

                parsed["skills"] = merged
                parsed["semantic_skills"] = semantic  # keep metadata separately
                parsed["actual_context"] = actual_context  # keep actual tech groups

                # ---- SINGLE WORD NAME DETECTION ----
                # (Only treat as name when NOT a known technology)
                if len(query.split()) == 1:
                    word = query.strip().lower()
                    known_skills = set(repo.get_all_skills())

                    if word not in known_skills and word not in merged:
                        return {"employee_name": query.strip()}

                logger.info(f"🧩 LLM parsed query: {parsed}")
                return parsed

            except Exception as e:
                logger.error(f"❌ Query parsing failed: {e}")
                return {}
        
        except Exception as e:
            logger.error(f"Simplified query parsing failed: {e}")
            return {}
        

    async def _sql_search_loose_simplified_semantic(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simplified SQL Search with multiple context support.
        Handles context as list for cross-platform skills like Flutter.
        """
        try:
            logger.info(f"🔍 SIMPLIFIED SQL SEARCH START: parsed_query={parsed_query}")

            if not parsed_query:
                logger.warning("❌ Empty parsed_query — returning empty results")
                return []

            import re
            from sqlalchemy import text

            skills = parsed_query.get("skills", [])
            
            context = parsed_query.get("context", [])
            if isinstance(context, str):
                context = [context]
            
            location = parsed_query.get("location")
            department = parsed_query.get("department")
            deployment = parsed_query.get("deployment")
            project = parsed_query.get("project")
            experience_min = parsed_query.get("experience_min")
            employee_name = parsed_query.get("employee_name")

            # semantic_skills = []
            # if skills:
            #     semantic_skills = await self._get_semantic_skills(skills)
            #     parsed_query["semantic_skills"] = semantic_skills
            #     logger.info(f"🧠 Semantic skill expansion → {semantic_skills}")

            conditions = []
            params = {}

            # if semantic_skills:
            #     skill_subconds = []
            #     for i, skill in enumerate(semantic_skills):
            #         safe_skill = skill.lower().strip()
            #         # pattern = fr"(^|[,\s;|()_-]){re.escape(safe_skill)}([,\s;|()_-]|$)"
            #         # skill_subconds.append(f"e.skill_set ~* :skill_{i}")
            #         # params[f"skill_{i}"] = pattern
            #         # skill_subconds.append(f"LOWER(e.skill_set) LIKE :skill_{i}")
            #         # params[f"skill_{i}"] = f"%{safe_skill}%"
            #         pattern = fr"(^|[^a-z0-9]){re.escape(safe_skill)}([^a-z0-9]|$)(?!\s*script)"
            #         skill_subconds.append(f"e.skill_set ~* :skill_{i}")
            #         params[f"skill_{i}"] = pattern


            #     if skill_subconds:
            #         conditions.append("(" + " OR ".join(skill_subconds) + ")")

            if skills:
                skill_subconds = []

                for i, skill in enumerate(skills):
                    safe = skill.lower().strip()

                    # Regex: match full tokens, but avoid "java" inside "javascript"
                    pattern = fr"(^|[^a-z0-9]){re.escape(safe)}([^a-z0-9]|$)"
                    skill_subconds.append(f"e.skill_set ~* :skill_{i}")
                    params[f"skill_{i}"] = pattern

                conditions.append("(" + " OR ".join(skill_subconds) + ")")
                logger.info(f"🧠 Skill filters applied: {skills}")

            # if context:
            #     context_subconds = []
            #     for i, ctx in enumerate(context):
            #         ctx_value = ctx.lower().strip()
            #         context_subconds.append(f"e.tech_group ILIKE :ctx_{i}")
            #         params[f"ctx_{i}"] = f"%{ctx_value}%"
                
            #     if context_subconds:
            #         conditions.append("(" + " OR ".join(context_subconds) + ")")
            #         logger.info(f"🧠 Multiple context filter applied: {context}")

            # New: Expand context based on skills
            if context:
                context_subconds = []
                for i, ctx in enumerate(set(context)):
                    normalized_ctx = ctx.lower().replace(" ", "")
                    context_subconds.append(
                        f"REPLACE(LOWER(e.tech_group), ' ', '') LIKE :ctx_{i}"
                    )
                    params[f"ctx_{i}"] = f"%{normalized_ctx}%"
                
                conditions.append("(" + " OR ".join(context_subconds) + ")")
                logger.info(f"🧠 Normalized context filter applied: {context}")

            if location:
                conditions.append("e.emp_location ILIKE :loc")
                params["loc"] = f"%{location}%"
            if department:
                conditions.append("e.employee_department ILIKE :dept")
                params["dept"] = f"%{department}%"
            if deployment:
                conditions.append("ep.deployment ILIKE :dep")
                params["dep"] = f"%{deployment}%"
            if project:
                conditions.append("(ep.project_name ILIKE :proj OR ep.customer ILIKE :proj OR ep.project_department ILIKE :proj)")
                params["proj"] = f"%{project}%"

            if employee_name:
                emp_name = employee_name.strip()
                if emp_name:
                    params["emp_name"] = f"%{emp_name}%"
                    conditions.append("e.display_name ILIKE :emp_name")

            if not employee_name:
                conditions.append("""
                    (
                    REGEXP_REPLACE(LOWER(e.designation), '[^a-z0-9 ]', '', 'g')
                    NOT LIKE ANY(ARRAY[
                        'director%', 'associate director%', 'manager%', '%director%',
                        '%associate director%', '%vp%', '%vice president%', '%manager%',
                        '%product marketing%', '%business partner%', '%talent acquisition%',
                        '%human resource%', '%hr%', '%admin%', '%operations%', '%coordinator%'
                    ])
                    )
                """)

                conditions.append("""
                    (
                    REGEXP_REPLACE(LOWER(e.tech_group), '[^a-z0-9 ]', '', 'g')
                    NOT LIKE ANY(ARRAY['%hr%', '%human resource%', '%admin%', '%business%', '%operations%', '%support%'])
                    )
                """)

                conditions.append("COALESCE(e.skill_set, '') <> ''")

            base_query = """
            SELECT e.employee_id, e.display_name, e.employee_department, 
                e.total_exp, e.skill_set, e.emp_location, e.designation, 
                e.tech_group, e.vvdn_exp, e.pm, e.rm_id, e.rm_name, 
                string_agg(DISTINCT ep.project_name, ', ') AS projects,
                string_agg(DISTINCT ep.deployment, ', ') AS deployments
            FROM employees e
            LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id
            WHERE TRUE
            """
            
            if not employee_name:
                base_query += """
                AND e.designation NOT ILIKE ANY(ARRAY[
                    '%manager%', '%director%', '%vp%', '%ceo%', '%cto%', '%admin%', '%hr%'
                ])
                """
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            base_query += " GROUP BY e.employee_id"

            logger.info(f"⚡ Executing simplified SQL search with {len(conditions)} conditions")

            sql_results = []
            with get_db_session() as session:
                result = session.execute(text(base_query), params)
                for row in result:
                    emp = dict(row._mapping)
                    if experience_min:
                        exp = self._parse_experience_years(emp.get("total_exp", "")) or 0
                        if exp < experience_min:
                            continue
                    emp["selection_reason"] = self._generate_selection_reason(emp, parsed_query)
                    sql_results.append({
                        "employee_data": emp,
                        "match_score": 1.0,
                        "search_type": "simplified_sql"
                    })

            logger.info(f"📈 Simplified SQL found {len(sql_results)} employees")
            return sql_results

        except Exception as e:
            logger.error(f"❌ Simplified SQL search error: {e}")
            return []