import json
import logging
import datetime
import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from ..repositories.project_repository import ProjectRepository
from ..core.database import get_db_session
from ..services.llm_service import LLMService
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain keyword clusters
# Each domain key → skills that BELONG to that domain.
# Language domains (python/java/node/…) also inherit "backend" + "database"
# via _get_domain_skills().
# ---------------------------------------------------------------------------
DOMAIN_CLUSTERS: Dict[str, List[str]] = {
    # ── Backend languages ──────────────────────────────────────────────────
    "python":    ["python", "django", "flask", "fastapi", "celery", "sqlalchemy",
                  "pydantic", "asyncio", "aiohttp", "pytest", "uvicorn"],
    "java":      ["java", "spring", "springboot", "spring boot", "hibernate",
                  "maven", "gradle", "jpa", "junit", "quarkus", "micronaut"],
    "node":      ["node", "nodejs", "node.js", "express", "nestjs", "koa", "hapi",
                  "typescript", "javascript"],
    "dotnet":    ["dotnet", ".net", "csharp", "c#", "asp.net", "blazor", "dot net"],

    # ── Frontend frameworks ────────────────────────────────────────────────
    "react":     ["react", "reactjs", "redux", "nextjs", "next.js", "next",
                  "zustand", "react native"],
    "angular":   ["angular", "rxjs", "ngrx", "ionic"],
    "vue":       ["vue", "vuejs", "nuxt", "nuxtjs", "nuxt.js"],

    # ── Mobile ────────────────────────────────────────────────────────────
    "android":   ["android", "kotlin", "jetpack", "compose", "gradle"],
    "ios":       ["ios", "swift", "swiftui", "objective-c", "xcode"],
    "flutter":   ["flutter", "dart"],

    # ── Cloud / Ops ────────────────────────────────────────────────────────
    "aws":       ["aws", "ec2", "s3", "lambda", "cloudformation", "ecs", "eks",
                  "rds", "dynamodb", "sqs", "sns", "cloudwatch", "route53"],
    "azure":     ["azure", "aks", "azure functions", "cosmos db", "azure devops",
                  "arm templates", "bicep"],
    "gcp":       ["gcp", "google cloud", "bigquery", "cloud run", "gke",
                  "pub/sub", "firebase"],
    "devops":    ["docker", "kubernetes", "k8s", "terraform", "ansible",
                  "jenkins", "github actions", "gitlab ci", "ci/cd", "helm",
                  "prometheus", "grafana", "argocd", "circleci"],

    # ── QA ────────────────────────────────────────────────────────────────
    "qa_manual":    ["manual testing", "test cases", "test plan", "bug reporting",
                     "jira", "functional testing", "regression testing",
                     "exploratory testing", "uat", "sanity testing"],
    "qa_auto":      ["selenium", "cypress", "playwright", "appium", "testng",
                     "junit", "pytest", "jest", "robot framework", "karate",
                     "postman", "rest assured", "jmeter", "gatling",
                     "load testing", "test automation", "bdd", "cucumber"],

    # ── Database ──────────────────────────────────────────────────────────
    "database":  ["sql", "nosql", "postgresql", "mysql", "mongodb", "redis",
                  "cassandra", "oracle", "dba", "query optimization",
                  "database design", "stored procedures", "indexing"],

    # ── AI / ML ───────────────────────────────────────────────────────────
    "aiml":      ["machine learning", "deep learning", "tensorflow", "pytorch",
                  "scikit", "nlp", "llm", "langchain", "huggingface",
                  "computer vision", "data science", "pandas", "numpy"],

    # ── Embedded ──────────────────────────────────────────────────────────
    "embedded":  ["c", "c++", "rtos", "embedded", "firmware", "linux kernel",
                  "bare metal", "fpga", "arm", "stm32"],

    # ── Generic base clusters (inherited, not matched directly) ───────────
    "backend":   ["microservices", "rest api", "graphql", "grpc", "rabbitmq",
                  "kafka", "redis", "postgresql", "mysql", "mongodb",
                  "elasticsearch", "nginx", "api gateway", "oauth", "jwt",
                  "websocket", "message queue", "event driven", "soap",
                  "swagger", "openapi"],
    "frontend":  ["html", "css", "javascript", "typescript", "webpack", "vite",
                  "tailwind", "sass", "scss", "figma", "responsive design",
                  "pwa", "accessibility", "storybook"],
    "mobile":    ["mobile", "cross platform", "push notification", "sqlite",
                  "realm", "firebase", "deep linking"],
}

# ---------------------------------------------------------------------------
# Designation → seniority tier
# Used to add a seniority hint to the anonymous token so LLM can assign
# leadership roles correctly — without leaking the actual name/title.
# ---------------------------------------------------------------------------
def _seniority_tier(designation: str) -> str:
    """
    Returns one of: lead | senior | mid | junior
    Derived purely from designation keywords — no personal data exposed.
    """
    d = (designation or "").lower()
    if any(k in d for k in ["director", "ceo", "president", "avp", "vp", "cto"]):
        return "director"
    if any(k in d for k in ["tech lead", "team lead", "lead", "principal",
                              "architect", "manager", "head"]):
        return "lead"
    if any(k in d for k in ["senior", "sr.", "sr ", "staff"]):
        return "senior"
    if any(k in d for k in ["junior", "jr.", "jr ", "trainee", "intern",
                              "fresher", "associate"]):
        return "junior"
    return "mid"


# ---------------------------------------------------------------------------
# Tech group normalization
# ---------------------------------------------------------------------------
# Priority list — more specific domains checked before generic ones.
_NORMALIZE_PRIORITY = [
    "python", "java", "node", "dotnet",
    "react", "angular", "vue",
    "flutter", "android", "ios",
    "aws", "azure", "gcp", "devops",
    "qa_auto", "qa_manual",          # auto before manual so "automation" hits first
    "aiml", "embedded", "database",
    "backend", "frontend", "mobile",
]

# Extra keyword aliases not covered by DOMAIN_CLUSTERS keys
_EXTRA_ALIASES: Dict[str, str] = {
    "dot net":     "dotnet",
    "next":        "react",   # "Frontend - Next" → react domain
    "nuxt":        "vue",
    "automation":  "qa_auto",
    "manual":      "qa_manual",
    "qa":          "qa_manual",   # bare "QA" defaults to manual; auto wins if "auto" present
    "db":          "database",
    "backend - db": "database",
    "ops":         "devops",
}


def _normalize_tech_group(raw: str) -> str:
    """
    Normalize raw tech_group → canonical domain key.

    "Backend - Python"   → python
    "Backend - Java"     → java
    "Backend - Node"     → node
    "Backend - DB"       → database
    "Frontend - React"   → react
    "Frontend - Angular" → angular
    "Frontend - Vue"     → vue
    "Frontend - Next"    → react   (Next.js is React-based)
    "Ops - AWS"          → aws
    "Ops - Azure"        → azure
    "Android"            → android
    "iOS"                → ios
    "Manual"             → qa_manual
    "Automatic" / "Automation" → qa_auto
    """
    if not raw:
        return "general"

    t = raw.strip().lower()
    t = re.sub(r"[^a-z0-9\s\-\./]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # 1. Check full-string aliases first (e.g. "backend - db")
    for alias, domain in _EXTRA_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", t):
            return domain

    # 2. Check priority domain names and their representative keywords
    for domain in _NORMALIZE_PRIORITY:
        if re.search(rf"\b{re.escape(domain.replace('_', ' '))}\b", t):
            return domain
        for kw in DOMAIN_CLUSTERS.get(domain, []):
            if re.search(rf"\b{re.escape(kw)}\b", t):
                return domain

    return "general"


# ---------------------------------------------------------------------------
# Domain skill inheritance
# ---------------------------------------------------------------------------
def _get_domain_skills(domain: str) -> List[str]:
    skills = list(DOMAIN_CLUSTERS.get(domain, []))
    if domain in {"python", "java", "node", "dotnet"}:
        skills += DOMAIN_CLUSTERS["backend"]
        skills += DOMAIN_CLUSTERS["database"]
    elif domain in {"react", "angular", "vue"}:
        skills += DOMAIN_CLUSTERS["frontend"]
    elif domain in {"android", "ios", "flutter"}:
        skills += DOMAIN_CLUSTERS["mobile"]
    elif domain in {"aws", "azure", "gcp"}:
        skills += DOMAIN_CLUSTERS["devops"]
    elif domain in {"qa_manual", "qa_auto"}:
        # qa_auto also knows manual basics
        if domain == "qa_auto":
            skills += DOMAIN_CLUSTERS["qa_manual"]
    return list(set(skills))


# ---------------------------------------------------------------------------
# Primary / secondary skill classification
# ---------------------------------------------------------------------------
def _classify_skills(raw_skills: str, domain: str) -> Tuple[List[str], List[str]]:
    if not raw_skills:
        return [], []
    tokens = [s.strip().lower() for s in re.split(r"[,|;]+", raw_skills) if s.strip()]
    domain_skills = _get_domain_skills(domain)
    primary, secondary = [], []
    for skill in tokens:
        is_primary = any(ds in skill or skill in ds for ds in domain_skills)
        (primary if is_primary else secondary).append(skill)
    return primary, secondary


# ---------------------------------------------------------------------------
# Anonymous token builder
# Format: E<n>|<domain>|<seniority>|primary:<skills>|secondary:<skills>
# Nothing personally identifiable is included.
# ---------------------------------------------------------------------------
def _make_token(seq_id: int, domain: str, seniority: str,
                primary: List[str], secondary: List[str],
                freepool_occupancy: int = 0) -> str:
    p = ",".join(primary[:8]) or "none"
    s = ",".join(secondary[:4]) or "none"
    return f"E{seq_id}|{domain}|{seniority}|free:{freepool_occupancy}%|primary:{p}|secondary:{s}"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class FreepoolProjectSuggestionService:
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.llm = LLMService()

    # ── 1. Fetch freepool employees ────────────────────────────────────────
    def _get_freepool_employees(self) -> List[Dict[str, Any]]:
        rows = self.project_repo.get_employees_with_projects()
        emp_map: Dict[str, Dict] = {}
        for row in rows:
            eid = row["employee_id"]
            if eid not in emp_map:
                emp_map[eid] = {
                    "employee_id": eid,
                    "display_name": row.get("display_name", ""),
                    "designation":  row.get("designation", ""),
                    "tech_group":   row.get("tech_group", ""),
                    "skill_set":    row.get("skill_set", ""),
                    "employee_department": row.get("employee_department", ""),
                    "total_exp":    row.get("total_exp", ""),
                    "deployment":   "free",
                    "total_occupancy": 0,
                    "freepool_occupancy": 0,
                }
            emp = emp_map[eid]
            if row.get("project_name"):
                dep = (row.get("deployment") or "").strip().lower()
                occupancy = row.get("occupancy") or 0
                if dep == "free":
                    emp["freepool_occupancy"] += occupancy
                else:
                    emp["total_occupancy"] += occupancy

        return [
            e for e in emp_map.values()
            if e["freepool_occupancy"] > 0 or e["total_occupancy"] == 0
        ]

    # ── 2. Enrich with domain + classified skills + seniority ─────────────
    def _enrich_employees(self, employees: List[Dict]) -> List[Dict]:
        enriched = []
        for emp in employees:
            domain = _normalize_tech_group(emp.get("tech_group", ""))
            primary, secondary = _classify_skills(emp.get("skill_set", ""), domain)
            seniority = _seniority_tier(emp.get("designation", ""))
            enriched.append({
                **emp,
                "domain":           domain,
                "seniority":        seniority,
                "primary_skills":   primary,
                "secondary_skills": secondary,
            })
        return enriched

    # ── 3. Build anonymous token map ──────────────────────────────────────
    def _build_token_map(
        self, employees: List[Dict]
    ) -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
        tokens, token_to_id, id_to_token = [], {}, {}
        for i, emp in enumerate(employees, start=1):
            key = f"E{i}"
            token_str = _make_token(
                i, emp["domain"], emp["seniority"],
                emp["primary_skills"], emp["secondary_skills"],
                emp.get("freepool_occupancy", 0),
            )
            tokens.append(token_str)
            token_to_id[key] = emp["employee_id"]
            id_to_token[emp["employee_id"]] = key
        return tokens, token_to_id, id_to_token

    # ── 4. LLM: project suggestions ───────────────────────────────────────
    async def _suggest_projects(
        self, tokens: List[str]
    ) -> Tuple[List[Dict], List[str]]:
        token_text = "\n".join(tokens)
        prompt = f"""
You are a senior technology consultant at a product engineering company
that primarily delivers Cloud and Web-based projects.

AVAILABLE ENGINEERS (anonymous):
Each line: TokenID | domain | seniority | free:X% | primary:skills | secondary:skills

FIELD MEANINGS:
- free: % is mentioning this much of availabilty this employee has. Higher = more available for new projects.

DOMAIN MEANINGS:
python=Backend-Python  java=Backend-Java  node=Backend-NodeJS  dotnet=Backend-.NET
react=Frontend-React   angular=Frontend-Angular  vue=Frontend-Vue/Nuxt
android=Android  ios=iOS  flutter=Flutter
aws=Cloud-AWS  azure=Cloud-Azure  gcp=Cloud-GCP  devops=DevOps
qa_manual=QA-Manual  qa_auto=QA-Automation  database=DB-Specialist
aiml=AI/ML  embedded=Embedded

SENIORITY MEANINGS:
director = Director / CTO / VP / AVP — strategic oversight only, DO NOT assign as project lead
lead   = Tech Lead / Team Lead / Architect — PREFERRED project lead; also contributes code
senior = Senior Engineer — strong individual contributor
mid    = Mid-level Engineer
junior = Junior / Trainee — needs guidance

RULES FOR ASSIGNMENT:
1. OCCUPANCY PRIORITY: Prefer engineers with higher free% for project assignments.
   Engineers with free:100% are fully available. Engineers with free:0% must NOT be assigned.
   For part-time availability (e.g. free:50%), assign only if their role is non-critical or part-time.
2. PROJECT LEAD selection:
   a. ALWAYS prefer "lead" seniority as Project Lead / Tech Lead.
   b. NEVER assign "director" seniority as project lead — they are strategic advisors only.
   c. If no "lead" is available, promote the most senior engineer with the highest free%.
3. Use PRIMARY skills for role assignment. Use secondary only if no primary match exists.
4. Suggest as many projects as the team size and skill mix can support.
5. Consider QA Engineers (qa_manual / qa_auto) for the project if they have the skills for developing and testing.
6. Reasoning should be why we considered this employee for this role by their primary skill, secondary skill and availability and should not include the TokenID while reasoning.
ENGINEERS:
{token_text}

TASK:
Suggest impactful AI-driven or advanced tech project ideas for this team.
For each project assign specific TokenIDs to roles.

Respond ONLY as a JSON array, no markdown:
[
  {{
    "project_title": "...",
    "description": "...",
    "tech_stack": ["..."],
    "estimated_duration": "...",
    "business_value": "...",
    "team_assignments": [
      {{
        "token_id": "E1",
        "assigned_role": "...",
        "seniority_used": "lead/senior/mid/junior",
        "skill_type": "primary or secondary",
        "reason": "..."
      }}
    ],
    "required_roles": ["..."]
  }}
]
"""
        raw = await self.llm.generate_response(prompt)
        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                projects = json.loads(match.group())
                assigned = {
                    a.get("token_id", "")
                    for p in projects
                    for a in p.get("team_assignments", [])
                }
                return projects, list(assigned)
        except Exception as e:
            logger.warning(f"Project suggestion LLM parse failed: {e}")
        return [], []

    # ── 5. LLM: upskill suggestions (batch) ───────────────────────────────
    async def _suggest_upskill_batch(
        self, tokens: List[str]
    ) -> Dict[str, List[Dict]]:
        if not tokens:
            return {}
        token_text = "\n".join(tokens)
        prompt = f"""
You are a senior tech career advisor at a product engineering company
that delivers Cloud and Web projects.

ENGINEERS ON BENCH (no project assigned):
Each line: TokenID | domain | seniority | free:X% | primary:skills | secondary:skills

FIELD MEANINGS:
free: % is mentioning this much of availabilty this employee has. Higher = more available and has more availability

SENIORITY MEANINGS:
director = Director / CTO / VP / AVP / CEO
lead   = Tech Lead / Architect
senior = Senior Engineer
mid    = Mid-level Engineer
junior = Junior / Trainee

ENGINEERS:
{token_text}

TASK:
For EACH engineer suggest exactly 3 upskilling recommendations.
Consider their seniority:
- director    → suggest strategic/leadership skills (product strategy, team management, etc.) and advanced system architecture skills
- lead/senior → suggest advanced/architectural skills (system design, cloud architecture, etc.)
- mid         → suggest depth in primary domain + one adjacent skill
- junior      → suggest fundamentals first, then one trending tool

Each suggestion must:
1. Build on their PRIMARY skill domain
2. Be relevant to cloud/web projects mainly associated with current trends
3. Be realistic to learn in 4-8 weeks
4. Consider the occupancy for calculating estimated_weeks (less occupancy will takes more time to upskill)
5. Reasoning should not include the TokenID.

Respond ONLY as a JSON object keyed by TokenID, no markdown:
{{
  "E3": [
    {{
      "skill": "...",
      "reason": "...",
      "learning_path": "...",
      "estimated_weeks": 4,
      "relevance_to_company": "..."
    }}
  ]
}}
"""
        raw = await self.llm.generate_response(prompt)
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"Upskill batch LLM parse failed: {e}")
        return {}

    # ── 6. Resolve tokens → real employee data ────────────────────────────
    def _resolve_assignments(
        self, projects: List[Dict],
        token_to_id: Dict[str, str],
        emp_map: Dict[str, Dict],
    ) -> List[Dict]:
        resolved = []
        for proj in projects:
            assignments = []
            for a in proj.get("team_assignments", []):
                eid = token_to_id.get(a.get("token_id", ""))
                if not eid:
                    continue
                emp = emp_map.get(eid, {})
                assignments.append({
                    "employee_id":     eid,
                    "display_name":    emp.get("display_name", ""),
                    "designation":     emp.get("designation", ""),
                    "seniority":       emp.get("seniority", ""),
                    "tech_group":      emp.get("tech_group", ""),
                    "domain":          emp.get("domain", ""),
                    "assigned_role":   a.get("assigned_role", ""),
                    "seniority_used":  a.get("seniority_used", ""),
                    "skill_type":      a.get("skill_type", ""),
                    "reason":          a.get("reason", ""),
                    "primary_skills":  emp.get("primary_skills", []),
                    "secondary_skills": emp.get("secondary_skills", []),
                })
            resolved.append({**proj, "team_assignments": assignments})
        return resolved

    def _resolve_upskill(
        self, upskill_map: Dict[str, List[Dict]],
        token_to_id: Dict[str, str],
        emp_map: Dict[str, Dict],
    ) -> List[Dict]:
        result = []
        for token_id, suggestions in upskill_map.items():
            eid = token_to_id.get(token_id)
            if not eid:
                continue
            emp = emp_map.get(eid, {})
            result.append({
                "employee_id":      eid,
                "display_name":     emp.get("display_name", ""),
                "designation":      emp.get("designation", ""),
                "seniority":        emp.get("seniority", ""),
                "tech_group":       emp.get("tech_group", ""),
                "domain":           emp.get("domain", ""),
                "primary_skills":   emp.get("primary_skills", []),
                "secondary_skills": emp.get("secondary_skills", []),
                "upskill_suggestions": suggestions if isinstance(suggestions, list) else [],
            })
        return result

    # ── 7. DB persistence — single upsert row ─────────────────────────────
    def _save_to_db(self, result: Dict[str, Any]) -> None:
        """
        Always keeps exactly ONE row in freepool_suggestions.
        On every API call: DELETE all → INSERT fresh row.
        Stores project_suggestions and upskill_suggestions as JSONB.
        """
        try:
            with get_db_session() as session:
                session.execute(text("DELETE FROM freepool_suggestions"))
                session.execute(text("""
                    INSERT INTO freepool_suggestions
                        (freepool_count, tech_groups_in_freepool,
                        project_suggestions, upskill_suggestions)
                    VALUES
                        (:freepool_count, :tech_groups_in_freepool,
                        :project_suggestions, :upskill_suggestions)
                """), {
                    "freepool_count": result["freepool_count"],
                    "tech_groups_in_freepool": result["tech_groups_in_freepool"],
                    "project_suggestions": json.dumps(result["project_suggestions"]),
                    "upskill_suggestions": json.dumps(result["upskill_suggestions"])
                })
                session.commit()
            logger.info("✅ Freepool suggestions saved to DB (single row upsert)")
        except Exception as e:
            logger.error(f"❌ Failed to save freepool suggestions to DB: {e}")
            raise

    # ── Main entry point ───────────────────────────────────────────────────
    async def get_suggestions(self) -> Dict[str, Any]:
        try:
            logger.info("Get Freepool Suggestion API hit")
            raw_employees = self._get_freepool_employees()
            logger.info(f"Freepool employees count: {len(raw_employees)}")
            if not raw_employees:
                return {
                    "status": "success",
                    "freepool_count": 0,
                    "tech_groups_in_freepool": 0,
                    "team_composition": [],
                    "project_suggestions": [],
                    "assigned_employee_count": 0,
                    "unassigned_employee_count": 0,
                    "upskill_suggestions": [],
                }

            employees  = self._enrich_employees(raw_employees)
            emp_map    = {e["employee_id"]: e for e in employees}
            tokens, token_to_id, id_to_token = self._build_token_map(employees)

            # LLM calls
            logger.info("Project Suggestion API Call...")
            projects_raw, assigned_tokens = await self._suggest_projects(tokens)
            project_suggestions = self._resolve_assignments(projects_raw, token_to_id, emp_map)

            assigned_ids      = {token_to_id[t] for t in assigned_tokens if t in token_to_id}
            unassigned        = [e for e in employees if e["employee_id"] not in assigned_ids]
            unassigned_tokens = [
                _make_token(
                    int(id_to_token[e["employee_id"]].lstrip("E")),
                    e["domain"], e["seniority"],
                    e["primary_skills"], e["secondary_skills"],
                    e.get("freepool_occupancy", 0),
                )
                for e in unassigned if e["employee_id"] in id_to_token
            ]

            logger.info("Upskill Suggestion API Call...")
            upskill_raw        = await self._suggest_upskill_batch(unassigned_tokens)
            upskill_suggestions = self._resolve_upskill(upskill_raw, token_to_id, emp_map)

            # Team composition grouped by domain
            domain_groups: Dict[str, List] = defaultdict(list)
            for e in employees:
                domain_groups[e["domain"]].append(e)

            result = {
                "status":                   "success",
                "freepool_count":           len(employees),
                "tech_groups_in_freepool":  len(domain_groups),
                "project_suggestions":      project_suggestions,
                "assigned_employee_count":  len(assigned_ids),
                "unassigned_employee_count": len(unassigned),
                "upskill_suggestions":      upskill_suggestions,
            }

            # Persist — always exactly one row
            self._save_to_db(result)
            logger.info("Freepool suggestions complete")
            return
        except Exception as e:
            logger.error(f"Error in get_suggestion: {e}")
            raise

    async def get_suggestions_from_db(self):
        try:
            with get_db_session() as session:
                result = session.execute(text("SELECT * FROM freepool_suggestions")).mappings().all()
                return {'status': 200, 'response': result}
        except Exception as e:
            logger.error(f"Error in getting suggestion for freepool employees: {e}")
            raise