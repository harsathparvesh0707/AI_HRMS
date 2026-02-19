"""
Simplified AI Ranking Service - Fast, effective prompt-based ranking
"""
import asyncio
import html
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class AIRankingService:
    """Fast AI-powered employee ranking with reasoning"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def rank_employees(self, query: str, parsed_query: Dict, compressed_employees: List[Dict], top_k: int = None) -> List[Dict[str, Any]]:
        """Single-pass AI ranking with detailed reasoning"""
        try:
            start_time = time.time()
            logger.info(f"🚀 Starting AI ranking for {len(compressed_employees)} employees")
            
            if not compressed_employees:
                return []
            
            # Rank ALL relevant employees (no pre-limiting)
            ranked_results = await self._single_pass_ai_ranking(
                query, parsed_query, compressed_employees, len(compressed_employees)
            )
            
            # Apply top_k only after ranking is complete
            if top_k:
                ranked_results = ranked_results[:top_k]
                logger.info(f"📊 Applied top_k filter: {len(ranked_results)} final results")
            
            processing_time = time.time() - start_time
            logger.info(f"✅ AI ranking complete: {len(ranked_results)} results in {processing_time:.2f}s")
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"AI ranking error: {e}")
            fallback_results = self._fallback_ranking(compressed_employees, len(compressed_employees))
            return fallback_results[:top_k] if top_k else fallback_results
    
    async def _single_pass_ai_ranking(self, query: str, parsed_query: Dict, employees: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """Single AI call that ranks and provides reasoning"""
        
        # Prepare employee profiles for ranking
        employee_profiles = []
        for i, emp in enumerate(employees):
            profile = f"{i+1}. {emp['compression']}"
            employee_profiles.append(profile)
        
        profiles_text = "\n".join(employee_profiles)
        
        # Enhanced ranking prompt - provide reasoning for ALL employees
        ranking_prompt = f"""
CONTEXT: This is for PROJECT ALIGNMENT - finding the best employees to assign to a new project requirement.

QUERY: "{query}"
QUERY TYPE: {parsed_query.get('query_type', 'general')}
REQUIRED SKILLS: {parsed_query.get('required_skills', [])}
PROJECT DOMAIN: {parsed_query.get('project_domain', 'any')}
AVAILABILITY NEEDED: {parsed_query.get('availability_required', 'any')}

PROFILE FORMAT: [ID]|tg:[TechGroup]|dep:[Deployment]|loc:[Location]|sk:[Skills]|pr:[Projects]|dom:[Domains]

CODES:
- TechGroup: BJ=Backend-Java, FA=Frontend-Angular, FR=Frontend-React, BP=Backend-Python, AN=Android
- Deployment: FP=Free(best), SH=Shadow(good), SP=Support(good), RD=RandD(medium), PL=Planned(medium), CB=ClientBackup(low), BB=BillableBackup(low), BU=Budgeted(low), BL=Billable(busy), CF=CustomerFacing(busy)
- Skills: ja=Java, sb=SpringBoot, ng=Angular, rt=React, py=Python, aw=AWS, sq=SQL, js=JavaScript

EMPLOYEE PROFILES:
{profiles_text}

TASK: Rank ALL {top_k} employees and provide reasoning for each one.

RANKING INSTRUCTIONS:
1. Check TechGroup match (Java→BJ preferred, Angular→FA/FR preferred)
2. Check skills in sk:[] array
3. Check deployment status (FP=best, CB/BB/BU=low, BL/CF=busy)
4. Rank by: TechGroup match > Deployment status > Skills match

IMPORTANT: Provide reasoning for ALL {top_k} employees, not just top few.

RETURN FORMAT:
RANK 1: Employee [Number] - [Reason with tg, dep, skills]
RANK 2: Employee [Number] - [Reason with tg, dep, skills]
...
RANK {top_k}: Employee [Number] - [Reason with tg, dep, skills]

Now rank ALL {top_k} employees:
        """
        
        # Get AI ranking with reasoning
        ai_response = await self.llm_service.generate_response(ranking_prompt)
        logger.info(f"🤖 AI Ranking Response:\n{ai_response}")
        logger.info(f"📋 Compressed profiles sent to AI ({len(profiles_text)} chars):\n{profiles_text[:300]}...")
        
        # Parse the ranked results with reasoning
        ranked_employees = self._parse_ranked_response(ai_response, employees, top_k)
        
        return ranked_employees
    
    def _parse_ranked_response(self, ai_response: str, employees: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """Parse AI response into ranked results with reasoning"""
        ranked_results = []
        
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('RANK '):
                try:
                    # Parse "RANK 1: Employee 3 - Reason here"
                    parts = line.split(':', 1)
                    if len(parts) < 2:
                        continue
                    
                    rank_text = parts[0].strip()  # "RANK 1"
                    rest = parts[1].strip()  # "Employee 3 - Reason here"
                    
                    # Extract rank number
                    rank_num = int(rank_text.split()[1].strip())
                    
                    # Extract employee number and reason
                    if 'Employee' in rest:
                        emp_part = rest.split('Employee')[1].strip()
                        # Handle both simple numbers (1, 2, 3) and employee IDs (12362, 12491)
                        emp_identifier = emp_part.split()[0].strip()
                        # Get everything after the first dash as reason
                        dash_parts = emp_part.split(' - ', 1)
                        if len(dash_parts) > 1:
                            reason = dash_parts[1].strip()
                            # Clean up any escape characters and formatting issues
                            reason = reason.replace('\"', '"').replace('\\', '').strip()
                        else:
                            reason = 'Good match for project requirements'
                        
                        # Try to find employee by ID or index
                        emp_idx = self._find_employee_index(emp_identifier, employees)
                        if emp_idx == -1:
                            logger.warning(f"Could not find employee with identifier: {emp_identifier}")
                            continue
                    else:
                        # Fallback parsing
                        numbers = [int(s) for s in rest.split() if s.isdigit()]
                        if numbers:
                            emp_identifier = str(numbers[0])
                            emp_idx = self._find_employee_index(emp_identifier, employees)
                            reason = ' '.join([s for s in rest.split() if not s.isdigit()])
                            if emp_idx == -1:
                                continue
                        else:
                            continue
                    
                    # Get employee data
                    if 0 <= emp_idx < len(employees):
                        employee_data = employees[emp_idx]['full_data'].copy()
                        
                        # Add ranking metadata
                        employee_data.update({
                            'ai_rank': rank_num,
                            'ranking_reason': reason,
                            'match_score_percentage': max(10, 100 - (rank_num * 10)),
                            'ai_confidence': self._calculate_confidence(rank_num, top_k)
                        })
                        
                        # Remove unnecessary fields including project-level fields that should only be in current_projects
                        fields_to_remove = [
                            'delivery_owner_emp_id', 'delivery_owner', 'joined_date', 'rm_id', 'rm_name', 
                            'sub_department', 'created_by_employee_id', 'created_by_display_name', 'created_at', 'updated_at',
                            'occupancy', 'project_name', 'customer', 'project_department', 'project_industry', 
                            'project_status', 'role', 'deployment'
                        ]
                        for field in fields_to_remove:
                            employee_data.pop(field, None)
                        
                        # Add current project details
                        employee_data['current_projects'] = self._get_employee_projects(employees[emp_idx]['full_data'].get('employee_id'))
                        
                        ranked_results.append(employee_data)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse ranking line: {line} - {e}")
                    continue
        
        # If AI parsing failed, use fallback
        if not ranked_results:
            fallback_results = self._fallback_ranking(employees, top_k)
            # Sort fallback results by ai_rank
            fallback_results.sort(key=lambda x: x['ai_rank'])
            return fallback_results
        
        # Ensure proper ordering by ai_rank (1, 2, 3, ...)
        ranked_results.sort(key=lambda x: x['ai_rank'])
        
        return ranked_results
    
    def _calculate_confidence(self, rank: int, total: int) -> float:
        """Calculate confidence score based on rank position"""
        # Higher rank = higher confidence
        return max(0.1, 1.0 - (rank / total))
    
    def _fallback_ranking(self, employees: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """Fallback ranking when AI fails"""
        logger.info("🔄 Using fallback keyword-based ranking")
        
        results = []
        for i, emp in enumerate(employees[:top_k]):
            employee_data = emp['full_data'].copy()
            employee_data.update({
                'ai_rank': i + 1,
                'ranking_reason': 'Fallback ranking based on profile relevance',
                'match_score_percentage': 50,
                'ai_confidence': 0.5
            })
            
            # Remove unnecessary fields including project-level fields that should only be in current_projects
            fields_to_remove = [
                'delivery_owner_emp_id', 'delivery_owner', 'joined_date', 'rm_id', 'rm_name', 
                'sub_department', 'created_by_employee_id', 'created_by_display_name', 'created_at', 'updated_at',
                'occupancy', 'project_name', 'customer', 'project_department', 'project_industry', 
                'project_status', 'role', 'deployment'
            ]
            for field in fields_to_remove:
                employee_data.pop(field, None)
            
            # Add current project details
            employee_data['current_projects'] = self._get_employee_projects(emp['full_data'].get('employee_id'))
            results.append(employee_data)
        
        return results
    
    def _calculate_match_score(self, employee_data: Dict, rank: int, total: int) -> int:
        """Calculate match score percentage based on rank and employee data"""
        try:
            compression = employee_data.get('compression', '').lower()
            full_data = employee_data.get('full_data', {})
            
            score = 0
            
            # Rank-based score (60%)
            rank_score = max(0, (total - rank + 1) / total) * 60
            score += rank_score
            
            # Tech group bonus (20%)
            tech_group = full_data.get('tech_group', '').lower()
            if 'java' in tech_group or 'backend' in tech_group:
                score += 20
            
            # Deployment status bonus (10%) - now from compression string
            if 'deploy:freepool' in compression:
                score += 10
            elif 'deploy:shadow' in compression or 'deploy:backup' in compression:
                score += 7
            elif 'deploy:budgeted' in compression:
                score += 5
            elif 'deploy:billable' in compression:
                score += 2
            
            return min(int(score), 100)
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return max(10, 100 - (rank * 10))  # Fallback based on rank
    
    def _get_employee_projects(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get current projects for employee with role and deployment details"""
        try:
            # Import here to avoid circular imports
            from ..repositories.project_repository import ProjectRepository
            
            project_repo = ProjectRepository()
            projects = project_repo.get_projects_by_employee(employee_id)
            
            # Filter and format current projects
            current_projects = []
            for project in projects:
                # Include all projects with their details
                project_info = {
                    'project_name': project.get('project_name'),
                    'customer': project.get('customer'),
                    'role': project.get('role'),
                    'deployment': project.get('deployment'),
                    'occupancy': project.get('occupancy', 0),
                    'project_industry': project.get('project_industry'),
                    'project_status': project.get('project_status')
                }
                current_projects.append(project_info)
            
            return current_projects
            
        except Exception as e:
            logger.error(f"Error getting employee projects: {e}")
            return []
    

    def _find_employee_index(self, identifier: str, employees: List[Dict]) -> int:
        """Find employee index by ID or sequential number"""
        try:
            # First try as 1-based sequential index
            seq_idx = int(identifier) - 1
            if 0 <= seq_idx < len(employees):
                return seq_idx
            
            # Then try to find by employee_id (handle numeric format)
            search_id = identifier
            
            for i, emp in enumerate(employees):
                emp_id = str(emp.get('full_data', {}).get('employee_id', ''))
                # Match against VVDN/3086 or 3086
                if emp_id == f"VVDN/{search_id}" or emp_id.replace('VVDN/', '') == search_id:
                    return i
            
            return -1  # Not found
            
        except (ValueError, TypeError):
            return -1
        

    
    async def llm_rank_employees(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    pre_ranked_employees: List[Dict[str, Any]],
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
        """
        Reasoning-based ranking using LLM — comparative and hierarchical.
        Input: pre-ranked employees with compression strings.
        Output: all employees with natural-language reasoning and AI score.
        """
        try:
            if not pre_ranked_employees:
                logger.warning("⚠️ No employees provided for LLM ranking.")
                return []

            # Limit list only if top_k specified
            employees = pre_ranked_employees[:top_k] if top_k else pre_ranked_employees

            # Build compact profile list
            profile_lines = [f"{i+1}. {e['compression']}" for i, e in enumerate(employees)]
            profiles_text = "\n".join(profile_lines)

            # Construct clear and compact HR ranking prompt
            prompt = f"""
    You are an HR evaluator ranking employees for a project requirement.

    PROJECT QUERY: "{query}"
    CONTEXT: {parsed_query.get('context', 'general')}
    REQUIRED SKILLS: {parsed_query.get('skills', [])}
    LOCATION PREFERENCE: {parsed_query.get('location', 'any')}

    You are given EMPLOYEE PROFILES in this format:
    <ID>|<RoleCode>|<DeptCode>|<Location>|<ExperienceYears>|<ProjectCount>|<DeploymentCode>|<KeySkills>

    Deployment priority (descending):
    Free > Backup > Shadow > R&D > Budgeted > Billable > CustomerFacing > Business/Marketing

    TASK:
    For each employee, assess how well they fit this project considering:
    - Skill match (technical relevance)
    - Experience (junior, mid, senior)
    - Availability (deployment)
    - Location match
    - Overall suitability for assignment

    Be descriptive, natural, and concise. Write like a professional HR reviewer giving a reasoned evaluation.

    OUTPUT STRICTLY AS JSON LIST:
    [
    {{
        "emp": "16117",
        "score": 92,
        "reason": "Excellent match — mid-level backend Java developer with 2.8 years total experience. Strong Spring Boot and Docker stack. Currently in MIX deployment (likely available soon)."
    }},
    {{
        "emp": "8177",
        "score": 74,
        "reason": "Solid 3+ years backend experience. Billable on current project but high technical fit for similar roles."
    }}
    ]
            """

            response = await self.llm_service.generate_response(prompt)
            logger.info(f"🤖 LLM Ranking Response (truncated): {response[:500]}")
            logger.info(f"🔍 Full LLM Response: {response}")

            import json, re, html
            # Clean and unescape HTML/Markdown
            clean_response = html.unescape(response.strip())

            # Extract JSON (even if embedded or truncated)
            json_match = re.search(r"\[.*\]", clean_response, re.DOTALL)
            json_str = json_match.group(0) if json_match else clean_response

            # Try parsing JSON, with repair fallback
            try:
                structured = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("⚠️ JSONDecodeError — attempting to repair JSON.")

            # Build final results, ensuring all employees appear
            final_ranked = []
            matched_ids = set()

            for item in structured:
                emp_id = str(item.get("emp", "")).replace("VVDN/", "")
                ai_score = float(item.get("score", 0))
                ai_reason = item.get("reason", "").strip()

                for e in employees:
                    if e["employee_id"].replace("VVDN/", "") == emp_id:
                        final_ranked.append({
                            **e,
                            "ai_score": round(ai_score, 1),
                            "ai_reason": ai_reason or "Strong alignment based on skill and deployment context."
                        })
                        matched_ids.add(emp_id)
                        break

            # Include any missing employees from pre-ranked list (if LLM skipped)
            missing = [e for e in employees if e["employee_id"].replace("VVDN/", "") not in matched_ids]
            if missing:
                logger.warning(f"⚠️ LLM returned {len(final_ranked)} / {len(employees)} employees. Filling {len(missing)} from pre-rank.")
                for e in missing:
                    final_ranked.append({
                        **e,
                        "ai_score": 60.0,
                        "ai_reason": "Not explicitly ranked by AI. Added from pre-ranked fallback."
                    })

            # Sort by descending AI score
            final_ranked.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

            logger.info(f"✅ LLM ranking complete for {len(final_ranked)} employees.")
            return final_ranked

        except Exception as e:
            logger.error(f"❌ LLM ranking failed: {e}")
            logger.debug(f"🔍 Exception details: {str(e)}")
            return pre_ranked_employees


    async def llm_progressive_rank(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
        """
        Full PDP ranking: hierarchical, reasoning-based, no elimination.
        Compares employees in small groups and assigns tiers progressively.
        """
        import json, math, html
        from itertools import islice

        if not employees:
            return []

        # Step 1: Split into groups of 5–8 for pairwise reasoning
        group_size = 5
        grouped = [employees[i:i+group_size] for i in range(0, len(employees), group_size)]

        all_results = []
        logger.info(f"🧩 Performing progressive reasoning on {len(employees)} employees across {len(grouped)} groups...")

        for g_idx, group in enumerate(grouped, start=1):
            # Build compact text
            profiles_text = "\n".join(
                f"{i+1}. {e['compression']}" for i, e in enumerate(group)
            )

            prompt = f"""
    You are an expert HR evaluator performing comparative ranking.

    PROJECT QUERY: "{query}"
    CONTEXT: {parsed_query.get('context', 'general')}
    REQUIRED SKILLS: {parsed_query.get('skills', [])}
    LOCATION: {parsed_query.get('location', 'any')}

    EMPLOYEES (compressed):
    Each line includes: employee_id|role|department|location|experience|active_project_count|availability_code
    Availability codes:
      FR = Free / Available,
      BIL = Billable / Client Project,
      RD = R&D / Internal,
      SH = Shadow / Learning,
      BU = Budgeted / Planned,
      BK = Backup / Support,
      MIX = Mixed / Multiple Roles.
    {profiles_text}

    TASK:
    Compare these employees **relatively**.
    Decide which ones are strongest fits for this project and which should be progressively demoted.

    RULES:
    - Do NOT remove anyone.
    - Tier 1 = Ideal match (skills, experience, availability, location)
    - Tier 2 = Good fit
    - Tier 3 = Partial fit
    - Tier 4 = Weak fit
    - Assign a numeric AI Score (0–100) indicating fit strength.
    - Give detailed natural HR-style reason for each, dont add compressed employee details & assumption.

    OUTPUT STRICT JSON:
    [
    {{"emp":"16117","score": 92,"reason":"Excellent backend Java match, 2.8y exp, likely available soon."}},
    {{"emp":"8177","score": 67,"reason":"Solid backend dev, but billable currently."}}
    ]
            """

            response = await self.llm_service.generate_response(prompt)
            logger.info(f"🤖 Group {g_idx}: LLM tier reasoning returned {len(response)} chars.")

            # Try to parse
            try:
                clean = html.unescape(response.strip())
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                structured = json.loads(clean)
                all_results.extend(structured)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse group {g_idx}: {e}")
                continue

        # Step 2: Merge back to employees
        final_ranked = []
        for e in employees:
            emp_id = e["employee_id"].replace("VVDN/", "")
            match = next((r for r in all_results if r.get("emp") == emp_id), None)
            if match:
                final_ranked.append({
                    **e,
                    "ai_score": float(match.get("score", 0)),
                    "ai_reason": match.get("reason", "").strip()
                })
            else:
                # fallback if missing
                final_ranked.append({
                    **e,
                    "ai_score": 0.0,
                    "ai_reason": "No reasoning available (fallback)"
                })

        # Step 3: Optional final consolidation pass (optional refinement)
        # This lets LLM reorder globally if needed
        final_prompt = f"""
    Now consolidate these results across all tiers for final ranking.
    Use tiers (Tier1→Tier4) and reasoning quality to produce ordered ranking.
    Return as JSON list with same keys.
        """
        summary_json = json.dumps(final_ranked[: min(len(final_ranked), 20)], indent=2)
        response = await self.llm_service.generate_response(final_prompt + summary_json)

        try:
            final_clean = html.unescape(response.strip())
            if "```json" in final_clean:
                final_clean = final_clean.split("```json")[1].split("```")[0].strip()
            consolidated = json.loads(final_clean)
            logger.info(f"✅ Final PDP reasoning ranking complete with {len(consolidated)} entries.")
            return consolidated
        except Exception:
            logger.warning("⚠️ Final consolidation parsing failed, using first stage results.")
            return final_ranked


    async def llm_progressive_rank_single(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
        """
        Fast global PDP reasoning — single LLM call for all employees.
        Full context, pure reasoning (no elimination), using percentage-based AI score.
        """
        import html, re, time, json

        if not employees:
            return []

        start_time = time.time()
        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running Single-Batch PDP reasoning for {len(employees)} employees...")

        prompt = f"""
You are an experienced HR evaluator ranking employees for project requirement & allocation.

PROJECT QUERY: "{query}"
CONTEXT: {parsed_query.get('context', 'general')}
REQUIRED SKILLS: {parsed_query.get('skills', [])}
LOCATION: {parsed_query.get('location', 'any')}

EMPLOYEES (compressed):
Each line includes:
employee_id|role|department|location|experience|active_project_count|availability_code|tech_group

Availability codes:
FR = Free / Available
BK = Backup / Support
RD = R&D / Internal
SH = Shadow / Learning
BU = Budgeted / Planned
BIL = Billable / Client Project
MIX = Mixed / Multiple Roles

TechGroup examples: Backend-Java, Backend-Python, Frontend-React, Frontend-Angular, CloudOps, Android, iOS, Flutter etc.


TASK:
Compare all employees **globally** for suitability for this project.

PRIORITY RULES (very important):
1. Strongly prefer employees whose **tech_group clearly matches** the project context or skills.
   - Example: if the project is backend Java, prefer "Backend-Java" tech group first, even if others are free.
   - If none match exactly, then consider related or general tech groups.
2. After tech group match, prioritize **availability**:
   Free (FR) > Backup (BK) > Support > R&D/Shadow > Budgeted/Billable.
3. Billable (BIL) and Budgeted (BU) employees get lower scores unless uniquely skilled.
4. Availability is more important than experience when tech_group and skill match are similar.
5. Prefer employees located near the project's location when other factors are similar.
6. Use natural HR reasoning — like a manager justifying choices in a meeting.

STYLE:
- Do NOT output JSON.
- For each employee, output one line:
  emp_id | score% | reasoning
- Score between 0 and 100.
- Human, HR-style tone:
  - Top candidates: up to 4 sentences.
  - Others: up to 2 sentences.
- Do NOT repeat compressed codes in reasons.

Reason examples:
- "Excellent backend Java developer with strong Spring Boot and SQL skills. Currently free and ready for immediate allocation."
- "Mid-level Java developer in backup role, suitable for new assignments."
- "Highly experienced engineer but currently billable, hence lower immediate availability."

EXAMPLE OUTPUT:
16117 | 92 | Excellent backend Java match, free and deployable.
8177 | 67 | Solid backend dev, but currently billable.
30433 | 84 | Junior but available with relevant Java skills.

EMPLOYEES:
{profiles_text}
"""


        # Send request to LLM
        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        # Parse output lines like: emp_id | score | reason
        results = []
        for line in clean.split("\n"):
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|", 2)]
            if len(parts) < 3:
                continue
            emp_id, score_str, reason = parts
            # Extract numeric score safely
            match = re.search(r"\d{1,3}", score_str)
            score = float(match.group()) if match else 0.0
            results.append({
                "emp": emp_id.replace("VVDN/", "").strip(),
                "score": min(max(score, 0), 100),
                "reason": reason.strip()
            })

        # Merge reasoning results back with employee data (keep same order)
        final_ranked = []
        for e in employees:
            emp_id = e["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r.get("emp") == emp_id), None)
            final_ranked.append({
                **e,
                "ai_score": float(match["score"]) if match else 0.0,
                "ai_reason": match["reason"] if match else "No reasoning available"
            })

        total_time = time.time() - start_time
        logger.info(f"✅ Single-batch reasoning complete in {total_time:.2f}s for {len(employees)} employees")
        return final_ranked


    async def llm_progressive_rank_single_with_criteria(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
        """
        Single-batch PDP reasoning with multi-criteria evaluation (Skill, TechGroup, Availability, Experience, Location).
        Produces human-like reasoning and interpretable component scores.
        """
        import html, re, time, json

        if not employees:
            return []

        start_time = time.time()
        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running Single-Batch PDP reasoning for {len(employees)} employees...")

        prompt = f"""
    You are an experienced HR evaluator ranking employees for project requirement & allocation.

    PROJECT QUERY: "{query}"
    CONTEXT: {parsed_query.get('context', 'general')}
    REQUIRED SKILLS: {parsed_query.get('skills', [])}
    LOCATION: {parsed_query.get('location', 'any')}

    EMPLOYEES (compressed):
    Each line includes:
    employee_id|role|department|location|experience|active_project_count|availability_code|tech_group

    Availability codes (for your internal reasoning only — do NOT include these raw codes in explanations):
    FR = Free / Available
    BK = Backup / Support
    RD = R&D / Internal
    SH = Shadow / Learning
    BU = Budgeted / Planned
    BIL = Billable / Client Project
    MIX = Mixed / Multiple Roles

    TechGroup examples (for your internal reasoning only):
    - "Backend-Java" → Backend developer specialized in Java/Spring Boot.
    - "Backend-Python" → Backend developer using Python/Django/Flask.
    - "Frontend-React" → Frontend web developer skilled in ReactJS.
    - "Frontend-Angular" → Frontend web developer skilled in Angular.
    - "CloudOps" → Cloud or DevOps specialist (AWS, GCP, Azure, Kubernetes).
    - "Android" / "iOS" → Mobile app developers.
    - "AI-ML" → Data or ML engineer.
    When writing reasoning, always describe roles and availability naturally.
    ✅ Example: say “fully available” instead of “FR”, and “budgeted” or “on a client project” instead of “BIL”.
    ✅ Never show tech group labels literally; instead describe them (e.g., “Java backend developer”, “React engineer”).


    TASK:
    Compare all employees **globally** for suitability for this project.

    For each employee, evaluate them on these 5 fixed criteria (0-100 each):
    1. Skill Match — how relevant are their skills to project needs.
    2. Tech Group Fit — how well their tech_group aligns with project context.
    3. Availability — based on deployment code (FR highest, then BK, SH, RD, BU, BIL).
    4. Experience Level — whether their experience matches expected project complexity.
    5. Location Fit — proximity to desired location or timezone.

    Then give an **Overall Suitability %** (0-100) as a human judgment considering all of the above (not a strict average).

    PRIORITY RULES (very important):
    1. Strongly prefer employees whose **tech_group clearly matches** the project context or skills.
    - Example: if the project is backend Java, prefer "Backend-Java" tech group first, even if others are free.
    - If none match exactly, then consider related or general tech groups.
    2. After tech group match, prioritize **availability**:
    Free (FR) > Backup (BK) > Support > R&D/Shadow > Budgeted/Billable.
    3. Billable (BIL) and Budgeted (BU) employees get lower scores unless uniquely skilled.
    4. Availability is more important than experience when tech_group and skill match are similar.
    5. Prefer employees located near the project's location when other factors are similar.
    6. Use natural HR reasoning — like a manager justifying choices in a meeting.

    OUTPUT FORMAT (strictly this format):
    emp_id | OverallScore | [Skill XX, TechGroup XX, Availability XX, Experience XX, Location XX] | reasoning

    EXAMPLE OUTPUT:
    16117 | 92 | [Skill 95, TechGroup 90, Availability 85, Experience 70, Location 80] | Excellent backend Java developer with strong Spring Boot and SQL skills, currently free and ready for allocation.
    8177 | 67 | [Skill 80, TechGroup 70, Availability 55, Experience 85, Location 65] | Experienced developer but currently billable, hence limited availability.
    30433 | 84 | [Skill 88, TechGroup 85, Availability 90, Experience 60, Location 75] | Junior but available with good Java fundamentals.

    EMPLOYEES:
    {profiles_text}
    """

        # Send request to LLM
        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        results = []
        line_pattern = re.compile(
            r"^(\d+)\s*\|\s*(\d{1,3})\s*\|\s*\[([^\]]+)\]\s*\|\s*(.+)$"
        )

        for line in clean.split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            match = line_pattern.match(line)
            if not match:
                continue

            emp_id, overall_str, criteria_str, reason = match.groups()

            # Parse sub-criteria like "Skill 95, TechGroup 90, ..."
            criteria = {}
            for part in criteria_str.split(","):
                seg = part.strip().split()
                if len(seg) == 2:
                    key, val = seg
                    try:
                        criteria[key] = float(val)
                    except ValueError:
                        pass

            results.append({
                "emp": emp_id.replace("VVDN/", "").strip(),
                "overall": float(overall_str),
                "criteria": criteria,
                "reason": reason.strip()
            })

        # Merge reasoning results with employee data
        final_ranked = []
        for e in employees:
            emp_id = e["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r.get("emp") == emp_id), None)
            final_ranked.append({
                **e,
                "ai_score": float(match["overall"]) if match else 0.0,
                "ai_reason": match["reason"] if match else "No reasoning available",
                "ai_criteria": match["criteria"] if match else {}
            })

        total_time = time.time() - start_time
        logger.info(f"✅ Single-batch reasoning with criteria complete in {total_time:.2f}s for {len(employees)} employees")
        return final_ranked




    async def llm_progressive_rank_single_with_criteria_fix(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
        """
        Single-batch PDP reasoning with multi-criteria evaluation (Skill, TechGroup, Availability, Experience, Location).
        Produces human-like reasoning and interpretable component scores.
        """
        import html, re, time, json

        if not employees:
            return []

        start_time = time.time()
        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running Single-Batch PDP reasoning for {len(employees)} employees...")

        prompt = f"""
    You are an experienced HR evaluator ranking employees for project requirement & allocation.

    PROJECT QUERY: "{query}"
    CONTEXT: {parsed_query.get('context', 'general')}
    REQUIRED SKILLS: {parsed_query.get('skills', [])}
    LOCATION: {parsed_query.get('location', 'any')}

    EMPLOYEES (compressed):
    Each line includes:
    employee_id|role|department|location|experience|active_project_count|availability_code|tech_group

    Availability codes (for your internal reasoning only — do NOT include these raw codes in explanations):
    FR = Free / Available
    BK = Backup / Support
    RD = R&D / Internal
    SH = Shadow / Learning
    BU = Budgeted / Planned
    BIL = Billable / Client Project
    MIX = Mixed / Multiple Roles

    TechGroup examples (for your internal reasoning only):
    - "Backend-Java" → Backend developer specialized in Java/Spring Boot.
    - "Backend-Python" → Backend developer using Python/Django/Flask.
    - "Frontend-React" → Frontend web developer skilled in ReactJS.
    - "Frontend-Angular" → Frontend web developer skilled in Angular.
    - "CloudOps" → Cloud or DevOps specialist (AWS, GCP, Azure, Kubernetes).
    - "Android" / "iOS" → Mobile app developers.
    - "AI-ML" → Data or ML engineer.
    When writing reasoning, always describe roles and availability naturally.
    ✅ Example: say “fully available” instead of “FR”, and “budgeted” or “on a client project” instead of “BIL”.
    ✅ Never show tech group labels literally; instead describe them (e.g., “Java backend developer”, “React engineer”).


    TASK:
    Compare all employees **globally** for suitability for this project.

    For each employee, evaluate them on these 5 fixed criteria (0-100 each):
    1. Skill Match — how relevant are their skills to project needs.
    2. Tech Group Fit — how well their tech_group aligns with project context.
    3. Availability — based on deployment code (FR highest, then BK, SH, RD, BU, BIL).
    4. Experience Level — whether their experience matches expected project complexity.
    5. Location Fit — proximity to desired location or timezone.

    Then give an **Overall Suitability %** (0-100) as a human judgment considering all of the above (not a strict average).

    PRIORITY RULES (very important):
    1. Strongly prefer employees whose **tech_group clearly matches** the project context or skills.
    - Example: if the project is backend Java, prefer "Backend-Java" tech group first, even if others are free.
    - If none match exactly, then consider related or general tech groups.
    2. After tech group match, prioritize **availability**:
    Free (FR) > Backup (BK) > Support > R&D/Shadow > Budgeted/Billable.
    3. Billable (BIL) and Budgeted (BU) employees get lower scores unless uniquely skilled.
    4. Availability is more important than experience when tech_group and skill match are similar.
    5. Prefer employees located near the project's location when other factors are similar.
    6. Use natural HR reasoning — like a manager justifying choices in a meeting.

    OUTPUT FORMAT (strictly this format):
    emp_id | OverallScore | [Skill XX, TechGroup XX, Availability XX, Experience XX, Location XX] | reasoning

    EXAMPLE OUTPUT:
    16117 | 92 | [Skill 95, TechGroup 90, Availability 85, Experience 70, Location 80] | Excellent backend Java developer with strong Spring Boot and SQL skills, currently free and ready for allocation.
    8177 | 67 | [Skill 80, TechGroup 70, Availability 55, Experience 85, Location 65] | Experienced developer but currently billable, hence limited availability.
    30433 | 84 | [Skill 88, TechGroup 85, Availability 90, Experience 60, Location 75] | Junior but available with good Java fundamentals.

    EMPLOYEES:
    {profiles_text}
    """

        # Send request to LLM
        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        # Parse output lines like: emp_id | score | criteria | reason
        results = []
        for line in clean.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue

            # Extract emp_id, score, and the rest flexibly
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue

            # Handle ID — allow "VVDN/30433", "30433", "#30433", etc.
            emp_raw = re.sub(r'[^A-Za-z0-9/]', '', parts[0])
            emp_id = emp_raw.replace("VVDN", "").replace("/", "").strip()

            # Score extraction
            score_match = re.search(r"\d{1,3}", parts[1])
            score = float(score_match.group()) if score_match else 0.0

            # Extract optional criteria
            criteria_text = ""
            reason_text = ""
            if len(parts) >= 4:
                criteria_text = parts[2].strip()
                reason_text = parts[3].strip()
            else:
                # handle [criteria] embedded in 3rd part
                if "[" in parts[2]:
                    criteria_text = re.search(r"\[(.*?)\]", parts[2])
                    criteria_text = criteria_text.group(1) if criteria_text else ""
                    reason_text = re.sub(r"\[.*?\]", "", parts[2]).strip()
                else:
                    reason_text = parts[2].strip()

            # Parse criteria if present
            ai_criteria = {}
            if criteria_text:
                for crit in ["Skill", "TechGroup", "Availability", "Experience", "Location"]:
                    match = re.search(fr"{crit}\s*(\d+)", criteria_text, re.I)
                    if match:
                        ai_criteria[crit] = float(match.group(1))

            results.append({
                "emp": emp_id,
                "score": min(max(score, 0), 100),
                "reason": reason_text,
                "ai_criteria": ai_criteria
            })


        # Merge reasoning results with employee data
        final_ranked = []
        for e in employees:
            emp_id = e["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r.get("emp") == emp_id), None)
            final_ranked.append({
                **e,
                "ai_score": float(match["score"]) if match else 0.0,
                "ai_reason": match["reason"] if match else "No reasoning available",
                "ai_criteria": match["ai_criteria"] if match else {}
            })


        total_time = time.time() - start_time
        logger.info(f"✅ Single-batch reasoning with criteria complete in {total_time:.2f}s for {len(employees)} employees")
        return final_ranked



    async def llm_progressive_rank_parallel(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:
        """
        Parallel PDP reasoning — splits employees into groups and runs LLM in parallel.
        Suitable for large batches (100–500 employees). Includes global merge.
        """
        if not employees:
            return []

        import asyncio

        group_size = 6
        grouped = [employees[i:i+group_size] for i in range(0, len(employees), group_size)]
        logger.info(f"🧩 Parallel PDP reasoning: {len(grouped)} groups of {group_size}")
        semaphore = asyncio.Semaphore(3)

        async def _rank_group(g_idx: int, group: List[Dict[str, Any]]):
            async with semaphore:
                start = time.time()
                profiles_text = "\n".join(f"{i+1}. {e['compression']}" for i, e in enumerate(group))
                logger.info(f"🚀 Starting group {g_idx} ({len(group)} employees)")            
                prompt = f"""
        You are an expert HR evaluator performing comparative ranking.

        PROJECT QUERY: "{query}"
        CONTEXT: {parsed_query.get('context', 'general')}
        REQUIRED SKILLS: {parsed_query.get('skills', [])}
        LOCATION: {parsed_query.get('location', 'any')}

        EMPLOYEES (compressed):
        Each line includes: employee_id|role|department|location|experience|active_project_count|availability_code
        Availability codes:
        FR = Free / Available,
        BIL = Billable / Client Project,
        RD = R&D / Internal,
        SH = Shadow / Learning,
        BU = Budgeted / Planned,
        BK = Backup / Support,
        MIX = Mixed / Multiple Roles.
        {profiles_text}

        TASK:
        Compare these employees **relatively** within this group.
        Assign numeric AI Score (0–100) and clear HR-style reasoning (no compressed data).

        OUTPUT STRICT JSON:
        [
        {{"emp":"16117","score":92,"reason":"Excellent backend Java match, 2.8y exp, likely available soon."}}
        ]
                """
                response = await self.llm_service.generate_response(prompt)
                duration = time.time() - start
                logger.info(f"✅ Group {g_idx} finished in {duration:.2f}s")

                # If your LLMService returns HTTP headers, print them here:
                if isinstance(response, dict) and 'headers' in response:
                    headers = response['headers']
                    logger.info(f"🧾 Group {g_idx} headers: {headers.get('x-processing-ms')}ms, rate={headers.get('x-ratelimit-remaining')}")

                # Continue JSON parsing
                try:
                    clean = html.unescape(response.strip() if isinstance(response, str) else str(response))
                    if "```json" in clean:
                        clean = clean.split("```json")[1].split("```")[0].strip()
                    return json.loads(clean)
                except Exception as e:
                    logger.warning(f"⚠️ Parse failed for group {g_idx}: {e}")
                    return []

        # Run groups concurrently
        group_tasks = [_rank_group(i, g) for i, g in enumerate(grouped, 1)]
        group_results = await asyncio.gather(*group_tasks)
        all_results = [r for group in group_results for r in group]

        # --- Final consolidation for global consistency ---
        final_prompt = """
    Now consolidate these per-group results into a **single global ranking**.
    Use score and reasoning quality to sort employees.
    Return as JSON with the same keys: emp, score, reason.
    """
        summary_json = json.dumps(all_results, indent=2)
        response = await self.llm_service.generate_response(final_prompt + summary_json)

        try:
            clean = html.unescape(response.strip())
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            consolidated = json.loads(clean)
        except Exception as e:
            logger.warning(f"⚠️ Global merge parse failed: {e}")
            consolidated = all_results

        # Merge with full employee details
        final_ranked = []
        for e in employees:
            emp_id = e["employee_id"].replace("VVDN/", "")
            match = next((r for r in consolidated if r.get("emp") == emp_id), None)
            final_ranked.append({
                **e,
                "ai_score": float(match.get("score", 0)) if match else 0.0,
                "ai_reason": match.get("reason", "No reasoning available") if match else "No reasoning available"
            })
        return final_ranked

    async def llm_progressive_rank_single_with_criteria_simplified(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:

        import html, re, time

        if not employees:
            return []

        start_time = time.time()

        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running PURE PDP reasoning for {len(employees)} employees...")

      
        prompt = f"""
    You are an experienced HR evaluator performing PURE reasoning-based ranking using a PDP (Preference–Demotion–Promotion) method.

    Your task has TWO steps:

    ---------------------------------------
    STEP 1 — Assign TIER using PURE reasoning
    ---------------------------------------
    Tiers:
    1 = Strong Match
    2 = Good Match
    3 = Partial Match
    4 = Weak Match

    PRIORITY RULES:

    1. Tech-group match is the strongest factor.
    - ALWAYS use the exact tech_group from employee compression line.
    - NEVER rename, infer, shorten, or hallucinate tech groups.
    - NEVER output fake groups like “CAMA tech group” or “Backend - Java”.

    2. Availability codes (never reveal codes, only meaning):
    FR  = fully available
    BK  = available with some support duties
    SH  = shadow/learning
    RD  = R&D assignment
    BU  = budgeted
    BIL = on a client project
    MIX = multiple responsibilities

    3. Ranking order:
    - fully available > shadow/R&D > budgeted > client project.
    - Free (FR) > Backup (BK) > Support > R&D/Shadow > Budgeted > Billable.
    - Billable (BIL) and Budgeted (BU) employees get lower scores unless uniquely skilled.
    - Availability is more important than experience when tech_group and skill match are similar.

    4. Skills:
    direct match = strong
    related = medium
    unrelated = weak

    5. Experience helps but does NOT override tech-group or availability.

    6. Reasoning MUST be exactly 2 sentences, natural, HR-style and Human readable.
      - Generate diverse expressions, not repetitive templates.  
      - You may vary tone slightly (e.g., “strong fit”, “well aligned”, “solid match”, “brings good capability”).  
      - Use different justification styles such as:
            - skill alignment  
            - tech-group relevance  
            - availability readiness  
            - experience depth  
            - recent project suitability  
            - learning potential when junior  

      - DO NOT mention any scores, tier labels, availability codes, or compression fields.  
      - Keep the reasoning factual, concise, and human-like.

    ---------------------------------------
    STEP 2 — Evaluation Scores (NOT used for ranking)
    ---------------------------------------
    Return for each employee:
    Skill XX
    TechGroup XX
    Availability XX
    Experience XX
    Location XX
    OverallScore XX

    ---------------------------------------
    OUTPUT FORMAT (STRICT)
    ---------------------------------------
    emp_id | TIER <1-4> | OverallScore XX | [Skill XX, TechGroup XX, Availability XX, Experience XX, Location XX] | <2-sentence HR style reasoning>

    No extra text.

    ---------------------------------------
    PROJECT QUERY:
    "{query}"

    CONTEXT: {parsed_query.get('context', 'general')}
    SKILLS NEEDED: {parsed_query.get('skills', [])}
    LOCATION PREFERENCE: {parsed_query.get('location', 'any')}

    ---------------------------------------
    COMPRESSION FORMAT (IMPORTANT):
    id|role_code|tech_group|location_code|experience_years|non_free_project_count|department_code|availability_code|skills

    Example:
    30443|ES|Frontend - Angular|KO|1.1|1|CAMA|SH|react,angular


    ---------------------------------------
    EMPLOYEES:
    {profiles_text}
    """

        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        results = []

        for raw_line in clean.splitlines():
            line = raw_line.strip()
            if "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue

            emp_raw = re.sub(r"[^A-Za-z0-9/]", "", parts[0])
            emp_id = emp_raw.replace("VVDN", "").replace("/", "").strip()
            if not emp_id.isdigit():
                continue

            tier_match = re.search(r"TIER\s*(\d+)", parts[1], re.I)
            tier = int(tier_match.group(1)) if tier_match else 4

            score_match = re.search(r"(\d+)", parts[2])
            overall_score = float(score_match.group(1)) if score_match else 0.0

            criteria_block = parts[3]
            ai_criteria = {}
            for crit in ["Skill", "TechGroup", "Availability", "Experience", "Location"]:
                m = re.search(fr"{crit}\s*(\d+)", criteria_block, re.I)
                ai_criteria[crit] = float(m.group(1)) if m else 0.0

            reason_text = parts[4] if len(parts) > 4 else ""
            reason_text = reason_text.replace("\n", " ").strip()

            if len(reason_text.split(".")) < 2:
                reason_text += " Additional context required."

            results.append({
                "emp": emp_id,
                "tier": tier,
                "score": overall_score,
                "reason": reason_text,
                "ai_criteria": ai_criteria,
            })

        final_ranked = []

        for emp in employees:
            emp_id = emp["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r["emp"] == emp_id), None)

            if match:
                final_ranked.append({
                    **emp,
                    "ai_tier": match["tier"],
                    "ai_score": match["score"],
                    "ai_reason": match["reason"],
                    "ai_criteria": match["ai_criteria"],
                })
            else:
                final_ranked.append({
                    **emp,
                    "ai_tier": 4,
                    "ai_score": 0.0,
                    "ai_reason": "No reasoning available from AI.",
                    "ai_criteria": {crit: 0 for crit in ["Skill","TechGroup","Availability","Experience","Location"]},
                })

        final_ranked.sort(key=lambda x: x["ai_tier"])

        logger.info(f"🏁 Ranking completed in {time.time() - start_time:.2f}s")
        return final_ranked



    async def llm_progressive_rank_single_with_criteria_simplified_fix(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:

        import html, re, time

        if not employees:
            return []

        start_time = time.time()

        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running PURE PDP reasoning for {len(employees)} employees...")

        # -------------------------------------------------------------------------
        # STRICT PROMPT
        # -------------------------------------------------------------------------
        prompt = f"""
    You are an expert HR evaluator performing PURE reasoning-style ranking using a STRICT PDP
    (Preference–Demotion–Promotion) framework.

    You must produce TWO things per employee:
    1) A TIER (1–4)
    2) A concise 2-sentence HR reasoning

    The reasoning MUST be:
        • fully grounded ONLY in the compact record
        • fact-based, no hallucination
        • explicitly explain why the employee is promoted or demoted
        • mention tech-group match or mismatch
        • explain detected hybrid/full-stack/mobile multi-platform capability when present
        • mention internal vs external project context
        • mention occupancy / project load and availability category IN WORDS (not codes)
        • mention senior-role override (Lead/Principal/Architect) if applied

    IMPORTANT RESTRICTIONS FOR REASONING:
        • NEVER mention raw internal codes like "FR", "BK", "SH", "RD", "BU", "BIL", "CRD", "IN".
        • NEVER mention raw DEP_DETAIL strings or customer tokens like "EXTREMENETWORKS",
        "NORDENRESEARCHANDINN", "VVDNINTERNALPROJECT" etc.
        • If you need to refer to them, use ONLY generic phrases such as:
            - "internal company project"
            - "external client project"
            - "fully occupied on a client project"
            - "partially allocated to internal work"
        • NEVER guess full expanded customer names from compressed tokens.

    ------------------------------------------------------------------------------------
    COMPACT FORMAT (USE THIS STRUCTURE)
    ------------------------------------------------------------------------------------
    id|role_code|tech_group|location|experience_years|project_count|department|
    DEP_SUMMARY|DEP_DETAIL|skills

    Example internal:
    16117|ES|Frontend - Angular|KO|2.8|2|CAMA|IN|IN:100:VVDNINTERNALPROJECT|angular,typescript,java

    Example external:
    19220|ES|Frontend - Angular|NO|7.3|1|CMAP|BIL|BIL:100:EXTREMENETWORKS|angular,javascript

    DEP_DETAIL always contains entries in the form:
        CODE:OCCUPANCY:CUSTOMER
    Internal project if CUSTOMER contains “VVDN” or “INTERNAL”.

    ------------------------------------------------------------------------------------
    HYBRID / FULL-STACK / MULTI-PLATFORM CAPABILITY
    ------------------------------------------------------------------------------------
    Tech-group alone may not represent capability. Use skills to detect:

    • FULL-STACK (Frontend + Backend skills together)
        e.g., angular + java, react + node, react + spring boot, angular + spring boot, react + java.

    • HYBRID MOBILE
        e.g., flutter + android, flutter + ios, android + ios.

    • BACKEND-CLOUD HYBRID
        e.g., java/python + cloud/devops skills.

    If such hybrid capability satisfies the PROJECT QUERY domain:
        → treat employee as matching the domain even if tech_group differs.
        → mention explicitly in reasoning (e.g., “brings full-stack frontend + backend capability”).
    Hybrid uplift NEVER bypasses demotion rules.

    ------------------------------------------------------------------------------------
    TECH-GROUP OVERRIDE (PRIMARY FILTER)
    ------------------------------------------------------------------------------------
    If neither tech_group nor skills (including hybrid/full-stack inference) match the technical intent
    of the PROJECT QUERY:
        → MUST be Tier 3 or 4
        → NEVER Tier 1 or 2

    If skills DO match the query domain (even with a different tech_group):
        → treat as matching domain for Tier 1/2 eligibility (subject to demotion rules).

    ------------------------------------------------------------------------------------
    DEMOTION RULES (AFTER TECH-GROUP FILTER)
    ------------------------------------------------------------------------------------
    A) INTERNAL PROJECT OVERRIDE (highest priority)
    If ANY DEP_DETAIL entry has CUSTOMER containing “VVDN” or “INTERNAL”:
        → Employee is treated like working on internal company work.
        → Allowed tiers = {{1, 2}}
        → Occupancy decides within {{1,2}}:
            0–50 total internal occupancy → Tier 1
            >50–100 internal occupancy   → Tier 2

    You must mention in reasoning that they are on an internal company project
    and whether they are fully or partially occupied on it.

    B) EXTERNAL PROJECT DEMOTION (all non-internal customers)
    From DEP_DETAIL, identify:
        worst_category = lowest availability code (by severity)
        worst_occupancy = highest occupancy among all external entries.

    Availability codes order (best → worst):
        IN (internal)
        FR
        BK
        SH
        RD
        BU
        BIL
        CRD (Client)

    Allowed tiers based on worst_category (without senior override):
        FR, BK, SH            → allowed tiers {{1, 2}}
        RD, BU                → allowed tiers {{2, 3}}
        BIL, Client, CRD      → allowed tiers {{3, 4}}

    ADDITIONAL EXTERNAL EXPERIENCE RULE:
        For employees whose worst_category is BU or BIL/Client with high occupancy (≥80%) on external work:
            • If experience_years < 5 AND role is NOT a senior role (no Lead/Principal/Architect),
            then maximum allowed tier is 3 (they CANNOT be Tier 2).
            • Mention explicitly in reasoning that they are heavily loaded on external client work
            and have less than 5 years of experience, limiting them to a lower tier.

    C) SENIOR ROLE OVERRIDE
    If role_code indicates a senior role (Lead, Principal, Architect) AND
    worst_category is external (BIL/Client):
        → allowed tiers become {{2, 3}}
        → if worst_occupancy < 100 → prefer Tier 2
    You must mention seniority in the reasoning when this override is applied.

    No skill or experience may escape the allowed tier band after these rules.

    ------------------------------------------------------------------------------------
    PROMOTION RULES (within allowed band)
    ------------------------------------------------------------------------------------
    Inside the allowed band:

        Strong skill match (direct match with query domain and key skills) → top of band
        Medium skill match (related skills)                               → middle of band
        Weak alignment                                                    → bottom of band

    Tie-breakers in order:
        1. Lower total occupancy (more available)
        2. Internal projects over external projects
        3. Higher experience
        4. Hybrid/full-stack advantage when relevant to the query

    ------------------------------------------------------------------------------------
    STEP 2 — SCORES (NOT used for ranking)
    ------------------------------------------------------------------------------------
    You must output ALL of the following numeric values (0–100):
        Skill XX
        TechGroup XX
        Availability XX
        Experience XX
        OverallScore XX

    You MUST always output a number for each criterion.
    Never omit the criteria block, never leave any criterion blank.

    Availability scoring (conceptual guide):
        Base:
            IN=95, FR=95, BK=85, SH=80, RD=70, BU=60, BIL=40, CRD=30
        Penalty by worst_occupancy:
            0–20  → +10
            20–50 → 0
            50–80 → –10
            80–99 → –20
            100   → –30

    Cap final availability between 0 and 95.

    OverallScore MUST strictly follow tier band:
        Tier 1 → 80–100
        Tier 2 → 41–79
        Tier 3 → 20-40
        Tier 4 → 0–19

    Ensure OverallScore is consistent with the reasoning:
        • external, fully loaded juniors with <5 years and heavy client work
        should have clearly lower scores (Tier 3 or 4 band),
        • strong internal or highly suitable matches should sit in Tier 1 or high Tier 2 bands.

    ------------------------------------------------------------------------------------
    STRICT OUTPUT FORMAT (CRITICAL)
    ------------------------------------------------------------------------------------
    You MUST output EXACTLY one line per employee in this form:

    emp_id | TIER <1–4> | OverallScore XX |
    [Skill XX, TechGroup XX, Availability XX, Experience XX] |
    <exactly 2 concise sentences HR reasoning>

    Rules:
        • The criteria block MUST be inside square brackets and list ALL four dimensions.
        • The reasoning MUST be exactly 2 sentences.
        • Do NOT add any extra lines or commentary.

    ------------------------------------------------------------------------------------
    PROJECT QUERY:
    \"{query}\"

    CONTEXT: {parsed_query.get('context','general')}
    SKILLS NEEDED: {parsed_query.get('skills',[])}
    LOCATION PREFERENCE: {parsed_query.get('location','any')}

    ------------------------------------------------------------------------------------
    EMPLOYEES:
    {profiles_text}
    """

        # -------------------------------------------------------------------------
        # LLM CALL
        # -------------------------------------------------------------------------
        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        results = []

        for raw_line in clean.splitlines():
            line = raw_line.strip()
            if "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue

            emp_raw = re.sub(r"[^A-Za-z0-9/]", "", parts[0])
            emp_id = emp_raw.replace("VVDN", "").replace("/", "").strip()
            if not emp_id.isdigit():
                continue

            tier_match = re.search(r"TIER\s*(\d+)", parts[1], re.I)
            tier = int(tier_match.group(1)) if tier_match else 4

            score_match = re.search(r"(\d+)", parts[2])
            overall_score = float(score_match.group(1)) if score_match else 0.0

            criteria_block = parts[3]
            ai_criteria = {}
            for crit in ["Skill", "TechGroup", "Availability", "Experience"]:
                m = re.search(fr"{crit}[:=\s]*([0-9]+\.?[0-9]*)", criteria_block, re.I)
                ai_criteria[crit] = float(m.group(1)) if m else 0.0

            reason_text = parts[4] if len(parts) > 4 else ""
            reason_text = reason_text.replace("\n", " ").strip()

            # Do NOT auto-append any generic text; keep model's reasoning as-is.
            results.append({
                "emp": emp_id,
                "tier": tier,
                "score": overall_score,
                "reason": reason_text,
                "ai_criteria": ai_criteria,
            })

        # -------------------------------------------------------------------------
        # MERGE RESULTS BACK INTO EMPLOYEES
        # -------------------------------------------------------------------------
        final_ranked = []

        for emp in employees:
            emp_id = emp["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r["emp"] == emp_id), None)

            if match:
                final_ranked.append({
                    **emp,
                    "ai_tier": match["tier"],
                    "ai_score": match["score"],
                    "ai_reason": match["reason"],
                    "ai_criteria": match["ai_criteria"],
                })
            else:
                final_ranked.append({
                    **emp,
                    "ai_tier": 4,
                    "ai_score": 0.0,
                    "ai_reason": "No reasoning available from AI.",
                    "ai_criteria": {crit: 0 for crit in ["Skill", "TechGroup", "Availability", "Experience", "Location"]},
                })

        final_ranked.sort(key=lambda x: x["ai_tier"])

        logger.info(f"🏁 Ranking completed in {time.time() - start_time:.2f}s")
        return final_ranked


    def _parse_compact_for_prerank(self, compact: str):
        """
        Strict parsing of compact format used only for pre-rank.
        Correctly identifies INTERNAL only from CUSTOMER token.
        """
        try:
            parts = compact.split("|")
            if len(parts) < 10:
                return None

            emp_id = parts[0]
            tech_group = parts[2]
            exp_years = float(parts[4])
            project_count = int(parts[5])

            skills = [s.strip().lower() for s in parts[9].split(",") if s.strip()]

            # Parse DEP_DETAIL
            raw_details = parts[8]
            detail_list = []

            for entry in raw_details.split(","):
                entry = entry.strip()
                if not entry or ":" not in entry:
                    continue

                code, occ, customer = entry.split(":", 2)
                code = code.strip().upper()
                occ = int(occ.strip())

                # STRICT internal detection: ONLY customer token decides
                customer_token = customer.strip().upper()

                is_internal = (
                    "VVDN" in customer_token
                    or "INTERNAL" in customer_token
                )

                detail_list.append({
                    "code": code,
                    "occupancy": occ,
                    "customer": customer_token,
                    "is_internal": is_internal
                })

            # DEBUG LOG
            logger.info(f"🔍 Parsed DEP_DETAIL for {emp_id} => {detail_list}")

            return {
                "emp_id": emp_id,
                "exp_years": exp_years,
                "project_count": project_count,
                "skills": skills,
                "dep_detail": detail_list,
                "tech_group": tech_group
            }

        except Exception as e:
            logger.error(f"❌ Compact parse error: {e}")
            return None


    def _availability_score_for_prerank(self, code: str, occ: int) -> float:
        """
        Simple availability score for pre-ranked external employees.
        Code mapping is aligned with your deployment normalization.
        """
        code = (code or "").upper()
        base_map = {
            "IN": 95,
            "FR": 95,
            "BK": 85,
            "SH": 80,
            "RD": 70,
            "BU": 60,
            "BIL": 40,
            "CRD": 30
        }
        base = base_map.get(code, 60)

        if occ <= 20:
            base += 10
        elif occ <= 50:
            base += 0
        elif occ <= 80:
            base -= 10
        elif occ < 100:
            base -= 20
        else:  # 100
            base -= 30

        return max(0, min(95, base))

    def _skill_score_for_prerank(self, parsed_query, skills: list) -> float:
        """
        Smarter skill scoring:
        - Measures overlap between employee skills and query skills.
        - Rewards Full-Stack / Polyglot / Cross-platform combinations.
        """
        if not skills:
            return 40.0

        emp = set(s.lower() for s in skills)

        query = set()
        for key in ("semantic_skills", "skills"):
            for s in parsed_query.get(key, []) or []:
                query.add(s.lower().strip())

        if not query:
            return 60.0  # Neutral baseline when no explicit skills in query.

        overlap = len(emp.intersection(query))

        # Base overlap scoring
        if overlap == len(query):
            score = 90.0
        elif overlap >= (len(query) // 2):
            score = 75.0
        elif overlap > 0:
            score = 60.0
        else:
            score = 30.0

        # --- Add stronger tech reasoning ---
        blob = " ".join(emp)

        is_fullstack = (
            ("react" in blob or "angular" in blob or "frontend" in blob)
            and ("java" in blob or "spring" in blob or "node" in blob or "python" in blob)
        )

        is_polyglot_backend = (
            ("java" in blob and "python" in blob)
            or ("java" in blob and "node" in blob)
            or ("python" in blob and "node" in blob)
        )

        is_cross_platform = (
            ("android" in blob and "react" in blob)
            or ("ios" in blob and "flutter" in blob)
        )

        if is_fullstack:
            score = max(score, 80)
        if is_polyglot_backend:
            score = max(score, 85)
        if is_cross_platform:
            score = max(score, 80)

        return float(score)

    def _availability_reason_text(self, total_external_occupancy, total_internal_occupancy):
        if total_external_occupancy > 0:
            if total_external_occupancy >= 90:
                return "very limited availability due to heavy external client work"
            if total_external_occupancy >= 70:
                return "low availability because of significant external client work"
            return "moderate availability with some client commitments"
        else:
            # Internal only → always more flexible
            if total_internal_occupancy >= 90:
                return "moderate availability despite being fully involved in an internal initiative"
            return "good availability as they are mainly on internal work"

    def _strength_reason_text(self, strong_skill_match, tech_group_matches):
        if strong_skill_match:
            return "strong matching skills for the requested role"
        if tech_group_matches:
            return "relevant technical background aligned with the role"
        return "general technical experience"

    def _build_reason_for_prerank(self, availability_text, strength_text):
        return (
            f"This employee has {availability_text}, and brings {strength_text}. "
            "Their current workload limits their redeployability for immediate allocation."
        )


    def _experience_score_for_prerank(self, exp_years: float) -> float:
        """
        Simple, HR-like experience scoring.
        """
        if exp_years <= 1:
            return 30.0
        if exp_years <= 3:
            return 50.0
        if exp_years <= 6:
            return 65.0
        if exp_years <= 10:
            return 80.0
        return 90.0



    def pre_rank_employees_simplified(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    employee_data_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Python pre-ranking for EXTERNAL-HEAVY employees ONLY.
        
        EXTERNAL-HEAVY DEFINITION: Any deployment with BIL/BU/BUD/IB/CRD code and occupancy ≥ 80%
        
        IMPORTANT: External-heavy employees get LOW SCORES because they are heavily committed
        to external client work and should NOT be assigned to new projects.
        """

        logger.info("🧮 Starting Python pre-ranking for EXTERNAL-HEAVY employees...")

        def parse_dep_detail(dep_detail: str) -> List[Dict[str, Any]]:
            entries = []
            if not dep_detail:
                return entries
            for raw in dep_detail.split(";"):  
                raw = raw.strip()
                if not raw:
                    continue
                parts = raw.split(":")
                if len(parts) < 2:
                    continue
                code = parts[0].strip().upper()
                try:
                    occ = int(parts[1])
                except Exception:
                    occ = 0
                customer = parts[2].strip().upper() if len(parts) > 2 else ""
                is_internal = ("VVDN" in customer) or ("INTERNAL" in customer)
                entries.append({
                    "code": code,
                    "occupancy": occ,
                    "customer": customer,
                    "is_internal": is_internal
                })
            return entries

        # EXTERNAL-HEAVY CODES (as per LLM prompt)
        # These are the codes that indicate heavy external client work
        # BIL = Billable, BU = Budgeted, BUD = Budgeted, IB = Internal Budgeted, CRD = Credited
        external_heavy_codes = {"BIL", "BU", "BUD", "CRD"}
        
        # OCCUPANCY THRESHOLD for external-heavy (as per LLM prompt)
        heavy_occupancy_threshold = 80

        pre_ranked: List[Dict[str, Any]] = []
        llm_candidates: List[Dict[str, Any]] = []

        for emp in employees:
            emp_id_full = emp.get("employee_id", "")
            compression = emp.get("compression", "")
            parts = compression.split("|")

            if len(parts) < 9:
                llm_candidates.append(emp)
                continue

            compact_emp_id = parts[0].strip()
            tech_group = parts[2].strip()
            exp_str = parts[4].strip()
            proj_count_str = parts[5].strip()
            dep_detail = parts[8].strip()
            skills_text = parts[9].strip().lower() if len(parts) > 9 else ""

            # Parse basic info
            try:
                non_free_project_count = int(float(proj_count_str))
            except Exception:
                non_free_project_count = 0

            try:
                exp_years = float(exp_str)
            except Exception:
                exp_years = 0.0

            # Get seniority
            orig = employee_data_lookup.get(emp_id_full, {})
            designation = (orig.get("designation") or "").lower()
            is_senior = any(k in designation for k in ["lead", "principal", "architect", "sr ", "tech lead", "senior"])

            # Parse deployment details
            entries = parse_dep_detail(dep_detail)
            if not entries:
                llm_candidates.append(emp)
                continue

            # Separate internal and external entries
            internal_entries = [e for e in entries if e["is_internal"]]
            external_entries = [e for e in entries if not e["is_internal"]]
            
            total_external_occupancy = sum(e["occupancy"] for e in external_entries)
            
            # Get query skills for skill matching
            query_skills = [s.lower() for s in parsed_query.get("semantic_skills", [])] or \
                        [s.lower() for s in parsed_query.get("skills", [])]
            
            # ============================================
            # CHECK IF EMPLOYEE IS EXTERNAL-HEAVY
            # ============================================
            is_external_heavy = False
            heavy_code_used = None
            heavy_occupancy = 0
            
            # Check each external entry for heavy codes with high occupancy
            for e in external_entries:
                code = e["code"]
                occ = e["occupancy"]
                
                if code in external_heavy_codes and occ >= heavy_occupancy_threshold:
                    is_external_heavy = True
                    heavy_code_used = code
                    heavy_occupancy = occ
                    break
            
            # ============================================
            # DECISION: PRE-RANK ONLY EXTERNAL-HEAVY EMPLOYEES
            # ============================================
            if is_external_heavy:
                # EXTERNAL-HEAVY EMPLOYEE - GIVE LOW SCORES (FIXED as per LLM prompt)
                
                # Calculate skill match for criteria scores
                perfect_skill_match = False
                good_skill_match = False
                
                if query_skills:
                    matched_skills = sum(1 for skill in query_skills if skill in skills_text)
                    if matched_skills == len(query_skills):
                        perfect_skill_match = True
                    elif matched_skills > 0:
                        good_skill_match = True
                
                # ============================================
                # FIXED SCORES FOR EXTERNAL-HEAVY (as per LLM prompt)
                # ============================================
                
                if not is_senior:
                    # NON-SENIOR EXTERNAL-HEAVY
                    if total_external_occupancy >= 90:
                        # Very heavily committed (≥90%) → LOWEST SCORE
                        tier = 4
                        overall_score = 10.0
                    else:
                        # Heavily committed (≥80% but <90%) → LOW SCORE
                        tier = 3
                        overall_score = 20.0
                else:
                    # SENIOR EXTERNAL-HEAVY
                    if total_external_occupancy >= 90 or non_free_project_count >= 3:
                        # Very busy senior → LOW SCORE
                        tier = 3
                        overall_score = 25.0
                    else:
                        # Senior with some availability → MODERATE SCORE
                        llm_candidates.append(emp)
                        continue
                
                # ============================================
                # CALCULATE CRITERIA SCORES (for display only)
                # ============================================
                
                # 1. SKILL SCORE
                if perfect_skill_match:
                    skill_score = 95.0
                elif good_skill_match:
                    skill_score = 70.0
                else:
                    skill_score = 50.0
                
                # 2. TECH GROUP SCORE
                ctx = parsed_query.get("context", "")
                if isinstance(ctx, list):
                    ctx = " ".join([str(x).lower() for x in ctx])
                else:
                    ctx = str(ctx).lower()
                
                tech_group_lower = str(tech_group).lower()
                tech_score = 40.0  # Default mismatch
                
                # Simple tech group matching for external-heavy
                if any(term in tech_group_lower for term in ctx.split()):
                    tech_score = 95.0
                elif ("backend" in tech_group_lower or "back end" in tech_group_lower) and "backend" in ctx:
                    tech_score = 80.0
                elif "full stack" in tech_group_lower and ("full stack" in ctx or "backend" in ctx):
                    tech_score = 80.0
                
                # 3. EXPERIENCE SCORE
                if exp_years >= 8:
                    exp_score = 100.0
                elif exp_years >= 5:
                    exp_score = 80.0
                elif exp_years >= 3:
                    exp_score = 60.0
                elif exp_years >= 1:
                    exp_score = 40.0
                else:
                    exp_score = 20.0
                
                # 4. AVAILABILITY SCORE (LOW for external-heavy)
                if perfect_skill_match:
                    availability_score = 30.0  # External-heavy with perfect skills
                elif good_skill_match:
                    availability_score = 20.0  # External-heavy with good skills
                elif skill_score >= 50:
                    availability_score = 10.0  # External-heavy with basic skills
                else:
                    availability_score = 5.0   # External-heavy with no skills
                
                # Senior multitasking bonus
                if is_senior and perfect_skill_match and tech_score >= 90:
                    availability_score = min(100.0, availability_score + 30.0)
                
                # Add to pre-ranked list
                pre_ranked.append({
                    **emp,
                    "ranked_by": "system",
                    "ai_tier": tier,
                    "ai_score": round(overall_score, 1),  # FIXED LOW SCORE
                    "ai_criteria": {
                        "Skill": round(skill_score, 1),
                        "TechGroup": round(tech_score, 1),
                        "Availability": round(availability_score, 1),
                        "Experience": round(exp_score, 1)
                    },
                })
                
                logger.info(f"🔍 EXTERNAL-HEAVY PRE-RANKED {compact_emp_id}: "
                        f"code={heavy_code_used}, occ={heavy_occupancy}%, "
                        f"senior={is_senior}, tier={tier}, score={overall_score}")
            
            else:
                # NOT EXTERNAL-HEAVY → send to LLM
                llm_candidates.append(emp)
                
                # Debug logging
                if external_entries:
                    ext_codes = [e['code'] for e in external_entries]
                    ext_occ = [e['occupancy'] for e in external_entries]
                    logger.info(f"🔍 SEND TO LLM {compact_emp_id}: Not external-heavy "
                            f"(codes={ext_codes}, occ={ext_occ})")
                else:
                    logger.info(f"🔍 SEND TO LLM {compact_emp_id}: No external entries")

        logger.info(f"🧮 Pre-ranked {len(pre_ranked)} EXTERNAL-HEAVY employees with LOW SCORES")
        logger.info(f"🧠 Sending {len(llm_candidates)} employees to LLM")

        return pre_ranked, llm_candidates



    async def llm_rank_candidates_simplified(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
    ) -> List[Dict[str, Any]]:

        import html, re, time

        if not employees:
            return []

        start_time = time.time()

        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running LLM PDP ranking for {len(employees)} candidates...")

        prompt = f"""
You are an expert HR evaluator performing PURE reasoning-style ranking using a PDP
(Preference–Demotion–Promotion) framework.

You must produce for each employee:
1) A TIER (1–4)
2) Reasoning must be short justification why the employee received THIS tier and score. No filler words. No repetition.
3) A set of numeric scores: Skill XX, TechGroup XX, Availability XX, Experience XX, OverallScore XX

PRIORITY REASONING:
- Do NOT explain skills.
- Focus only on availability first, then Project, then Domain (If Needed).
- Use one short priority-driven statement.
Keep it extremely short.
No comparison words.
No explanations.
No restating scores.

Constraints:
- Reasoning MUST be fully grounded ONLY in the compact record.
- No hallucinated skills, customers, or roles.
- Mention tech-group match or mismatch, basic skill alignment, internal vs external work, and rough availability.
- NEVER output raw internal codes like "FR", "BK", "SH", "RD", "BU", "BIL", "CRD", "IN".
- NEVER output raw DEP_DETAIL strings or customer tokens like "EXTREMENETWORKS" or "VVDNINTERNALPROJECT".
- Use generic phrases like "internal company project", "external client project", "fully occupied on client work", etc.

COMPACT FORMAT:
id|role_code|tech_group|location|experience_years|project_count|department|DEP_SUMMARY|DEP_DETAIL|skills

DEP_DETAIL contains one or more deployment entries separated by semicolons ';'.

Each entry follows the format:
CODE:OCCUPANCY:CUSTOMER_TOKEN

Examples:
IN:10:VVDNINTERNAL;BUD:90:CUSTOMER

SKILL INTERPRETATION RULES:
- Analyze skills carefully to detect cross-platform capabilities:
  • Frontend + Backend skills = Full Stack capability
  • Mobile + Web skills (Android + React, iOS + Flutter) = Cross-Platform capability
  • Multiple backend languages (Java + Python + Node) = Polyglot backend capability
- Even if tech_group doesn't mention "Full Stack" or "Hybrid", consider skill combinations
- Give credit for versatile skill sets that match project requirements across domains
- "JavaScript" and "Java" are COMPLETELY different technologies - never confuse them
- "Java Script" = JavaScript (frontend), NOT Java (backend)
- Only match exact skills, not partial matches

INTERNAL PROJECT OVERRIDE (highest priority):
If ANY DEP_DETAIL entry has CUSTOMER containing "VVDN" or "INTERNAL":
    → Employee is on internal company work
    → MUST be Tier 1 or 2 (NEVER Tier 3 or 4)
    → Occupancy decides within {1,2}:
        0–50 total internal occupancy → Tier 1
        >50–100 internal occupancy   → Tier 1 (still internal, high priority)

Internal projects include: VVDNINTERNALPROJECT, VVDNTRAINING, etc.
CRITICAL RULE (APPLIES FIRST, OVERRIDES ALL OTHER RULES):
- If ANY external occupancy ≥ 80% AND experience_years < 5 AND role is not senior → MUST be Tier 3 or 4 ONLY. Internal projects do NOT override this rule.
- If Free (FR), this employee should have the top tier 1 and score even compared with Internal projects.

If an employee is FREE (FR) in deployment and their skills + tech_group match the job query:
→ They MUST be Tier 1 and placed at the top of Tier 1.
→ Experience does NOT override FR availability.
→ No employee with lower availability should outrank a FREE employee if the conditions match

SHADOW/BACKUP EXCEPTION (APPLIES AFTER CRITICAL RULE):
- Shadow/Backup (SH/BK) deployments are special cases:
  • If on Internal projects → Can be Tier 1 (low end)
  • If on External projects with low occupancy (<50%) → Can be Tier 2
  • If on External projects with high occupancy (≥80%) → Still subject to CRITICAL RULE above
- Shadow/Backup indicates learning/support role with more flexibility than billable roles

CUSTOMER DETECTION RULES:
- Internal project ONLY if CUSTOMER_TOKEN contains "VVDN" or "INTERNAL"
- All other customers are EXTERNAL clients
- Never assume a project is internal unless explicitly marked

HIGH-LEVEL RULES:
- If tech_group and/or skills clearly match the PROJECT QUERY domain → they can be Tier 1–2,
  subject to availability.
- If they are clearly in a different domain and skills do not match → Tier 3–4.
- Internal company work usually indicates better redeployability than heavy external client work.
- Higher occupancy on external client work reduces availability unless employee is on deployments SH/BK.
- More experience slightly improves the tier, but never fully compensates for very poor availability.

SCORING:
- Skill, TechGroup, Availability, Experience: return values between 0 and 100.

AVAILABILITY SCORING:
1. If any deployment has code FR: → Availability = 100 (fully available).
2. Else if there is ANY external work (BIL, BU, BUD, IB, CRD):
   → Availability = max(0, 40 - total_external_occupancy/2).
     (Example: 100% external → 0, 80% external → 0, 60% external → 10, 50% external → 15, 30% external → 25.)
3. Else (only internal work: IN, RD, SH, BK):
   → Availability = max(30, 100 - total_internal_occupancy/2).
     (Example: 100% internal → 50, 80% internal → 60, 50% internal → 75, 30% internal → 85.)

SKILL SCORING (PRECISE VALUES):
- Direct match to ALL required skills: 90-100
- Direct match to PRIMARY skill only: 70-85  
- Partial/related match: 50-69
- Basic match: 30-49
- No match: 0-29

SCORE BASED ON SKILL MATCH QUALITY:
1. EXCELLENT MATCH (90-100):
   - Has ALL required skills from query
   - PLUS demonstrates advanced knowledge/certifications
   - PLUS has related complementary skills
   Example for Python Django query: "Python, Django, Flask, REST APIs, SQL" = 95-100
2. VERY GOOD MATCH (80-89):
   - Has ALL required skills from query
   - Basic level without advanced expertise
   Example: "Python, Django" = 85-89
3. GOOD MATCH (70-79):
   - Has PRIMARY required skill with depth
   - Missing some secondary required skills
   Example: "Python Level 2, OOPs, Modules" (no Django) = 72-78
4. BASIC MATCH (60-69):
   - Has PRIMARY required skill at basic level
   - No advanced knowledge demonstrated
   Example: "Python" (only, no Django, no advanced topics) = 62-68
5. PARTIAL MATCH (50-59):
   - Has some related skills but not direct match
   Example: "Java, Spring" for Python query = 52-58
6. WEAK MATCH (40-49):
   - Very basic or marginally related skills
   Example: "C programming" for Python query = 42-48
7. NO MATCH (0-39):
   - Completely unrelated skills

TECH GROUP SCORING (MUST FOLLOW QUERY ANALYSIS):

ANALYZE THE INPUT QUERY

IF QUERY MENTIONS SPECIFIC TECHNOLOGY (Python, Java, Android, React, etc):
- Tech groups containing that specific technology: 90-100 (EXACT MATCH)
- Other tech groups in same domain: 70-85 (RELATED)
- Full Stack tech groups: 75-90 (VERSATILE)
- Other domains: 30-65 (PARTIAL/MISMATCH)

IF QUERY MENTIONS DOMAIN ONLY (backend, frontend, mobile):
- Tech groups in that exact domain: 85-100 (EXACT MATCH)
- Full Stack tech groups: 80-95 (VERSATILE)
- Related domains: 60-80 (RELATED)
- Different domains: 30-55 (MISMATCH)

TECH GROUP SCORING EXAMPLES BASED ON QUERY:

FOR PYTHON-RELATED QUERIES:
- Backend - Python: 95-100 (EXACT MATCH)
- Other Backend (Java, NodeJS, .NET): 65-80 (BACKEND DOMAIN)
- Full Stack: 75-90 (CAN DO PYTHON BACKEND)
- Frontend (React, Angular, Vue): 40-60 (DIFFERENT DOMAIN)
- Mobile (Android, iOS): 35-55 (DIFFERENT DOMAIN)
- Database/DevOps: 50-70 (RELATED)

FOR BACKEND-ONLY QUERIES:
- All Backend groups (Python, Java, NodeJS): 85-100
- Full Stack: 80-95
- Frontend: 45-65
- Mobile: 40-60

FOR ANDROID-RELATED QUERIES:
- Android: 95-100
- iOS, Hybrid Mobile: 70-85
- Full Stack: 65-80
- Backend: 50-70
- Frontend: 45-65

SPECIAL CASE: "Backend - DB" TECH GROUP
- For backend queries: Score 70-85 (specialized backend but not application development)
- For Python/Java/Node backend queries: Score 60-75 (database skills are related but not core development)
- For frontend/mobile queries: Score 40-60 (different domain)

EXPERIENCE SCORING (PRECISE VALUES):
- 0-1 years: 20
- 1-3 years: 40  
- 3-5 years: 60
- 5-8 years: 80
- 8+ years: 100

OVERALL SCORE CALCULATION:
OverallScore = (Skill × 0.35) + (TechGroup × 0.25) + (Availability × 0.25) + (Experience × 0.15)

TIER BOUNDARIES (STRICT):
- Tier 1: OverallScore ≥ 80
- Tier 2: OverallScore 41-79
- Tier 3: OverallScore 20-40
- Tier 4: OverallScore 0-19

SCORING EXAMPLES FOR REFERENCE:
1. Free employee with perfect skills: Skill=95, TechGroup=95, Availability=100, Experience=40 → Score=86 → Tier 1
2. Internal employee with good match: Skill=80, TechGroup=85, Availability=50, Experience=60 → Score=70 → Tier 2
3. External-heavy with partial skills: Skill=60, TechGroup=70, Availability=10, Experience=40 → Score=47 → Tier 2
4. External-heavy with no skills: Skill=30, TechGroup=40, Availability=5, Experience=20 → Score=25 → Tier 3
5. Mismatch with high experience: Skill=40, TechGroup=30, Availability=30, Experience=100 → Score=45 → Tier 2

OUTPUT FORMAT (STRICT, ONE LINE PER EMPLOYEE):
emp_id | TIER <1–4> | OverallScore XX | [Skill XX, TechGroup XX, Availability XX, Experience XX] | <exactly 2 concise sentences HR reasoning>

Do NOT add any extra lines or commentary.
Do NOT output scores with decimal points (use whole numbers).
Do NOT deviate from the scoring formulas above.

PROJECT QUERY:
\"{query}\"

CONTEXT: {parsed_query.get('context','general')}
SKILLS NEEDED: {parsed_query.get('skills',[])}
LOCATION PREFERENCE: {parsed_query.get('location','any')}

EMPLOYEES:
{profiles_text}
"""

        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        results = []

        # Simple parsing for format: emp_id|tier|score|[criteria]|reasoning
        for line in clean.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
                
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                logger.warning(f"⚠️ LLM line skipped (insufficient parts): {line}")
                continue
                
            try:
                emp_id = parts[0].replace("VVDN/", "").strip()
                # Extract tier number - handle both "TIER 1" and "1" formats
                tier_text = parts[1].upper().replace("TIER", "").strip()
                # Extract first number found in the tier text
                tier_match = re.search(r'(\d+)', tier_text)
                tier = int(tier_match.group(1)) if tier_match else 4
                score = float(parts[2].replace("OverallScore", "").strip())
                
                # Parse criteria - handle both formats
                criteria_text = parts[3]
                ai_criteria = {}
                
                # Extract numbers from brackets [100, 100, 100, 167, 95]
                numbers = re.findall(r'\d+', criteria_text)
                if len(numbers) >= 4:
                    ai_criteria = {
                        "Skill": float(numbers[0]),
                        "TechGroup": float(numbers[1]), 
                        "Availability": float(numbers[2]),
                        "Experience": float(numbers[3])
                    }
                else:
                    # Fallback to named parsing
                    for crit in ["Skill", "TechGroup", "Availability", "Experience"]:
                        match = re.search(fr"{crit}\s*[:=\s]\s*([0-9]+)", criteria_text, re.I)
                        ai_criteria[crit] = float(match.group(1)) if match else 0.0
                
                reason_text = " ".join(parts[4:]).strip()
                # Clean up [Skill XX] prefix from reasoning
                reason_text = re.sub(r'^\[Skill \d+\]\s*', '', reason_text)
                
                results.append({
                    "emp": emp_id,
                    "tier": tier,
                    "score": score,
                    "reason": reason_text,
                    "ai_criteria": ai_criteria,
                })
                
            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️ LLM line parse error: {line} - {e}")
                continue





        final_ranked = []

        for emp in employees:
            emp_id = emp["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r["emp"] == emp_id), None)

            if match:
                final_ranked.append({
                    **emp,
                    "ranked_by": "ai",
                    "ai_tier": match["tier"],
                    "ai_score": match["score"],
                    "ai_reason": match["reason"],
                    "ai_criteria": match["ai_criteria"],
                })
            else:
                # Fallback if LLM missed this employee
                final_ranked.append({
                    **emp,
                    "ranked_by": "ai",
                    "ai_tier": 4,
                    "ai_score": 0.0,
                    "ai_reason": "No LLM-based reasoning available.",
                    "ai_criteria": {crit: 0.0 for crit in ["Skill", "TechGroup", "Availability", "Experience"]},
                })

        logger.info(f"🏁 LLM ranking completed for {len(final_ranked)} employees in {time.time() - start_time:.2f}s")
        return final_ranked


    async def llm_progressive_rank_single_with_criteria_simplified_fix_new(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    top_k: int = None
) -> List[Dict[str, Any]]:

        import html, re, time

        if not employees:
            return []

        start_time = time.time()

        profiles_text = "\n".join(
            f"{i+1}. {e['compression']}" for i, e in enumerate(employees)
        )

        logger.info(f"⚡ Running PURE PDP reasoning for {len(employees)} employees...")

        # -------------------------------------------------------------------------
        # STRICT PROMPT (unchanged logic-wise – external-heavy already filtered)
        # -------------------------------------------------------------------------
        prompt = f"""
You are an expert HR evaluator. You MUST balance skill matching with availability.

PROJECT QUERY: "{query}"
REQUIRED SKILLS: {parsed_query.get('skills', [])}
PREFERRED TECH GROUPS: {parsed_query.get('context', [])}

CRITICAL PRINCIPLE: Skill excellence can compensate for limited availability, especially for senior employees.

SCORING RULES:

1. SKILL SCORE (0-100):
   - Direct match to required skills: 90-100
   - Related/semantic match (Python→Django, Java→Spring): 70-89
   - Partial/basic match: 50-69
   - No match: 0-49

2. TECHGROUP SCORE (0-100):
   - Exact match to preferred groups: 95-100
   - Related domain (Backend→Full Stack): 70-94
   - Some relevance: 40-69
   - Mismatch: 0-39

3. AVAILABILITY SCORE (0-100) - SKILL-AWARE:
   FREE (FR) employees: 100
   
   EXTERNAL HEAVY (BIL/BU/BUD/IB/CRD ≥80%):
   - Perfect skills: 30-40 (seniors: 40-50)
   - Good skills: 20-30
   - Basic skills: 10-20
   - No skills: 5-10
   
   MIXED DEPLOYMENTS:
   - Calculate as: 100 - (external_occupancy × 0.7) + (skill_bonus × 10)
   - Skill bonus: Perfect=3, Good=2, Basic=1, None=0
   
   INTERNAL ONLY (IN/RD/SH/BK):
   - 100% internal: 30-40
   - <100% internal: 60 - (internal_occupancy × 0.3)

4. EXPERIENCE SCORE (0-100):
   - 0-1 year: 20
   - 1-3 years: 40
   - 3-5 years: 60
   - 5-8 years: 80
   - 8+ years: 100

SENIORITY BONUS (NEW):
- Senior employees (Lead/Principal/Architect/Sr) get +20 to Availability score
- They can manage multiple projects better

TIER ASSIGNMENT (Skill-Weighted):
PERFECT MATCH employees (Skill≥90, TechGroup≥90):
- Tier 1: Score ≥70
- Tier 2: Score 40-69
- Tier 3: Score 20-39
- NEVER Tier 4

GOOD MATCH employees (Skill≥70, TechGroup≥70):
- Tier 1: Score ≥80  
- Tier 2: Score 45-79
- Tier 3: Score 20-44
- Tier 4: Score <20

OTHER employees:
- Standard tiers

OVERALL SCORE CALCULATION:
For PERFECT matches: Score = (Skill×0.40 + TechGroup×0.30 + Availability×0.20 + Experience×0.10)
For GOOD matches: Score = (Skill×0.35 + TechGroup×0.25 + Availability×0.25 + Experience×0.15)
For OTHERS: Score = (Skill×0.30 + TechGroup×0.20 + Availability×0.30 + Experience×0.20)

EXAMPLE SCENARIOS:
1. Senior with perfect Python skills but 100% external:
   - Skill: 95, TechGroup: 95, Availability: 50 (30+20 senior bonus), Experience: 80
   - Score: 95×0.40 + 95×0.30 + 50×0.20 + 80×0.10 = 38 + 28.5 + 10 + 8 = 84.5 → Tier 1

2. Junior with perfect skills but 100% external:
   - Skill: 95, TechGroup: 95, Availability: 30, Experience: 30
   - Score: 95×0.40 + 95×0.30 + 30×0.20 + 30×0.10 = 38 + 28.5 + 6 + 3 = 75.5 → Tier 1

3. Employee with no skill match, 100% external:
   - Skill: 20, TechGroup: 40, Availability: 5, Experience: 50
   - Score: 20×0.30 + 40×0.20 + 5×0.30 + 50×0.20 = 6 + 8 + 1.5 + 10 = 25.5 → Tier 3

OUTPUT FORMAT:
emp_id | TIER <1-4> | OverallScore XX | [Skill XX, TechGroup XX, Availability XX, Experience XX] | <2 sentences>

EMPLOYEES:
{profiles_text}"""

        # -------------------------------------------------------------------------
        # LLM CALL
        # -------------------------------------------------------------------------
        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        results = []

        for raw_line in clean.splitlines():
            line = raw_line.strip()
            if not line or "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue

            emp_raw = re.sub(r"[^A-Za-z0-9/]", "", parts[0])
            emp_id = emp_raw.replace("VVDN", "").replace("/", "").strip()
            if not emp_id.isdigit():
                continue

            # TIER from second part
            tier_match = re.search(r"TIER\s*(\d+)", parts[1], re.I)
            tier = int(tier_match.group(1)) if tier_match else 4

            # Overall score from third part
            score_match = re.search(r"(\d+)", parts[2])
            overall_score = float(score_match.group(1)) if score_match else 0.0

            # Find criteria block: first part that contains '[' and ']'
            criteria_idx = None
            for i in range(3, len(parts)):
                if "[" in parts[i] and "]" in parts[i]:
                    criteria_idx = i
                    break

            if criteria_idx is None or criteria_idx >= len(parts) - 1:
                logger.warning(f"⚠️ Malformed LLM line (no criteria or reasoning) for emp {emp_id}: {line}")
                continue

            criteria_block = parts[criteria_idx]
            reason_text = " ".join(parts[criteria_idx + 1:]).strip()

            ai_criteria: Dict[str, float] = {}
            for crit in ["Skill", "TechGroup", "Availability", "Experience"]:
                m = re.search(fr"{crit}[:=\s]*([0-9]+\.?[0-9]*)", criteria_block, re.I)
                ai_criteria[crit] = float(m.group(1)) if m else 0.0

            # If everything is zero and reasoning empty, treat as malformed and skip
            all_zero = all(v == 0.0 for v in ai_criteria.values())
            if (not reason_text) and all_zero and overall_score == 0.0:
                logger.warning(f"⚠️ Skipping malformed LLM output for emp {emp_id} (empty reason & scores). Raw: {line}")
                continue

            # Minimal fallback reasoning if empty
            if not reason_text:
                reason_text = (
                    "This employee's tier is based on their skills, technical group alignment and current project availability. "
                    "Details are inferred from the compressed deployment and skills data."
                )

            results.append({
                "emp": emp_id,
                "tier": tier,
                "score": overall_score,
                "reason": reason_text,
                "ai_criteria": ai_criteria,
            })

        # -------------------------------------------------------------------------
        # MERGE RESULTS BACK INTO EMPLOYEES
        # -------------------------------------------------------------------------
        final_ranked: List[Dict[str, Any]] = []

        for emp in employees:
            emp_id_numeric = emp["employee_id"].replace("VVDN/", "")
            match = next((r for r in results if r["emp"] == emp_id_numeric), None)

            if match:
                final_ranked.append({
                    **emp,
                    "ai_tier": match["tier"],
                    "ai_score": match["score"],
                    "ai_reason": match["reason"],
                    "ai_criteria": match["ai_criteria"],
                })
            else:
                # No line or malformed line for this employee
                logger.warning(f"⚠️ No valid LLM output for employee {emp['employee_id']} – defaulting to Tier 4.")
                final_ranked.append({
                    **emp,
                    "ai_tier": 4,
                    "ai_score": 0.0,
                    "ai_reason": "No valid reasoning available from AI; defaulted to a low tier based on missing output.",
                    "ai_criteria": {
                        "Skill": 0.0,
                        "TechGroup": 0.0,
                        "Availability": 0.0,
                        "Experience": 0.0,
                    },
                })

        final_ranked.sort(key=lambda x: x["ai_tier"])

        logger.info(f"🏁 Ranking completed in {time.time() - start_time:.2f}s")
        return final_ranked


    async def llm_generate_reason_and_scores(self, pre_ranked: List[Dict[str, Any]]):
        """
        LLM generates reasoning ONLY. All scores remain unchanged.
        """
        import html, re

        if not pre_ranked:
            return pre_ranked
        
        start_time = time.time()

        profiles_text = "\n".join(
            f"{emp['employee_id']} | TIER {emp['ai_tier']} | SCORE {emp['ai_score']} | "
            f"SKILL {emp['ai_criteria'].get('Skill', 0)} | TECH {emp['ai_criteria'].get('TechGroup', 0)} | "
            f"AVAIL {emp['ai_criteria'].get('Availability', 0)} | EXP {emp['ai_criteria'].get('Experience', 0)}"
            for emp in pre_ranked
        )

        prompt = f"""
You are an HR evaluator providing reasoning for pre-ranked employees.

CRITICAL: DO NOT modify any scores or tiers. They are already calculated correctly.

Your task for EACH employee:
Reasoning must justify in natural words why the employee received THIS tier and score. No filler words. No repetition.

IMPORTANT: DO NOT mention ANY deployment codes or customer names. Use only generic descriptions.

SCORE INTERPRETATION:
- Skill (XX): Skill match quality (higher = better match)
- TechGroup (XX): Technology domain alignment (higher = better alignment)  
- Availability (XX): Current availability (higher = more available)
- Experience (XX): Years of experience (higher = more experienced)
- Tier (1-4): 1=best, 4=lowest priority

REASONING GUIDELINES:
Based on Skill score:
- ≥80: "excellent/strong skill alignment"
- 60-79: "good/relevant skills"  
- <60: "limited/partial skill match"

Based on TechGroup score:
- ≥80: "exact/perfect domain match"
- 60-79: "related domain alignment"
- <60: "domain mismatch"

Based on Availability score:
- ≥70: "high/complete availability"
- 40-69: "moderate/partial availability" 
- <40: "limited/heavy occupancy"

Based on Experience score:
- Consider if experience adds value or is limited

ALWAYS USE GENERIC TERMS:
- Instead of codes: "external client work", "internal project", "current assignments"
- Instead of customers: "client projects", "company initiatives", "current engagements"

NEVER MENTION:
- FR, BK, SH, RD, BU, BIL, BUD, IB, CRD, IN (any deployment codes)
- Customer names like "Extreme Networks", "Buspatrol", "NXP"
- Technical jargon or abbreviations

PRIORITY REASONING:
- Do NOT explain skills.
- Focus only on availability first, then tech group, then experience.
- Use one short priority-driven statement.
Keep it extremely short.
No comparison words.
No explanations.
No restating scores.

OUTPUT FORMAT (one line per employee):
emp_id | TIER X | <2 sentences reasoning>

EMPLOYEES WITH EXISTING SCORES:
{profiles_text}
"""

        response = await self.llm_service.generate_response(prompt)
        clean = html.unescape(response.strip())

        # Create a mapping of employee_id to new reasoning
        reasoning_map = {}
        
        for line in clean.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:  # Only need emp_id, tier, and reason
                continue

            emp_id = parts[0]
            
            # Extract reasoning (everything after TIER)
            if len(parts) >= 3:
                reason = " | ".join(parts[2:]).strip()
            else:
                reason = parts[-1].strip()
            
            reasoning_map[emp_id] = reason

        # Update only the reasoning in pre_ranked
        for emp in pre_ranked:
            eid = emp["employee_id"]
            if eid in reasoning_map:
                # ONLY update the reasoning, keep all scores unchanged
                emp["ai_reason"] = reasoning_map[eid]
            else:
                # Fallback: use existing or generate basic reason
                if "ai_reason" not in emp or not emp.get("ai_reason"):
                    emp["ai_reason"] = f"No LLM reasoning available"
        
        logger.info(f"🏁 LLM reasoning completed for {len(pre_ranked)} employees in {time.time() - start_time:.2f}s")
        return pre_ranked


    def pre_rank_employees_simplified_enhanced(
    self,
    query: str,
    parsed_query: Dict[str, Any],
    employees: List[Dict[str, Any]],
    employee_data_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Enhanced Python pre-ranking with actual_context and improved skill matching.
        Gives higher weights to employees with matching tech groups and skills.
        """
        logger.info("🧮 Starting Enhanced Python pre-ranking with actual_context matching...")

        # Get actual_context from parsed_query for enhanced matching
        actual_context = parsed_query.get('actual_context', [])
        query_skills = parsed_query.get('skills', []) + parsed_query.get('semantic_skills', [])
        
        def parse_dep_detail(dep_detail: str) -> List[Dict[str, Any]]:
            entries = []
            if not dep_detail:
                return entries
            for raw in dep_detail.split(";"):  
                raw = raw.strip()
                if not raw:
                    continue
                parts = raw.split(":")
                if len(parts) < 2:
                    continue
                code = parts[0].strip().upper()
                try:
                    occ = int(parts[1])
                except Exception:
                    occ = 0
                customer = parts[2].strip().upper() if len(parts) > 2 else ""
                is_internal = ("VVDN" in customer) or ("INTERNAL" in customer)
                entries.append({
                    "code": code,
                    "occupancy": occ,
                    "customer": customer,
                    "is_internal": is_internal
                })
            return entries

        def calculate_tech_group_match_score(emp_tech_group: str) -> float:
            """Enhanced tech group matching using actual_context"""
            if not actual_context:
                return 60.0
            
            emp_tech_lower = emp_tech_group.lower()
            for actual_ctx in actual_context:
                if actual_ctx.lower() in emp_tech_lower or emp_tech_lower in actual_ctx.lower():
                    return 95.0  # Perfect match with actual context
            
            # Fallback to simplified context matching
            context = parsed_query.get('context', [])
            if isinstance(context, str):
                context = [context]
            
            for ctx in context:
                if ctx.lower() in emp_tech_lower:
                    return 80.0  # Good match with simplified context
            
            return 50.0  # No match

        def calculate_enhanced_skill_score(emp_skills: List[str]) -> float:
            """Enhanced skill scoring with semantic matching"""
            if not query_skills or not emp_skills:
                return 40.0
            
            emp_skills_lower = [s.lower().strip() for s in emp_skills]
            query_skills_lower = [s.lower().strip() for s in query_skills]
            
            # Direct matches
            direct_matches = len(set(emp_skills_lower) & set(query_skills_lower))
            
            # Semantic matches (related technologies)
            semantic_matches = 0
            semantic_map = {
                'java': ['spring', 'springboot', 'hibernate', 'maven'],
                'javascript': ['react', 'angular', 'vue', 'nodejs', 'typescript'],
                'python': ['django', 'flask', 'fastapi'],
                'android': ['kotlin', 'java'],
                'ios': ['swift'],
                'flutter': ['dart']
            }
            
            for query_skill in query_skills_lower:
                for emp_skill in emp_skills_lower:
                    if query_skill in semantic_map.get(emp_skill, []) or emp_skill in semantic_map.get(query_skill, []):
                        semantic_matches += 0.5
            
            total_matches = direct_matches + semantic_matches
            match_ratio = total_matches / len(query_skills_lower)
            
            if match_ratio >= 0.8:
                return 95.0
            elif match_ratio >= 0.5:
                return 85.0
            elif match_ratio >= 0.3:
                return 70.0
            elif total_matches > 0:
                return 60.0
            else:
                return 30.0

        severity_order = {
            "FR": 1, "BK": 2, "SH": 3,
            "RD": 4,
            "BU": 5, "BUD": 5, "IB": 5,
            "BIL": 6, "CRD": 7, "CLIENT": 7,
        }

        heavy_codes = {"BIL", "BU", "BUD", "IB", "CRD"}
        shadow_codes = {"SH"}
        unknown_codes = {"UK"}
        heavy_occ_threshold = 80

        pre_ranked: List[Dict[str, Any]] = []
        llm_candidates: List[Dict[str, Any]] = []

        for emp in employees:
            emp_id_full = emp.get("employee_id", "")
            compression = emp.get("compression", "")
            parts = compression.split("|")

            if len(parts) < 9:
                llm_candidates.append(emp)
                continue

            compact_emp_id = parts[0].strip()
            role_code = parts[1].strip()
            tech_group = parts[2].strip()
            loc_code = parts[3].strip()
            exp_str = parts[4].strip()
            proj_count_str = parts[5].strip()
            dep_summary = parts[7].strip()
            dep_detail = parts[8].strip()
            skills = [s.strip().lower() for s in parts[9].split(",")] if len(parts) > 9 else []

            try:
                non_free_project_count = int(float(proj_count_str))
            except Exception:
                non_free_project_count = 0

            try:
                exp_years = float(exp_str)
            except Exception:
                exp_years = 0.0

            orig = employee_data_lookup.get(emp_id_full, {})
            designation = (orig.get("designation") or "").lower()
            is_senior = any(k in designation for k in ["lead", "principal", "architect", "manager"])

            entries = parse_dep_detail(dep_detail)

            if not entries:
                llm_candidates.append(emp)
                continue

            has_internal = any(e["is_internal"] for e in entries)
            external_entries = [e for e in entries if not e["is_internal"]]
            total_external_occupancy = sum(e["occupancy"] for e in external_entries)
            has_heavy_external = any(e["code"].upper() in heavy_codes and e["occupancy"] >= 70 for e in external_entries)
            
            if has_internal:
                if total_external_occupancy >= 80 or has_heavy_external:
                    pass  # Continue to external_heavy logic
                else:
                    llm_candidates.append(emp)
                    continue

            external_heavy = False
            external_project_count = len(external_entries)
            non_zero_external_projects = [e for e in external_entries if e["occupancy"] > 0]
            has_shadow_external = any(e["code"].upper() in shadow_codes and e["occupancy"] >= 80 for e in external_entries)
            has_unknown_external = any(e["code"].upper() in unknown_codes for e in external_entries)
            
            if (external_project_count >= 3 or len(entries) >= 5 or 
                total_external_occupancy >= 80 or 
                len(non_zero_external_projects) > 0 and external_project_count >= 2 or 
                has_shadow_external or 
                has_unknown_external and external_project_count >= 1):
                external_heavy = True

            for e in external_entries:
                code = e["code"].upper()
                occ = e["occupancy"]
                if code in heavy_codes and occ >= heavy_occ_threshold:
                    external_heavy = True

            if not external_heavy:
                llm_candidates.append(emp)
                continue

            # Enhanced scoring for external heavy employees
            tech_group_score = calculate_tech_group_match_score(tech_group)
            skill_score = calculate_enhanced_skill_score(skills)
            
            # Enhanced availability scoring
            ext = total_external_occupancy
            int_occ = sum(e["occupancy"] for e in entries if e["is_internal"])
            
            if ext > 0:
                availability_score = max(10.0, 50.0 - (ext * 0.4))
            else:
                availability_score = max(30.0, 100.0 - (int_occ * 0.7))

            if is_senior:
                availability_score += 5.0

            if exp_years >= 10:
                availability_score += 5.0
            elif exp_years >= 5:
                availability_score += 5.0
            elif exp_years >= 3:
                availability_score += 2.5

            availability_score = max(0.0, min(100.0, availability_score))
            exp_score = self._experience_score_for_prerank(exp_years)

            # Enhanced tier calculation with tech group and skill matching
            tech_skill_bonus = 0
            if tech_group_score >= 90 and skill_score >= 80:  # Perfect match
                tech_skill_bonus = 1
            elif tech_group_score >= 80 or skill_score >= 70:  # Good match
                tech_skill_bonus = 0.5

            if not is_senior:
                if total_external_occupancy >= 90:
                    tier = max(3, 4 - tech_skill_bonus)  # Can improve from 4 to 3 with good match
                    overall = 18.0 + (tech_skill_bonus * 15)  # 18-33 range
                else:
                    tier = max(2, 3 - tech_skill_bonus)  # Can improve from 3 to 2 with perfect match
                    overall = 26.0 + (tech_skill_bonus * 20)  # 26-46 range
            else:
                if total_external_occupancy >= 90 or non_free_project_count >= 3:
                    tier = max(2, 3 - tech_skill_bonus)  # Can improve from 3 to 2
                    overall = 32.0 + (tech_skill_bonus * 18)  # 32-50 range
                else:
                    tier = max(1, 2 - tech_skill_bonus)  # Can improve from 2 to 1 with perfect match
                    overall = 50.0 + (tech_skill_bonus * 25)  # 50-75 range

            tier = int(tier)
            total_internal_occupancy = sum(e["occupancy"] for e in entries if e["is_internal"])
            
            availability_text = self._availability_reason_text(total_external_occupancy, total_internal_occupancy)
            strength_text = self._strength_reason_text(skill_score >= 70, tech_group_score >= 80)
            reason = self._build_reason_for_prerank(availability_text, strength_text)

            pre_ranked.append({
                **emp,
                "ai_tier": tier,
                "ai_score": overall,
                "ai_reason": reason,
                "ai_criteria": {
                    "Skill": skill_score,
                    "TechGroup": tech_group_score,
                    "Availability": availability_score,
                    "Experience": exp_score
                },
            })

        logger.info(f"🧮 Enhanced pre-ranking complete: {len(pre_ranked)} pre-ranked, {len(llm_candidates)} for LLM")
        return pre_ranked, llm_candidates