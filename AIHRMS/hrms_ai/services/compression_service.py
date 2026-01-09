# services/compression_service.py
import logging, json, re, time
from typing import Dict, Any, List, Tuple
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.project_repository import ProjectRepository
from .cache_manager import cache_manager
from .codebook_service import codebook_service, _make_code

logger = logging.getLogger(__name__)

def _parse_exp(exp_str: str) -> float:
    """
    Accept formats like '2Y 10M', '3Y', '0Y 6M', '3', etc. → returns years as float with 1 decimal.
    """
    if not exp_str: return 0.0
    s = exp_str.upper()
    y = 0; m = 0
    my = re.search(r"(\d+)\s*Y", s)
    mm = re.search(r"(\d+)\s*M", s)
    if my: y = int(my.group(1))
    if mm: m = int(mm.group(1))
    if not my and not mm:
        # plain number? assume years
        try: y = int(re.findall(r"\d+", s)[0])
        except: pass
    years = y + round(m/12.0, 1)
    return round(years, 1)



def _normalize_skills(raw: str) -> List[str]:
    """
    Normalize and enrich skills:
    - Keep original cleaned form
    - Add simplified variants (stem/core forms)
    - Fully generic, no tech hardcoding
    """
    if not raw:
        return []

    toks = re.split(r"[,\|;]+", raw)
    normalized = []

    for t in toks:
        t = t.strip().lower()
        if not t:
            continue

        # Remove bracketed noise but keep inside text
        t = re.sub(r"[\[\]\(\)]", " ", t)
        t = re.sub(r"[^a-z0-9+\s\-\._]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            continue

        variants = set()
        variants.add(t)  # keep original normalized form

        # Split into tokens and remove minor fluff
        words = [w for w in t.split() if w not in {
            "developer", "engineer", "intern", "training", "concepts",
            "language", "framework", "stack", "project", "course"
        }]

        if not words:
            continue

        # Add simplified single-token version if meaningful
        if len(words) > 1:
            # Keep last or first token heuristically
            variants.add(words[0])
            variants.add(words[-1])
            # Join top 2 tokens for hybrid cases like "spring boot"
            variants.add(" ".join(words[:2]))

        # Add alphanumeric stem (e.g. "springboot" from "spring boot")
        if " " in t:
            variants.add(t.replace(" ", ""))

        # Add basic core-word extraction (like removing 'core', 'basic', etc.)
        simple = re.sub(r"\b(core|basic|advanced|intro|fundamental)\b", "", t).strip()
        if simple and simple != t:
            variants.add(simple)

        normalized.extend(list(variants))

    # Deduplicate preserving order
    seen, result = set(), []
    for s in normalized:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result

def _normalize_deployment(raw_dep: str) -> Tuple[str, str]:
    """
    Dynamically infer short deployment code and readable name.
    No hardcoding — uses simple keyword clustering.
    """
    if not raw_dep:
        return "UK", "Unknown"

    dep = raw_dep.strip().lower()

    # Normalize spacing, punctuation
    dep = re.sub(r"[^a-z0-9\s]", " ", dep)
    dep = re.sub(r"\s+", " ", dep).strip()

    # --- Keyword-driven generic clustering ---
    if re.search(r"\bfree|bench|available\b", dep):
        return "FR", "Free / Available"
    if re.search(r"\bbill|cust|client\b", dep):
        return "BIL", "Billable / Client Project"
    if re.search(r"\bbackup|support\b", dep):
        return "BK", "Support / Backup"
    if re.search(r"\bshadow\b", dep):
        return "SH", "Shadow / Learning"
    if re.search(r"\brand|r d\b|research\b", dep):
        return "RD", "R&D / Internal"
    if re.search(r"\bbudget\b|planned|bu\b", dep):
        return "BU", "Budgeted / Planned"
    if re.search(r"\bmarket|business|sales\b", dep):
        return "MK", "Business / Marketing"
    if re.search(r"\btrain|intern\b", dep):
        return "TR", "Training / Trainee"

    # Fallback → first 3 uppercase chars
    return _make_code(raw_dep, 3).upper(), raw_dep.title()


def _infer_tech_group(role_raw: str, dept_raw: str, skills_norm: List[str]) -> str:
    """
    Infer tech group dynamically from designation, department, and normalized skills.
    No hardcoded mapping — pattern clusters only.
    """
    role = (role_raw or "").lower()
    dept = (dept_raw or "").lower()
    skill_text = " ".join(skills_norm).lower()

    # Predefined keyword clusters (non-exhaustive, flexible)
    backend_kw = ["backend", "back end", "server", "api", "spring", "java", "python", "dotnet", ".net", "node"]
    frontend_kw = ["frontend", "front end", "ui", "react", "angular", "vue"]
    mobile_kw = ["android", "ios", "flutter", "kotlin", "swift"]
    cloud_kw = ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "terraform"]
    fullstack_kw = ["full stack", "fullstack"]
    db_kw = ["database", "sql", "mysql", "postgres", "db", "dba"]
    ml_kw = ["ml", "machine learning", "ai", "data", "nlp"]
    hr_kw = ["hr", "payroll", "recruitment", "hiring"]

    text_blob = f"{role} {dept} {skill_text}"

    def has_any(keywords): return any(k in text_blob for k in keywords)

    # --- Logic priority ---
    if has_any(fullstack_kw):
        return "FullStack"
    if has_any(backend_kw):
        # pick dominant backend language if available
        if "java" in text_blob: return "Backend-Java"
        if "python" in text_blob: return "Backend-Python"
        if "dotnet" in text_blob or ".net" in text_blob: return "Backend-DotNet"
        if "node" in text_blob: return "Backend-NodeJS"
        return "Backend-General"
    if has_any(frontend_kw):
        if "angular" in text_blob: return "Frontend-Angular"
        if "react" in text_blob: return "Frontend-React"
        return "Frontend-General"
    if has_any(mobile_kw):
        if "android" in text_blob: return "Android"
        if "ios" in text_blob: return "iOS"
        return "Mobile"
    if has_any(cloud_kw):
        return "CloudOps"
    if has_any(db_kw):
        return "Backend-DB"
    if has_any(ml_kw):
        return "AI-ML"
    if has_any(hr_kw):
        return "HR-Cloud"

    return "General"


def _employee_numeric_id(full_id: str) -> str:
    if not full_id: return "X"
    return full_id.replace("VVDN/", "")

class CompressionService:
    def __init__(self):
        self.employee_repo = EmployeeRepository()
        self.project_repo  = ProjectRepository()
        self.codebook      = codebook_service

    async def _load_codebooks(self):
        return await self.codebook.get()

    async def generate_compression(self, employee: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create compression with strict DEP_DETAIL formatting:
        CODE:OCCUPANCY:CUSTOMER
        Internal project detection overrides CODE to IN.
        All skills_norm are included in compact.
        """
        try:
            dept_cb, loc_cb, role_cb, dep_cb = await self._load_codebooks()
        except Exception:
            dept_cb, loc_cb, role_cb, dep_cb = {}, {}, {}, {}

        emp_id_full = employee.get("employee_id", "")
        emp_id = _employee_numeric_id(emp_id_full)

        # Codes
        dept_raw = (employee.get("employee_department") or "").strip()
        loc_raw = (employee.get("emp_location") or "").strip()
        role_raw = (employee.get("designation") or "").strip()

        D = dept_cb.get(dept_raw, _make_code(dept_raw))
        L = loc_cb.get(loc_raw, _make_code(loc_raw, 3))
        R = role_cb.get(role_raw, _make_code(role_raw))

        # Experience
        total_exp_str = employee.get("total_exp", "")
        vvdn_exp_str = employee.get("vvdn_exp", "")

        total_exp = _parse_exp(total_exp_str)
        vvdn_exp = _parse_exp(vvdn_exp_str)

        if (not total_exp_str) or total_exp < 0.9 or total_exp_str.strip().upper().startswith("0Y"):
            exp_years = vvdn_exp
        else:
            exp_years = total_exp

        X = f"{exp_years:.1f}"

        # Projects
        projects = self.project_repo.get_projects_by_employee(emp_id_full) or []

        dep_codes = []
        dep_occ_map = {}
        non_free_count = 0
        details = []

        for p in projects:
            raw_dep = (p.get("deployment") or "").strip()
            customer = (p.get("customer") or "").strip()
            occ = int(p.get("occupancy") or 0)

            d_code, _ = _normalize_deployment(raw_dep)

            # Normalize customer for LLM
            cust_norm = re.sub(r"[^A-Za-z0-9]", "", customer).upper()[:20] or "UNK"

            # FINAL INTERNAL PROJECT DETECTION
            is_internal = ("VVDN" in cust_norm) or ("INTERNAL" in cust_norm)

            if is_internal and d_code != "FR":
                d_code = "IN" 

            dep_codes.append(d_code)
            dep_occ_map[d_code] = dep_occ_map.get(d_code, 0) + occ

            if not is_internal and "free" not in raw_dep.lower():
                non_free_count += 1

            details.append(f"{d_code}:{occ}:{cust_norm}")

        # Department summary code
        if not dep_codes:
            DEP = "UK"
        else:
            uniq_codes = sorted(set(dep_codes))
            if len(uniq_codes) == 1:
                DEP = uniq_codes[0]
            elif len(uniq_codes) == 2:
                DEP = "-".join(uniq_codes)
            else:
                DEP = "MIX"

        P = str(non_free_count)
        DEP_DETAIL = ";".join(details)

        # Skills
        skills_norm = _normalize_skills(employee.get("skill_set", ""))

        tech_group_raw = employee.get("tech_group", "").strip()
        tech_group = tech_group_raw if tech_group_raw else "General"

        # FULL skill list
        SK_part = ",".join(skills_norm)

        compact = (
            f"{emp_id}|{R}|{tech_group}|{L}|{X}|{P}|{D}|"
            f"{DEP}|{DEP_DETAIL}|{SK_part}"
        )

        return {
            "employee_id": emp_id_full,
            "id": emp_id,
            "compact": compact,
            "skills_norm": skills_norm,
            "role_code": R,
            "dept_code": D,
            "loc_code": L,
            "exp": X,
            "proj_count": P,
            "dep_summary": DEP,
            "dep_detail": DEP_DETAIL,
            "tech_group": tech_group,
            "updated_at": int(time.time())
        }


    async def update_compression(self, employee_id: str) -> bool:
        emp = self.employee_repo.get_employee_by_id(employee_id)
        if not emp: return False
        payload = await self.generate_compression(emp)
        await cache_manager.set(f"compression:{payload['id']}", payload)
        await cache_manager.sadd("comp:ids", payload["id"])
        logger.info(f"Updated compression for {payload['id']}")
        return True

    async def get_compressed_batch(self, ids: List[str]) -> List[Dict[str, Any]]:
        out=[]
        for emp_id in ids:
            cached = await cache_manager.get(f"compression:{emp_id}")
            if cached:
                out.append(cached)
                continue
            # fallback to DB and on-the-fly build
            full = self.employee_repo.get_employee_by_id(f"VVDN/{emp_id}") or \
                   self.employee_repo.get_employee_by_id(emp_id)
            if not full: continue
            payload = await self.generate_compression(full)
            await cache_manager.set(f"compression:{payload['id']}", payload)
            await cache_manager.sadd("comp:ids", payload["id"])
            out.append(payload)
        return out

    async def rebuild_cache(self) -> int:
        # 1) rebuild codebooks first
        await self.codebook.rebuild()

        # 2) clear only compression keys
        await self._clear_compression_keys_only()

        employees = self.employee_repo.get_all_employees() or []
        count = 0
        bulk = []
        for e in employees:
            payload = await self.generate_compression(e)
            bulk.append(("compression:"+payload["id"], payload))
            count += 1
        # store
        for k, v in bulk:
            await cache_manager.set(k, v)
        await cache_manager.delete("comp:ids")
        for _, v in bulk:
            await cache_manager.sadd("comp:ids", v["id"])

        # (Optional) don't store a giant "all_compressed_employees" blob — too big.
        logger.info(f"✅ Compression cache rebuilt for {count} employees")
        return count

    async def _clear_compression_keys_only(self) -> bool:
        try:
            if not cache_manager.is_available():
                return False
            rc = getattr(cache_manager.cache, "redis_client", None)
            if not rc:
                return await cache_manager.clear()
            async for key_batch in rc.scan_iter(match="compression:*", count=500):
                await rc.delete(*key_batch)
            await cache_manager.delete("comp:ids")
            return True
        except Exception as e:
            logger.error(f"Error clearing compression keys: {e}")
            return False

# Global instance
compression_service = CompressionService()