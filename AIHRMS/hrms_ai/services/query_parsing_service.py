"""
Query Parsing Service - Enhanced LLM query parsing
"""
import logging
from typing import Dict, Any, List
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class QueryParsingService:
    """Service for enhanced query parsing with LLM"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def parse_query(self, query: str) -> Dict[str, Any]:
        """Enhanced query parsing with optimized Gemini Flash 2.5 prompt"""
        try:
            logger.info(f"🔍 Starting query parsing for: '{query}'")
            
            # Optimized Gemini Flash 2.5 parsing prompt
            parsing_prompt = f"""
You are a query parser for an Employee Search system.

Extract structured information from this HR search query:
"{query}"

Return a JSON with these exact keys:
{{
  "intent": "",                      # describe what user wants (e.g., find employees, get details, etc.)
  "required_skills": [],             # list of skills like [java, react, python]
  "experience": "",                  # number or range like "3 years", ">=5 years", "junior/mid/senior"
  "location": "",                    # city or region name
  "availability": "",                # free pool, 40%, <50%, >70%, etc.
  "project_domain": "",              # fintech, ecommerce, healthcare, etc.
  "manager_name": "",                # if a manager or reporting relation is mentioned
  "employee_name": "",               # if specific person requested (e.g., person1)
  "department": "",                  # if mentioned
  "multi_intent": false              # true if multiple intents like skill+availability
}}

Examples:
1. "show employees working as java with 3 years experience in Kochi"
   → {{
       "intent": "find employees skilled in java with 3 years experience in kochi",
       "required_skills": ["java"],
       "experience": "3 years",
       "location": "kochi"
     }}

2. "employees who are in free pool"
   → {{
       "intent": "find employees currently in free pool",
       "availability": "free pool"
     }}

3. "I want details of person1"
   → {{
       "intent": "get details of a specific employee",
       "employee_name": "person1"
     }}

4. "React developers available 40% for ecommerce project"
   → {{
       "intent": "find react developers available 40% for ecommerce project",
       "required_skills": ["react"],
       "availability": "40%",
       "project_domain": "ecommerce",
       "multi_intent": true
     }}

If no relevant info is found for a field, leave it empty (e.g., "location": "").
Return only valid JSON — no text before or after.
            """
            
            # Get AI response
            ai_response = await self.llm_service.generate_response(parsing_prompt)
            logger.info(f"🤖 Raw AI response: {ai_response[:200]}...")
            
            # Parse JSON response
            try:
                import json
                # Clean up markdown code blocks if present
                clean_response = ai_response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()
                
                parsed_result = json.loads(clean_response)
                logger.info(f"✅ Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parsing failed: {e}")
                logger.info(f"🔄 Attempting fallback parsing...")
                parsed_result = self._enhanced_fallback_parsing(query)
            
            # Enhanced validation and normalization
            validated_result = self._validate_and_enhance_parsing(parsed_result, query)
            
            # Log detailed parsing results
            logger.info(f"📋 Parsed Query Results:")
            logger.info(f"   Intent: {validated_result.get('intent')}")
            logger.info(f"   Query Type: {validated_result.get('query_type')}")
            logger.info(f"   Skills: {validated_result.get('required_skills')}")
            logger.info(f"   Domain: {validated_result.get('project_domain')}")
            logger.info(f"   Availability: {validated_result.get('availability')}")
            logger.info(f"   Multi-intent: {validated_result.get('multi_intent')}")
            logger.info(f"   Location: {validated_result.get('location')}")
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Query parsing error: {e}")
            # Return basic fallback structure
            return self._enhanced_fallback_parsing(query)
    
    def _parse_llm_response(self, llm_response: str, original_query: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        try:
            # Enhanced parsing with project awareness
            # Extract information first
            extracted_skills = self._extract_basic_skills(original_query)
            extracted_domain = self._extract_domain(original_query)
            extracted_availability = self._extract_availability(original_query)
            is_multi_intent = self._detect_multi_intent(original_query)
            
            # Determine query type based on extracted information
            query_type = "general"
            if extracted_skills:
                query_type = "skill_search"
            elif extracted_domain:
                query_type = "project_search"
            elif extracted_availability:
                query_type = "availability_search"
            
            parsed = {
                "original_query": original_query,
                "query_type": query_type,
                "required_skills": extracted_skills,
                "experience_level": "any",
                "availability_required": extracted_availability,
                "location": None,
                "project_domain": extracted_domain,
                "project_experience": None,
                "department": None,
                "occupancy_constraint": self._extract_occupancy_constraint(original_query),
                "multi_intent": is_multi_intent,
                "intent": "Find employees matching the query"
            }
            
            # Extract information from LLM response
            lines = llm_response.lower().split('\n')
            
            for line in lines:
                if 'query type:' in line:
                    parsed["query_type"] = line.split(':')[1].strip()
                elif 'required skills:' in line:
                    skills_text = line.split(':')[1].strip()
                    parsed["required_skills"] = [s.strip() for s in skills_text.split(',') if s.strip()]
                elif 'experience level:' in line:
                    parsed["experience_level"] = line.split(':')[1].strip()
                elif 'location:' in line:
                    location = line.split(':')[1].strip()
                    if location and location != 'none':
                        parsed["location"] = location
                elif 'project domain:' in line:
                    domain = line.split(':')[1].strip()
                    if domain and domain != 'none':
                        parsed["project_domain"] = domain
                elif 'project experience:' in line:
                    proj_exp = line.split(':')[1].strip()
                    if proj_exp and proj_exp != 'none':
                        parsed["project_experience"] = proj_exp
                elif 'department:' in line:
                    dept = line.split(':')[1].strip()
                    if dept and dept != 'none':
                        parsed["department"] = dept
                elif 'occupancy constraint:' in line:
                    occupancy = line.split(':')[1].strip()
                    if occupancy and occupancy != 'none':
                        parsed["occupancy_constraint"] = occupancy
                elif 'multi intent:' in line:
                    multi = line.split(':')[1].strip().lower()
                    parsed["multi_intent"] = multi == 'true'
                elif 'intent:' in line:
                    parsed["intent"] = line.split(':')[1].strip()
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Use fallback parsing instead of raising
            return self._enhanced_fallback_parsing(original_query)
    
    def _enhanced_fallback_parsing(self, query: str) -> Dict[str, Any]:
        """Enhanced fallback parsing with better skill detection"""
        logger.info(f"🔧 Using enhanced fallback parsing for: '{query}'")
        
        # Extract information
        extracted_skills = self._extract_basic_skills(query)
        extracted_domain = self._extract_domain(query)
        extracted_availability = self._extract_availability(query)
        is_multi_intent = self._detect_multi_intent(query)
        
        # Determine query type
        query_type = "general"
        if extracted_skills:
            query_type = "skill_search"
        elif extracted_domain:
            query_type = "project_search"
        elif extracted_availability:
            query_type = "availability_search"
        
        result = {
            "original_query": query,
            "query_type": query_type,
            "required_skills": extracted_skills,
            "experience_level": "any",
            "availability_required": extracted_availability,
            "location": None,
            "project_domain": extracted_domain,
            "project_experience": None,
            "department": None,
            "occupancy_constraint": self._extract_occupancy_constraint(query),
            "multi_intent": is_multi_intent,
            "intent": "Find employees matching the query"
        }
        
        logger.info(f"📝 Enhanced fallback parsing result: Type={query_type}, Skills={extracted_skills}, Domain={extracted_domain}")
        return result
    

    
    def _extract_basic_skills(self, query: str) -> List[str]:
        """Basic skill extraction without LLM"""
        common_skills = [
            'java', 'python', 'javascript', 'react', 'angular', 'spring', 'node',
            'aws', 'docker', 'kubernetes', 'sql', 'mongodb', 'postgresql',
            'machine learning', 'ai', 'data science', 'devops', 'frontend', 'backend',
            'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            'vue', 'express', 'django', 'flask', 'laravel', 'rails'
        ]
        
        query_lower = query.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in query_lower:
                found_skills.append(skill)
        
        logger.info(f"🔍 Skill extraction: Found {found_skills} in '{query}'")
        return found_skills
    
    def _extract_availability(self, query: str) -> str:
        """Extract availability requirements from query"""
        import re
        query_lower = query.lower()
        
        # Look for percentage patterns
        percentage_patterns = [
            r'<\s*(\d+)%',  # <50%
            r'>\s*(\d+)%',  # >30%
            r'(\d+)%\s*available',  # 40% available
            r'available\s*(\d+)%',  # available 40%
        ]
        
        for pattern in percentage_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_domain(self, query: str) -> str:
        """Extract project domain from query"""
        domains = [
            'fintech', 'ecommerce', 'e-commerce', 'healthcare', 'banking', 
            'insurance', 'retail', 'education', 'logistics', 'manufacturing'
        ]
        
        query_lower = query.lower()
        for domain in domains:
            if domain in query_lower:
                return domain.replace('-', '')
        
        return None
    
    def _extract_occupancy_constraint(self, query: str) -> str:
        """Extract occupancy constraints"""
        query_lower = query.lower()
        
        if 'available' in query_lower or 'free' in query_lower:
            return 'available'
        elif 'partial' in query_lower or '<' in query_lower:
            return 'partially_available'
        
        return None
    
    def _detect_multi_intent(self, query: str) -> bool:
        """Detect if query has multiple intents"""
        query_lower = query.lower()
        
        # Check for different types of intents
        has_skills = bool(self._extract_basic_skills(query))
        has_availability = any(word in query_lower for word in ['available', 'free', '%', 'capacity'])
        has_domain = bool(self._extract_domain(query))
        has_experience = any(word in query_lower for word in ['experience', 'worked on', 'project', 'years'])
        has_location = any(word in query_lower for word in ['bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune', 'kochi'])
        
        intent_count = sum([has_skills, has_availability, has_domain, has_experience, has_location])
        
        logger.info(f"📊 Multi-intent analysis: Skills={has_skills}, Availability={has_availability}, Domain={has_domain}, Experience={has_experience}, Location={has_location} -> Count={intent_count}")
        
        return intent_count >= 2
    
    def _validate_and_enhance_parsing(self, parsed_result: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Validate and enhance parsed results with backward compatibility"""
        try:
            # Convert new format to old format for backward compatibility
            enhanced_result = {
                "original_query": original_query,
                "intent": parsed_result.get("intent", "Find employees matching the query"),
                "query_type": self._determine_query_type(parsed_result),
                "required_skills": parsed_result.get("required_skills", []),
                "experience_level": parsed_result.get("experience", "any"),
                "availability_required": parsed_result.get("availability", ""),
                "location": parsed_result.get("location", ""),
                "project_domain": parsed_result.get("project_domain", ""),
                "manager_name": parsed_result.get("manager_name", ""),
                "employee_name": parsed_result.get("employee_name", ""),
                "department": parsed_result.get("department", ""),
                "multi_intent": parsed_result.get("multi_intent", False),
                "occupancy_constraint": self._extract_occupancy_constraint(original_query)
            }
            
            # Normalize empty strings to None for consistency
            for key, value in enhanced_result.items():
                if value == "":
                    enhanced_result[key] = None
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error validating parsing results: {e}")
            return self._enhanced_fallback_parsing(original_query)
    
    def _determine_query_type(self, parsed_result: Dict[str, Any]) -> str:
        """Determine query type from parsed results"""
        if parsed_result.get("employee_name"):
            return "person_lookup"
        elif parsed_result.get("required_skills"):
            return "skill_search"
        elif parsed_result.get("availability"):
            return "availability_search"
        elif parsed_result.get("project_domain"):
            return "project_search"
        else:
            return "general"