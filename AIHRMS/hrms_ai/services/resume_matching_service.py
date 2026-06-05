import json
import logging
import re
from typing import Any, Dict, List

from ..repositories.project_repository import ProjectRepository
from ..services.llm_service import LLMService
from .freepool_suggestion_service import (
    _normalize_tech_group,
    _classify_skills,
    _seniority_tier,
)
from .jd_ranking_service import (
    BATCH_SIZE,
    _parse_exp,
    _compute_availability_score,
    _skill_score_cap,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Employee pool builder — includes ALL designations (directors, AVPs, etc.)
# ---------------------------------------------------------------------------
def _build_employee_pool_all(rows: List[Dict]) -> List[Dict]:
    emp_map: Dict[str, Dict] = {}
    for row in rows:
        eid = row["employee_id"]
        if eid not in emp_map:
            emp_map[eid] = {
                "employee_id":         eid,
                "display_name":        row.get("display_name", ""),
                "designation":         row.get("designation", ""),
                "tech_group":          row.get("tech_group", ""),
                "skill_set":           row.get("skill_set", ""),
                "employee_department": row.get("employee_department", ""),
                "total_exp":           row.get("total_exp", ""),
                "freepool_occupancy":  0,
                "other_occupancy":     0,
                "projects":            [],
            }
        emp = emp_map[eid]
        if row.get("project_name"):
            dep = (row.get("deployment") or "").strip().lower()
            occ = row.get("occupancy") or 0
            emp["projects"].append({
                "project_name": row.get("project_name", ""),
                "deployment":   row.get("deployment", ""),
                "occupancy":    occ,
                "role":         row.get("role", ""),
                "start_date":   str(row.get("start_date") or ""),
                "end_date":     str(row.get("end_date") or ""),
            })
            if dep == "free":
                emp["freepool_occupancy"] += occ
            else:
                emp["other_occupancy"] += occ

    for emp in emp_map.values():
        emp["availability_pct"] = emp["freepool_occupancy"]
        domain = _normalize_tech_group(emp.get("tech_group", ""))
        primary, secondary = _classify_skills(emp.get("skill_set", ""), domain)
        emp["domain"]           = domain
        emp["seniority"]        = _seniority_tier(emp.get("designation", ""))
        emp["primary_skills"]   = primary
        emp["secondary_skills"] = secondary

    return list(emp_map.values())


# ---------------------------------------------------------------------------
# Resume parser
# ---------------------------------------------------------------------------
async def _parse_resume(llm: LLMService, resume_text: str) -> Dict[str, Any]:
    prompt = f"""
Extract the candidate profile from the resume below.
Ignore personal details, addresses, contact info, hobbies, and references.

RESUME:
{resume_text}

Reply ONLY with a JSON object with EXACTLY these 6 keys (no extra keys, no markdown):
{{
  "designation": "current or most recent job title",
  "primary_skills": ["skill1", "skill2"],
  "secondary_skills": ["skill1"],
  "total_experience_years": 5,
  "seniority": "senior",
  "domain": "frontend"
}}

Rules:
- primary_skills: core technical skills the candidate is strong in, max 12.
- secondary_skills: skills used but not primary focus, max 8.
- total_experience_years: integer total years of professional experience.
- seniority: one of senior/lead/mid/junior.
- domain: pick exactly one from:
  frontend | backend | mobile | ops | devops | fullstack | general
"""
    raw = await llm.generate_response(prompt)
    logger.info(f"Resume parse raw: {raw[:300]}")
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            p = json.loads(m.group())
            return {
                "designation":            str(p.get("designation") or ""),
                "primary_skills":         list(p.get("primary_skills") or [])[:12],
                "secondary_skills":       list(p.get("secondary_skills") or [])[:8],
                "total_experience_years": int(p.get("total_experience_years") or 0),
                "seniority":              str(p.get("seniority") or "mid"),
                "domain":                 str(p.get("domain") or "general"),
            }
    except Exception as e:
        logger.warning(f"Resume parse failed: {e} | raw: {raw[:300]}")
    return {
        "designation": "", "primary_skills": [], "secondary_skills": [],
        "total_experience_years": 0, "seniority": "mid", "domain": "general",
    }


# ---------------------------------------------------------------------------
# Token — includes exp so LLM can score experience similarity
# ---------------------------------------------------------------------------
def _make_resume_token(seq: int, emp: Dict, skill_cap: int) -> str:
    p   = ",".join(emp["primary_skills"][:8]) or "none"
    s   = ",".join(emp["secondary_skills"][:4]) or "none"
    exp = _parse_exp(emp.get("total_exp", ""))
    tg  = (emp.get("tech_group") or "unknown").strip()
    return (
        f"C{seq}|domain:{emp['domain']}|techgroup:{tg}|{emp['seniority']}"
        f"|exp:{exp:.1f}y|skill_cap:{skill_cap}|primary:{p}|secondary:{s}"
    )


# ---------------------------------------------------------------------------
# LLM similarity scoring
# Scores: skill_match, experience_match, secondary_match
# Availability is NOT scored by LLM — shown as info only in response
# ---------------------------------------------------------------------------
async def _similarity_batch(
    llm: LLMService, profile: Dict, tokens: List[str]
) -> List[Dict]:
    token_text    = "\n".join(tokens)
    primary_str   = ", ".join(profile["primary_skills"])
    secondary_str = ", ".join(profile["secondary_skills"])
    domain        = profile["domain"]
    candidate_exp = profile["total_experience_years"]
    n_primary     = max(len(profile["primary_skills"]), 1)
    n_secondary   = max(len(profile["secondary_skills"]), 1)

    prompt = f"""
You are an HR analyst. Score how similar each employee is to the incoming candidate profile.

INCOMING CANDIDATE PROFILE:
- Domain: {domain}
- Experience: {candidate_exp} years
- Primary Skills: {primary_str}
- Secondary Skills: {secondary_str}

EMPLOYEE FORMAT:
C<id> | domain | techgroup | seniority | exp:<years>y | skill_cap:<N> | primary:<skills> | secondary:<skills>

SCORING RULES — each score 0 to 100:

skill_match:
  - Each employee has a skill_cap. NEVER exceed it.
  - skill_cap:100 = same domain → score freely based on skill overlap.
  - skill_cap:70  = same domain family → max 70.
  - skill_cap:40  = adjacent domain → max 40.
  - skill_cap:20  = completely different domain → max 20.
  - Within cap: skill_match = (primary_skills_in_common / {n_primary}) * skill_cap
  - A frontend employee matching a backend profile gets low score even with some shared skills.

experience_match:
  - Compare employee exp against candidate exp of {candidate_exp} years.
  - ±1 year difference  → 100
  - ±2 years difference → 80
  - ±3 years difference → 60
  - ±4 years difference → 40
  - ±5+ years difference → 20 or less
  - An employee with 2 years exp is NOT similar to a candidate with 6 years exp. Score them 20 or below.

secondary_match:
  - secondary_match = (secondary_skills_in_common / {n_secondary}) * 100

similarity_reason:
  - 2 sentences covering: primary skill overlap, experience gap or match, domain alignment.
  - Do NOT mention candidate IDs or token IDs.

EMPLOYEES:
{token_text}

Return a JSON array. No markdown, no text outside JSON.
[
  {{
    "candidate_id": "C1",
    "skill_match": 80,
    "experience_match": 90,
    "secondary_match": 50,
    "similarity_reason": "..."
  }}
]
"""
    raw = await llm.generate_response(prompt)
    logger.info(f"Similarity batch raw (first 500): {raw[:500]}")
    try:
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        logger.warning(f"No JSON array in similarity response: {raw[:800]}")
    except Exception as e:
        logger.warning(f"Similarity parse failed: {e} | raw: {raw[:500]}")
    return []


# ---------------------------------------------------------------------------
# Pre-filter — ±4 years exp window, drop completely wrong domain
# ---------------------------------------------------------------------------
def _prefilter_resume(employees: List[Dict], profile: Dict) -> List[Dict]:
    candidate_exp = float(profile["total_experience_years"])
    domain        = profile["domain"]

    filtered = []
    for emp in employees:
        emp_exp = _parse_exp(emp.get("total_exp", ""))
        # Drop if more than 4 years apart — experience_match would be ≤40 anyway
        if abs(emp_exp - candidate_exp) > 4:
            continue
        # Drop completely wrong domain employees
        if _skill_score_cap(emp["domain"], domain) == 20:
            continue
        filtered.append(emp)

    logger.info(f"Resume pre-filter: {len(employees)} → {len(filtered)} employees")
    return filtered


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ResumeMatchingService:
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.llm = LLMService()

    async def match_resume(self, resume_text: str) -> Dict[str, Any]:
        # 1. Parse resume
        profile = await _parse_resume(self.llm, resume_text)
        logger.info(f"Parsed resume profile: {profile}")

        # 2. Load all employees (including directors/AVPs)
        rows      = self.project_repo.get_employees_with_projects()
        employees = _build_employee_pool_all(rows)
        logger.info(f"Total employees loaded: {len(employees)}")
        if not employees:
            return {"status": "success", "resume_profile": profile, "total_matches": 0, "similar_profiles": []}

        # 3. Pre-filter by exp window and domain
        employees = _prefilter_resume(employees, profile)
        if not employees:
            return {"status": "success", "resume_profile": profile, "total_matches": 0, "similar_profiles": []}

        # 4. Build tokens with exp included
        token_to_id: Dict[str, str] = {}
        cap_map:     Dict[str, int] = {}
        tokens:      List[str]      = []
        for i, emp in enumerate(employees, start=1):
            cid = f"C{i}"
            cap = _skill_score_cap(emp["domain"], profile["domain"])
            tokens.append(_make_resume_token(i, emp, cap))
            token_to_id[cid] = emp["employee_id"]
            cap_map[cid]     = cap
        emp_map = {e["employee_id"]: e for e in employees}

        # 5. Batched LLM scoring
        all_raw: List[Dict] = []
        for start in range(0, len(tokens), BATCH_SIZE):
            batch = tokens[start: start + BATCH_SIZE]
            logger.info(f"Similarity batch {start}–{start + len(batch)}")
            results = await _similarity_batch(self.llm, profile, batch)
            logger.info(f"Batch returned {len(results)} results")
            all_raw.extend(results)

        logger.info(f"Total similarity results: {len(all_raw)}")

        # 6. Resolve — skill+exp+secondary from LLM, availability as info only
        matched = []
        for r in all_raw:
            cid = r.get("candidate_id", "")
            eid = token_to_id.get(cid)
            if not eid:
                continue
            emp = emp_map[eid]

            # Clamp LLM scores, enforce domain cap on skill_match
            skill_match = min(
                float(cap_map.get(cid, 100)),
                min(100.0, max(0.0, float(r.get("skill_match", 0))))
            )
            experience_match = min(100.0, max(0.0, float(r.get("experience_match", 0))))
            secondary_match  = min(100.0, max(0.0, float(r.get("secondary_match", 0))))

            # Availability computed server-side — shown in response but NOT in score
            availability_pct = _compute_availability_score(emp)

            # Overall: skill 50%, experience 35%, secondary 15%
            # Availability intentionally excluded from score — this is profile similarity not assignment
            overall_score = round(
                skill_match      * 0.30 +
                experience_match * 0.30 +
                secondary_match  * 0.10 +
                availability_pct * 0.30,
                1
            )

            tier = 1 if overall_score >= 80 else 2 if overall_score >= 60 else 3 if overall_score >= 40 else 4

            matched.append({
                "employee_id":      eid,
                "display_name":     emp["display_name"],
                "designation":      emp["designation"],
                "tech_group":       emp["tech_group"],
                "domain":           emp["domain"],
                "seniority":        emp["seniority"],
                "total_exp":        emp["total_exp"],
                "availability_pct": availability_pct,
                "projects":         emp.get("projects", []),
                "primary_skills":   emp["primary_skills"],
                "secondary_skills": emp["secondary_skills"],
                "ai_score":         overall_score,
                "ai_tier":          tier,
                "ai_reason":        r.get("similarity_reason", ""),
                "ai_criteria": {
                    "Skill":      skill_match,
                    "Experience": experience_match,
                    "SecondarySkill":  secondary_match,
                    "Availability": availability_pct,
                },
            })

        matched.sort(key=lambda x: (x["ai_tier"], -x["ai_score"]))
        logger.info(f"Final similar profiles: {len(matched)}")

        return {
            "status":           "success",
            "resume_profile":   profile,
            "total_matches":    len(matched),
            "similar_profiles": matched,
        }
