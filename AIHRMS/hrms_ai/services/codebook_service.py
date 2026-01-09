# services/codebook_service.py
import re
import json
import logging
from typing import Dict, List
from ..core.database import get_db_session
from sqlalchemy import text
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

def _make_code(name: str, max_len: int = 4) -> str:
    """Make short code from a phrase; ensures 2–4 ASCII uppercase"""
    if not name:
        return "NA"
    n = re.sub(r"[^A-Za-z0-9\s\-_/]", "", name).strip()
    # Try acronym of words first
    parts = re.split(r"[\s\-/]+", n)
    acronym = "".join(p[:1] for p in parts if p)[:max_len].upper()
    if len(acronym) >= 2:
        return acronym
    # Fallback: first letters + extra chars
    compact = re.sub(r"\s+", "", n)[:max_len].upper()
    return compact if compact else "NA"

def _dedupe_codes(names: List[str], max_len: int = 4) -> Dict[str, str]:
    """Generate unique codes for names, handling collisions"""
    code_map = {}
    used = set()
    for raw in names:
        base = _make_code(raw, max_len)
        code = base
        i = 1
        while code in used:
            i += 1
            code = (base[:max_len-1] + str(i))[:max_len]
        used.add(code)
        code_map[raw] = code
    return code_map

class CodebookService:
    """Dynamic codebook service for role/dept/location compression"""
    
    DEPT_KEY = "codebook:dept"
    LOC_KEY = "codebook:loc"
    ROLE_KEY = "codebook:role"
    DEPLOY_KEY = "codebook:deploy"

    async def rebuild(self) -> None:
        """Rebuild codebooks from current database values"""
        try:
            with get_db_session() as s:
                depts = [r[0] for r in s.execute(text("SELECT DISTINCT employee_department FROM employees WHERE employee_department IS NOT NULL")).fetchall()]
                locs = [r[0] for r in s.execute(text("SELECT DISTINCT emp_location FROM employees WHERE emp_location IS NOT NULL")).fetchall()]
                roles = [r[0] for r in s.execute(text("SELECT DISTINCT designation FROM employees WHERE designation IS NOT NULL")).fetchall()]
                deployments = [r[0] for r in s.execute(
                    text("SELECT DISTINCT deployment FROM employee_projects WHERE deployment IS NOT NULL")
                ).fetchall()]

            dept_map = _dedupe_codes(depts)
            loc_map = _dedupe_codes(locs, max_len=3)  # keep locations tighter
            role_map = _dedupe_codes(roles)
            dep_map = _dedupe_codes(deployments, max_len=3)


            await cache_manager.set(self.DEPT_KEY, dept_map)
            await cache_manager.set(self.LOC_KEY, loc_map)
            await cache_manager.set(self.ROLE_KEY, role_map)
            await cache_manager.set(self.DEPLOY_KEY, dep_map)


            logger.info(f"✅ Codebooks rebuilt: depts={len(dept_map)} locs={len(loc_map)} roles={len(role_map)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to rebuild codebooks: {e}")
            raise

    async def get(self):
        """Get all codebooks"""
        dept = await cache_manager.get(self.DEPT_KEY) or {}
        loc = await cache_manager.get(self.LOC_KEY) or {}
        role = await cache_manager.get(self.ROLE_KEY) or {}
        dep  = await cache_manager.get(self.DEPLOY_KEY) or {}
        return dept, loc, role, dep

# Global instance
codebook_service = CodebookService()