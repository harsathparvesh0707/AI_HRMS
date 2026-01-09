"""
LLM service for query processing using LangChain
"""
import logging
from typing import Tuple, List
import google.generativeai as genai
from config.settings import settings
from models.schemas import LLMResponse
import aiohttp, os, json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = "gemini-2.5-flash-lite"

    
    async def process_query(self, query: str) -> LLMResponse:
        """Process user query and return structured response"""
        try:
            if not query.strip():
                return self._fallback_response(query)
            
            # Create HR-aware prompt
            prompt = f"""
You are an HR assistant. Analyze this query and provide a brief response.

Query: {query}

Provide a helpful response about finding employees or HR information.
"""
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            chat_response = response.text if response.text else "Found employees matching your criteria"
            
            # Use fallback for structured data
            return self._fallback_response(query, chat_response)
            
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return self._fallback_response(query)
    
    def _parse_llm_output(self, response: str) -> Tuple[str, List[str], List[str], str, str]:
        """Parse LLM output (similar to original llm_integration.py)"""
        try:
            lines = [line.strip() for line in response.split("\n") if line.strip()]
            
            sql = ""
            fields = []
            ui_actions = []
            chat_response = ""
            search_strategy = "hybrid"
            in_sql_block = False
            
            for line in lines:
                # Handle markdown SQL blocks
                if line.startswith("```sql"):
                    in_sql_block = True
                    continue
                elif line.startswith("```") and in_sql_block:
                    in_sql_block = False
                    continue
                elif in_sql_block and line.upper().startswith("SELECT"):
                    sql = line.replace("`", "")
                    continue
                
                # Handle structured format
                if line.startswith("SQL:"):
                    sql = line.replace("SQL:", "").strip()
                    sql = sql.replace("`", "")
                    # Clean up malformed SQL with VectorDB references
                    if "OR VectorDB:" in sql:
                        sql = sql.split("OR VectorDB:")[0].strip()
                        if sql.endswith(";"):
                            sql = sql[:-1]  # Remove trailing semicolon
                        search_strategy = "vector_only"
                elif line.startswith("Fields:"):
                    fields_str = line.replace("Fields:", "").strip()
                    fields = [f.strip() for f in fields_str.split(",") if f.strip()]
                elif line.startswith("UI_actions:"):
                    actions_str = line.replace("UI_actions:", "").strip()
                    ui_actions = [a.strip() for a in actions_str.split(",") if a.strip()]
                elif line.startswith("Chat_response:"):
                    chat_response = line.replace("Chat_response:", "").strip()
                elif line.startswith("Search_strategy:"):
                    search_strategy = line.replace("Search_strategy:", "").strip()
            
            # Fallback values if parsing fails
            if not fields:
                fields = ["display_name", "employee_department", "deployment"]
            if not ui_actions:
                ui_actions = ["show_table"]
            if not chat_response:
                chat_response = "Found employees matching your criteria"
            if search_strategy not in ["sql_only", "vector_only", "hybrid"]:
                search_strategy = "hybrid"
            
            return sql, fields, ui_actions, chat_response, search_strategy
            
        except Exception as e:
            logger.error(f"Error parsing LLM output: {e}")
            return self._get_fallback_parsing(response)
    
    def _get_fallback_parsing(self, response: str) -> Tuple[str, List[str], List[str], str, str]:
        """Fallback parsing when structured parsing fails"""
        # Try to extract SQL from anywhere in the response
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        sql = ""
        
        for line in response.split("\n"):
            line = line.strip().replace("`", "")
            if any(keyword in line.upper() for keyword in sql_keywords):
                sql = line
                pass
                break
        
        return (
            sql,
            ["display_name", "employee_department", "deployment"],
            ["show_table"],
            "Processing your query",
            "hybrid"
        )
    
    def _determine_query_type(self, query: str) -> str:
        """Determine query type based on keywords"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['free pool', 'freepool']):
            return "free_pool"
        elif "billable" in query_lower:
            return "billable"
        elif any(kw in query_lower for kw in ['java', 'python', 'node', 'angular']):
            return "skills"
        else:
            return "general"
    
    def _fallback_response(self, query: str, chat_response: str = None) -> LLMResponse:
        """Generate fallback response using keyword analysis"""
        query_lower = query.lower()
        
        # Generate smart SQL based on keywords
        conditions = []
        
        # Availability conditions
        if any(kw in query_lower for kw in ['available', 'free pool', 'freepool', 'free', 'who are available']):
            conditions.append("(deployment ILIKE '%free%' OR deployment = 'Free')")
        elif "billable" in query_lower:
            conditions.append("deployment ILIKE '%billable%'")
        elif "budgeted" in query_lower:
            conditions.append("deployment ILIKE '%budgeted%'")
        
        # Skills conditions
        skills = []
        skill_keywords = ['node', 'angular', 'java', 'python', 'react', 'sql', 'javascript', 'spring']
        for skill in skill_keywords:
            if skill in query_lower:
                skills.append(f"skill_set ILIKE '%{skill}%'")
        
        if skills:
            conditions.append(f"({' AND '.join(skills)})")
        
        # Project-related filtering
        if any(kw in query_lower for kw in ['project', 'available', 'work']):
            conditions.append("employee_department NOT IN ('HR', 'Tools', 'Legal', 'Operations', 'Finance')")
            conditions.append("(designation ILIKE '%engineer%' OR designation ILIKE '%tech lead%' OR designation ILIKE '%trainee%')")
        
        # Build SQL
        base_sql = "SELECT e.*, ep.project_name, ep.customer FROM employees e LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id"
        
        if conditions:
            sql = base_sql + f" WHERE {' AND '.join(conditions)} ORDER BY e.designation LIMIT 20"
        else:
            sql = base_sql + " LIMIT 10"
        
        # Determine strategy
        has_deployment = any(kw in query_lower for kw in ['free pool', 'free', 'available', 'billable', 'budgeted'])
        has_skills = any(kw in query_lower for kw in skill_keywords)
        
        if has_deployment and has_skills:
            strategy = "hybrid"
        elif has_deployment:
            strategy = "sql_only"
        elif has_skills:
            strategy = "vector_only"
        else:
            strategy = "hybrid"
        
        return LLMResponse(
            sql=sql,
            fields=["display_name", "designation", "employee_department", "deployment"],
            ui_actions=["show_table"],
            chat_response=chat_response or "Found employees matching your criteria",
            confidence=0.8,
            query_type=self._determine_query_type(query),
            search_strategy=strategy
        )
    
    async def generate_response(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    text_headers = dict(resp.headers)
                    data = await resp.json()
                    logger.info(f"🧾 Gemini headers: {text_headers}")
                    
                    # Handle errors
                    if "error" in data:
                        logger.error(f"❌ Gemini API error: {data['error'].get('message')} (code {data['error'].get('code')})")
                        return f"ERROR: {data['error'].get('message')}"
                    
                    if "candidates" not in data:
                        logger.error(f"⚠️ Unexpected Gemini response: {json.dumps(data)[:500]}")
                        return "No valid response from Gemini."

                    text = data["candidates"][0]["content"]["parts"][0].get("text", "").strip()
                    return text or "No text generated."

        except Exception as e:
            logger.exception(f"Gemini async call failed: {e}")
            return f"ERROR: {e}"