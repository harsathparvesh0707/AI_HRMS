from ..core.database import get_db_session
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from ..services.ai_search_service import AISearchService
import logging, asyncio, json


logger = logging.getLogger(__name__)
search_service = AISearchService()


class ProjectRequirementSuggestion:
    def __init__(self):
        pass

    async def add_project_requirement(self, request):
        try:
            logger.info("Inserting data into Project Requirements...")
            with get_db_session() as session:
                result = session.execute(text("""
                    INSERT INTO project_requirements(project_name, requirements)
                    VALUES(:project_name, :requirements)
                    RETURNING id
                    """), 
                    {'project_name': request.project_name, "requirements": request.requirements}
                    )
                id = result.scalar()
                session.commit()
            logger.info("Data inserted...")
            return {
                "status": 200,
                "project_requirement_id": id,
                "detail": "New Project Requirement has been Added"
            }
        except Exception as e:
            logger.error(f"Error while inserting data into Project Requirements: {str(e)}") 
            raise

    async def process_requirement_suggestion(self, top_k: int = None, project_requirement_id: int = None):
        try:
            requirements = await self._get_all_project_requirements(project_requirement_id)
            if not requirements:
                logger.info("No Project Requirements Found")
                return {'status': 200, 'response': 'No Project Requirement Found'}
            all_results = []
            for requirement in requirements:
                project_name = requirement.get('project_name')
                requirement_text = requirement.get('requirements')
                if not requirement_text:
                    continue
                parsed_query = await search_service._cached_parse_query_simplified(requirement_text)
                logger.info(parsed_query)
                if search_service._is_effectively_empty(parsed_query):
                    continue
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
                    parsed_query.get('experience_max'),
                    parsed_query.get('project_duration_min_days'),
                    parsed_query.get('project_duration_max_days')
                ])
                merged_results = (await search_service.hybrid_engine._sql_search_loose_simplified(parsed_query)) if has_structured_filters else (await search_service.hybrid_engine._vector_search(requirement_text))
                employee_data_list = [
                    r["employee_data"] for r in merged_results if "employee_data" in r
                ]
                enriched = await search_service._get_or_compress_employees(employee_data_list, parsed_query)
                logger.info(f"🧠 Prepared {len(enriched)} compressed employees for ranking.")

                employee_data_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
                pre_ranked, llm_candidates = search_service.ranking_service.pre_rank_employees_simplified(
                    query=requirement_text,
                    parsed_query=parsed_query,
                    employees=enriched,
                    employee_data_lookup=employee_data_lookup,
                )
                logger.info(
                    f"🧮 Pre-ranking result: {len(pre_ranked)} employees pre-ranked without LLM, "
                    f"{len(llm_candidates)} employees will go through LLM PDP ranking."
                )
                try:
                    tasks = []
                    
                    if pre_ranked:
                        logger.info("🧠 Sending Python pre-ranked employees to LLM for reasoning + score refinement...")
                        tasks.append(search_service.ranking_service.llm_generate_reason_and_scores(pre_ranked))
                    else:
                        async def empty_pre_ranked():
                            return []
                        tasks.append(empty_pre_ranked())
                    
                    if llm_candidates:
                        logger.info(f"🧠 Starting LLM PDP ranking for {len(llm_candidates)} candidates...")
                        tasks.append(search_service.ranking_service.llm_rank_candidates_simplified(
                            requirement_text, parsed_query, llm_candidates, top_k
                        ))
                    else:
                        async def empty_llm_ranked():
                            return []
                        tasks.append(empty_llm_ranked())
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"❌ Error in LLM task {i}: {result}")
                            if i == 0 and pre_ranked:
                                pre_ranked_processed = pre_ranked
                                logger.warning("⚠️ Using pre-ranked employees without LLM refinement due to error")
                            elif i == 1 and llm_candidates:
                                llm_ranked = []
                                logger.warning("⚠️ LLM ranking failed, no LLM-ranked employees will be included")
                        else:
                            if i == 0:
                                pre_ranked_processed = result
                                logger.info(f"✅ LLM refinement completed for {len(pre_ranked_processed)} pre-ranked employees")
                            else:
                                llm_ranked = result
                                logger.info(f"✅ LLM PDP ranking completed for {len(llm_ranked)} employees")
                    
                except Exception as e:
                    logger.error(f"❌ Parallel LLM processing error: {e}")
                    if pre_ranked:
                        pre_ranked_processed = pre_ranked
                    llm_ranked = []
                
                final_ranked = pre_ranked_processed + llm_ranked

                employee_lookup = {emp.get("employee_id"): emp for emp in employee_data_list}
                ranked_with_details = []

                for ranked_emp in final_ranked:
                    emp_id = ranked_emp.get("employee_id")
                    if emp_id in employee_lookup:
                        full_emp_data = employee_lookup[emp_id].copy()

                        for f in ['pm', 'deployments', 'selection_reason']:
                            full_emp_data.pop(f, None)

                        full_emp_data['projects'] = search_service.ranking_service._get_employee_projects(emp_id)

                        full_emp_data.update({
                            "ranked_by": ranked_emp.get("ranked_by"),
                            "ai_score": ranked_emp.get("ai_score"),
                            "ai_reason": ranked_emp.get("ai_reason"),
                            "ai_tier": ranked_emp.get("ai_tier"),
                            "ai_criteria": ranked_emp.get("ai_criteria", {})
                        })
                        ranked_with_details.append(full_emp_data)

                ranked_with_details.sort(
                    key=lambda x: (x.get('ai_tier', 4), -x.get('ai_score', 0))
                )
                await self._insert_update_suggestion_details(project_name, requirement_text, ranked_with_details)
                all_results.append({
                    'project_name': project_name,
                    'requirement': requirement_text,
                    'response': ranked_with_details
                })
            if project_requirement_id is not None:
                return {'status': 200, 'response': all_results}
            return

        except Exception as e:
            logger.error(f"Error while processing requirement suggestion API: {str(e)}")
            raise

    async def _get_all_project_requirements(self, project_requirement_id: int = None):
        try:
            with get_db_session() as session:
                query = """
                SELECT 
                    pr.*, 
                    p.customer
                FROM project_requirements pr
                LEFT JOIN projects p 
                    ON pr.project_name = p.project_name"""
                params = {}
                if project_requirement_id:
                    query += " WHERE id = :id"
                    params['id'] = project_requirement_id
                query += " ORDER BY created_at"
                result = session.execute(text(query), params)
                return result.mappings().all()
        except Exception as e:
            logger.error(f"Error while fetching data from Requirements DB: {str(e)}")
            raise

    async def _insert_update_suggestion_details(self, project_name: str, requirement_text: str, suggestions):
        try:
            with get_db_session() as session:
                result = session.execute(text("SELECT id FROM project_requirements WHERE project_name = :project_name AND requirements = :requirement LIMIT 1"),
                    {'project_name': project_name, 'requirement': requirement_text}    
                ).fetchone()
                
                if not result:
                    raise ValueError("Project requirement not found")
                project_requirement_id = result[0]

                existing = session.execute(text("SELECT id FROM project_requirement_suggestions WHERE project_requirement_id = :project_requirement_id"),
                    {'project_requirement_id': project_requirement_id}
                ).fetchone()

                if existing:
                    session.execute(text("""
                        UPDATE project_requirement_suggestions
                        SET suggestion = :suggestion,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE project_requirement_id = :project_requirement_id
                    """), {
                        "suggestion": json.dumps(jsonable_encoder(suggestions)),
                        "project_requirement_id": project_requirement_id
                    })
                else:
                    session.execute(text("""
                        INSERT INTO project_requirement_suggestions 
                        (project_requirement_id, suggestion)
                        VALUES (:project_requirement_id, :suggestion)
                    """), {
                        "project_requirement_id": project_requirement_id,
                        "suggestion": json.dumps(jsonable_encoder(suggestions))
                    })
                session.commit()
            return
        except Exception as e:
            logger.error(f"Error while saving suggestion in DB: {e}")
            raise

    async def _get_all_project_suggestions(self, project_requirement_id = None):
        with get_db_session() as session:
            params = {}
            query = """
                SELECT 
                    pr.project_name,
                    pr.requirements,
                    prs.suggestion::json
                FROM project_requirements pr
                INNER JOIN project_requirement_suggestions prs
                    ON pr.id = prs.project_requirement_id
            """
            if project_requirement_id is not None:
                query += " WHERE pr.id = :id"
                params["id"] = project_requirement_id
            query += " ORDER BY pr.created_at DESC;"
            result = session.execute(text(query), params).mappings().all()
        return {'status': 200, 'response': result}
    
    async def _get_requirement_by_id(self, id: int):
        with get_db_session() as session:
            result = session.execute(text("SELECT * FROM project_requirements WHERE id = :id"), {'id': id}).mappings().fetchone()
            return dict(result) if result else None
        
    async def _update_project_requirement(self, id: int, update_data):
        existing = await self._get_requirement_by_id(id)
        if existing is None:
            return {'status_code': 400, 'response': 'No Requirement Found for this Id'}
        with get_db_session() as session:
            session.execute(text("""
                UPDATE project_requirements
                SET project_name = :project_name,
                    requirements = :requirements,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """), {"project_name": update_data.project_name, "requirements": update_data.requirements, "id": id})
            session.commit()
        return {'status_code': 200, 'response': 'Requirement Updated Successfully'}
    
    async def _delete_project_requirement(self, id: int):
        existing = await self._get_requirement_by_id(id)
        if existing is None:
            return {'status_code': 400, 'response': 'No Requirement Found for this Id'}
        with get_db_session() as session:
            session.execute(text("DELETE FROM project_requirement_suggestions WHERE project_requirement_id = :id"), {'id': id})
            session.execute(text("DELETE FROM project_requirements WHERE id = :id"), {'id': id})
        return {'status_code': 200, 'response': 'Requirement Deleted Successfully'}
    
    async def _get_requirements_by_project_name(self, project_name: str):
        with get_db_session() as session:
            result = session.execute(text("SELECT * FROM project_requirements WHERE project_name = :project_name"), {"project_name": project_name}).mappings().all()
        return {'status_code': 200, 'response': result}