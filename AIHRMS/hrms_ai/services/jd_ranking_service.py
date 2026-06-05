import json
import logging
import re
from typing import Any, Dict, List, Set

from ..repositories.project_repository import ProjectRepository
from ..services.llm_service import LLMService
from .freepool_suggestion_service import (
    _normalize_tech_group,
    _classify_skills,
    _seniority_tier,
)

logger = logging.getLogger(__name__)

BATCH_SIZE  = 200

# ---------------------------------------------------------------------------
# Domain family map — server-side skill_score cap
# ---------------------------------------------------------------------------
_FRONTEND_DOMAINS = {"react", "angular", "vue"}
_BACKEND_DOMAINS  = {"python", "java", "node", "dotnet"}
_MOBILE_DOMAINS   = {"android", "ios", "flutter"}
_CLOUD_DOMAINS    = {"aws", "azure", "gcp"}
_OPS_DOMAINS      = {"devops"}
_QA_DOMAINS       = {"qa_manual", "qa_auto"}
_DATA_DOMAINS     = {"database", "aiml"}
_EMBEDDED_DOMAINS = {"embedded"}

_FAMILY_MAP = [
    _FRONTEND_DOMAINS,
    _BACKEND_DOMAINS,
    _MOBILE_DOMAINS,
    _CLOUD_DOMAINS | _OPS_DOMAINS,
    _QA_DOMAINS,
    _DATA_DOMAINS,
    _EMBEDDED_DOMAINS,
]

_ADJACENT_PAIRS = [
    (_BACKEND_DOMAINS, _DATA_DOMAINS),
    (_CLOUD_DOMAINS,   _OPS_DOMAINS),
    (_BACKEND_DOMAINS, _QA_DOMAINS),
    (_FRONTEND_DOMAINS, _QA_DOMAINS),
]

# Maps broad JD domain (returned by _parse_jd) → set of matching employee domains
_JD_DOMAIN_MAP: Dict[str, set] = {
    "frontend":  _FRONTEND_DOMAINS,
    "backend":   _BACKEND_DOMAINS,
    "mobile":    _MOBILE_DOMAINS,
    "ops":       _CLOUD_DOMAINS | _OPS_DOMAINS,
    "devops":    _OPS_DOMAINS | _CLOUD_DOMAINS,
    "fullstack":  _FRONTEND_DOMAINS | _BACKEND_DOMAINS,
    "general":   set(),  # no cap
}


def _skill_score_cap(emp_domain: str, jd_domain: str) -> int:
    """
    JD domain is broad (frontend/backend/mobile/ops/devops/fullstack/general).
    emp_domain is granular (react/python/android/aws/devops/…).

    Returns the max skill_score the LLM is allowed to give this employee.
    """
    if jd_domain == "general":
        return 100

    jd_family = _JD_DOMAIN_MAP.get(jd_domain, set())

    # Exact match — emp domain is in the JD family
    if emp_domain in jd_family:
        return 100

    # Fullstack: frontend OR backend employee gets full credit;
    # adjacent domains (db, qa, devops) get partial credit
    if jd_domain == "fullstack":
        if emp_domain in _DATA_DOMAINS or emp_domain in _QA_DOMAINS:
            return 40
        if emp_domain in (_CLOUD_DOMAINS | _OPS_DOMAINS):
            return 30
        return 20

    # Same broad family but different tech (shouldn't normally happen with broad JD domains,
    # but handle gracefully)
    emp_family = next((f for f in _FAMILY_MAP if emp_domain in f), None)
    if emp_family and emp_family == jd_family:
        return 70

    # Adjacent pairs — partial credit
    for a, b in _ADJACENT_PAIRS:
        if (emp_domain in a and jd_domain in ("backend", "frontend") and b == jd_family) or \
           (emp_domain in b and a == jd_family):
            return 40
    # backend JD → database/aiml employee gets partial
    if jd_domain == "backend" and emp_domain in _DATA_DOMAINS:
        return 40
    # ops/devops JD → cloud employee gets partial
    if jd_domain in ("ops", "devops") and emp_domain in _CLOUD_DOMAINS:
        return 70
    if jd_domain in ("ops", "devops") and emp_domain in _BACKEND_DOMAINS:
        return 40
    # mobile JD → no adjacent domains, strict
    return 20


# ---------------------------------------------------------------------------
# Availability — computed fully server-side, never delegated to LLM
# availability_score = freepool_occupancy % clamped 0-100
# An employee with 0% freepool occupancy gets availability_score = 0
# ---------------------------------------------------------------------------
def _compute_availability_score(emp: Dict) -> float:
    return min(100.0, max(0.0, float(emp.get("availability_pct", 0))))


# ---------------------------------------------------------------------------
# Experience score — computed server-side with tolerance
# Tolerance: allow employees with exp >= (min_exp - 2) to still appear,
# but score them lower. E.g. JD needs 5y, employee has 3y → score ~60.
# ---------------------------------------------------------------------------
def _compute_experience_score(emp_exp: float, min_exp: int, max_exp: int | None) -> float:
    tolerance = 2
    effective_min = max(0, min_exp - tolerance)
    if emp_exp < effective_min:
        return 0.0

    if emp_exp < min_exp:
        return round(((emp_exp - effective_min) / tolerance) * 60, 1)

    if max_exp is None:
        return 100.0

    if emp_exp <= max_exp:
        return 100.0

    # Over maximum
    over = emp_exp - max_exp
    return max(40.0, round(100 - over * 5, 1))


# ---------------------------------------------------------------------------
# JD parser
# ---------------------------------------------------------------------------
async def _parse_jd(llm: LLMService, jd_text: str) -> Dict[str, Any]:
    prompt = f"""
Extract core technical requirements from the Job Description below.
Ignore contract terms, location, soft skills, vendor fields, evaluation percentages.

JD:
{jd_text}

Reply ONLY with a JSON object with EXACTLY these 7 keys (no extra keys, no markdown):
{{
  "role_title": "...",
  "primary_skills": ["skill1", "skill2"],
  "secondary_skills": ["skill1"],
  "min_experience_years": 3,
  "max_experience_years": null,
  "seniority_preference": "senior",
  "domain": "frontend"
}}

Classification rules (follow exactly):
- domain: pick exactly one from: frontend | backend | mobile | ops | devops | fullstack | general
- primary_skills: ONLY skills that directly belong to the chosen domain. Max 12.
    domain=frontend  → react, angular, vue, javascript, typescript, html, css, tailwind, bootstrap, redux, nextjs are PRIMARY
    domain=backend   → python, django, fastapi, java, spring, node, express, dotnet, rest api, graphql are PRIMARY
    domain=mobile    → android, kotlin, ios, swift, flutter, dart, react native are PRIMARY
    domain=ops/devops → aws, azure, gcp, docker, kubernetes, terraform, ci/cd, jenkins are PRIMARY
    domain=fullstack → both frontend AND backend skills listed above are PRIMARY
- secondary_skills: skills mentioned in the text that do NOT belong to the chosen domain. Max 8.
    Example: domain=frontend but JD also mentions python or docker → secondary_skills.
- min_experience_years: integer. Use 0 if not stated.
- max_experience_years: integer if explicitly stated, otherwise use null.
- seniority_preference: one of senior/lead/mid/junior.
"""
    raw = await llm.generate_response(prompt)
    logger.info(f"JD parse raw: {raw[:300]}")
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            p = json.loads(m.group())
            return {
                "role_title":           str(p.get("role_title") or ""),
                "primary_skills":       list(p.get("primary_skills") or [])[:12],
                "secondary_skills":     list(p.get("secondary_skills") or [])[:8],
                "min_experience_years": int(p.get("min_experience_years") or 0),
                "max_experience_years": int(p["max_experience_years"]) if p.get("max_experience_years") is not None else None,
                "seniority_preference": str(p.get("seniority_preference") or "any"),
                "domain":               str(p.get("domain") or "general"),
            }
    except Exception as e:
        logger.warning(f"JD parse failed: {e} | raw: {raw[:300]}")
    return {"role_title": "", "primary_skills": [], "secondary_skills": [],
            "min_experience_years": 0, "max_experience_years": None,
            "seniority_preference": "any", "domain": "general"}


# ---------------------------------------------------------------------------
# Employee pool builder — includes projects list per employee
# ---------------------------------------------------------------------------
def _build_employee_pool(rows: List[Dict]) -> List[Dict]:
    emp_map: Dict[str, Dict] = {}
    for row in rows:
        desig = (row.get("designation") or "").strip().lower()
        if any(k in desig for k in ["avp", "president", "director", "consultant"]):
            continue
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
            # Track project details
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


def _parse_exp(exp_str: str) -> float:
    nums = re.findall(r"\d+\.?\d*", str(exp_str or ""))
    return float(nums[0]) if nums else 0.0


# ---------------------------------------------------------------------------
# Pre-filter employees before sending to LLM — reduces token load
# ---------------------------------------------------------------------------
def _prefilter(employees: List[Dict], jd: Dict) -> List[Dict]:
    min_exp       = jd["min_experience_years"]
    max_exp       = jd["max_experience_years"]
    jd_domain     = jd["domain"]
    tolerance     = 2  # years below min still considered

    filtered = []
    for emp in employees:
        emp_exp = _parse_exp(emp.get("total_exp", ""))

        # Drop if experience is completely out of range (below tolerance floor)
        if emp_exp < max(0, min_exp - tolerance):
            continue

        # Drop if way over max (more than 15 years over — likely overqualified noise)
        if max_exp is not None:
            if max_exp < 99 and emp_exp > max_exp + 15:
                continue

        # Drop employees whose domain cap is 20 (completely wrong domain)
        # — they'd score at most 20*0.4 + 100*0.3 + 100*0.2 + 100*0.1 = 68 best case
        # but realistically near 0 on skill + low availability → under 25 anyway
        # Keep them only if they have very high availability (≥80%) as a fallback
        if _skill_score_cap(emp["domain"], jd_domain) == 20 and emp.get("availability_pct", 0) < 80:
            continue

        filtered.append(emp)

    logger.info(f"Pre-filter: {len(employees)} → {len(filtered)} employees")
    return filtered


# ---------------------------------------------------------------------------
# Token — skill & experience scores computed server-side, LLM only scores skills
# ---------------------------------------------------------------------------
def _make_token(seq: int, emp: Dict, skill_cap: int) -> str:
    p  = ",".join(emp["primary_skills"][:8]) or "none"
    s  = ",".join(emp["secondary_skills"][:4]) or "none"
    tg = (emp.get("tech_group") or "unknown").strip()
    return f"C{seq}|domain:{emp['domain']}|techgroup:{tg}|{emp['seniority']}|skill_cap:{skill_cap}|primary:{p}|secondary:{s}"


# ---------------------------------------------------------------------------
# LLM ranking — only scores skill_score and secondary_score
# availability_score and experience_score are computed server-side
# ---------------------------------------------------------------------------
async def _rank_batch(llm: LLMService, jd: Dict, tokens: List[str]) -> List[Dict]:
    token_text    = "\n".join(tokens)
    primary_str   = ", ".join(jd["primary_skills"])
    secondary_str = ", ".join(jd["secondary_skills"])
    jd_domain     = jd["domain"]
    n_primary     = max(len(jd["primary_skills"]), 1)

    prompt = f"""
You are a technical recruiter. For each candidate below, score ONLY skill_score and secondary_score.

JOB:
- Domain: {jd_domain}
- Primary Skills (must-have): {primary_str}
- Secondary Skills (nice-to-have): {secondary_str}

CANDIDATE FORMAT:
C<id> | domain | techgroup | seniority | skill_cap:<N> | primary:<skills> | secondary:<skills>

SCORING RULES:

skill_score (0–100):
  - The candidate has a skill_cap field. NEVER exceed it.
  - skill_cap:100 = correct domain, score freely.
  - skill_cap:70  = same domain family, cap at 70.
  - skill_cap:40  = adjacent domain, cap at 40.
  - skill_cap:20  = wrong domain, cap at 20.
  - Within the cap: count how many of the {n_primary} JD primary skills the candidate has.
    skill_score = (matched_count / {n_primary}) * skill_cap
  - Be strict: a React/Frontend engineer cannot score high on a Backend Python JD even if they list Python as a secondary skill.

secondary_score (0–100):
  - Count overlap between candidate's skills and JD secondary skills.
  - secondary_score = (matched_secondary_count / {max(len(jd["secondary_skills"]), 1)}) * 100

ranking_reason:
  - 2 sentences: how many primary skills matched, domain alignment note, any skill gaps.
  - Do NOT mention candidate IDs or token IDs.

CANDIDATES:
{token_text}

Return a JSON array. No markdown, no text outside JSON.
[
  {{
    "candidate_id": "C1",
    "skill_score": 80,
    "secondary_score": 50,
    "ranking_reason": "...",
    "gaps": "..."
  }}
]
"""
    raw = await llm.generate_response(prompt)
    logger.info(f"Ranking batch raw (first 500): {raw[:500]}")
    try:
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        logger.warning(f"No JSON array in ranking response: {raw[:800]}")
    except Exception as e:
        logger.warning(f"Ranking parse failed: {e} | raw: {raw[:500]}")
    return []


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class JDRankingService:
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.llm = LLMService()

    async def rank_by_jd(self, jd_text: str) -> Dict[str, Any]:
        # 1. Parse JD
        jd = await _parse_jd(self.llm, jd_text)
        logger.info(f"Parsed JD: {jd}")

        # 2. Load + build pool
        rows      = self.project_repo.get_employees_with_projects()
        employees = _build_employee_pool(rows)
        logger.info(f"Total employees loaded: {len(employees)}")
        if not employees:
            return {"status": "success", "jd_parsed": jd, "total_candidates": 0, "ranked_candidates": []}

        # 3. Pre-filter to reduce LLM load
        employees = _prefilter(employees, jd)
        if not employees:
            return {"status": "success", "jd_parsed": jd, "total_candidates": 0, "ranked_candidates": []}

        # 4. Build token map
        token_to_id: Dict[str, str] = {}
        cap_map:     Dict[str, int] = {}
        tokens:      List[str]      = []
        for i, emp in enumerate(employees, start=1):
            cid = f"C{i}"
            cap = _skill_score_cap(emp["domain"], jd["domain"])
            tokens.append(_make_token(i, emp, cap))
            token_to_id[cid] = emp["employee_id"]
            cap_map[cid]     = cap
        emp_map = {e["employee_id"]: e for e in employees}

        # 5. Batched LLM calls — only for skill scores
        all_raw: List[Dict] = []
        for start in range(0, len(tokens), BATCH_SIZE):
            batch = tokens[start: start + BATCH_SIZE]
            logger.info(f"Ranking batch {start}–{start + len(batch)}")
            results = await _rank_batch(self.llm, jd, batch)
            logger.info(f"Batch returned {len(results)} results")
            all_raw.extend(results)

        logger.info(f"Total LLM results: {len(all_raw)}")

        # 6. Resolve — availability & experience computed entirely server-side
        min_exp = jd["min_experience_years"]
        max_exp = jd["max_experience_years"]

        ranked = []
        for r in all_raw:
            cid = r.get("candidate_id", "")
            eid = token_to_id.get(cid)
            if not eid:
                continue
            emp = emp_map[eid]

            emp_exp = _parse_exp(emp.get("total_exp", ""))

            # skill_score: LLM value clamped by server-side cap
            skill_score = min(
                float(cap_map.get(cid, 100)),
                min(100.0, max(0.0, float(r.get("skill_score", 0))))
            )
            # secondary_score: LLM value
            secondary_score = min(100.0, max(0.0, float(r.get("secondary_score", 0))))

            # availability_score: fully server-side, never from LLM
            availability_score = _compute_availability_score(emp)

            # experience_score: fully server-side with tolerance
            experience_score = _compute_experience_score(emp_exp, min_exp, max_exp)

            overall_score = round(
                skill_score        * 0.40 +
                experience_score   * 0.10 +
                availability_score * 0.40 +
                secondary_score    * 0.10,
                1
            )


            tier = 1 if overall_score >= 80 else 2 if overall_score >= 60 else 3 if overall_score >= 40 else 4

            ranked.append({
                "employee_id":        eid,
                "display_name":       emp["display_name"],
                "designation":        emp["designation"],
                "tech_group":         emp["tech_group"],
                "domain":             emp["domain"],
                "seniority":          emp["seniority"],
                "total_exp":          emp["total_exp"],
                "availability_pct":   emp["availability_pct"],
                "projects":           emp.get("projects", []),
                "primary_skills":     emp["primary_skills"],
                "secondary_skills":   emp["secondary_skills"],
                "ai_score":           overall_score,
                "ai_reason":          r.get("ranking_reason", ""),
                "gaps":               r.get("gaps", ""),
                "ai_tier":            tier,
                "ai_criteria":        {
                    "Skill":             skill_score,
                    "Experience":        experience_score,
                    "Availability":      availability_score,
                    "SecondarySkill":    secondary_score,
                }
            })

        ranked.sort(key=lambda x: (x["ai_tier"], -x["ai_score"]))
        logger.info(f"Final ranked candidates: {len(ranked)}")

        return {
            "status":            "success",
            "jd_parsed":         jd,
            "total_candidates":  len(ranked),
            "ranked_candidates": ranked,
        }
