from ..config.settings import settings
import google.generativeai as genai
from ..services.hybrid_search_engine import HybridSearchEngine
from ..core.database import get_db_session
from sqlalchemy import text
import re, json, logging

logger = logging.getLogger(__name__)

class AiAnalytics:
    """
    AI-powered HRMS analytics SQL generator.
    Uses Gemini model to convert natural language queries into structured SQL + chart metadata.
    """

    SCHEMA = """
        Database Schema:

        Table: employees
        - employee_id (varchar, primary key)
        - display_name (varchar)
        - employee_department (varchar)
        - tech_group (varchar)
        - emp_location (varchar)
        - total_exp (varchar)
        - vvdn_exp (varchar)
        - rm_id (varchar)
        - designation (varchar)
        - skill_set (varchar)
        - committed_relieving_date (date)

        Table: employee_projects
        - id (integer, primary key)
        - employee_id (varchar, foreign key -> employees.employee_id)
        - project_name (varchar)
        - project_department (varchar)
        - customer (varchar)
        - project_joined_date (date)
        - project_industry (varchar)
        - project_status (varchar)
        - occupancy (integer)
        - project_committed_end_date (date)
        - deployment (varchar)
        """

    BUSINESS_RULES = """
        Business Logic Rules:

        1. Projects with project_name containing 'FREE' are NOT real projects.
        - They represent the employee's free (unallocated) percentage.
        - occupancy in FREE project = percentage of free capacity.
        - If FREE occupancy = 100 implies employee is fully free.

        2. Projects with project_name containing 'TRNG' represent training.
        - These are NOT billable projects.
        - They should not be counted as real project allocation unless explicitly requested.
        Do NOT assume specific designation words like "developer" exist unless present in data.

        3. If user refers to a skill (e.g., React, Python, Java), search in skill_set.
        4. If user refers to team/department (e.g., Backend, Frontend, Cloud), search in tech_group.
        5. If user refers to job title (Engineer, Manager, Director, Lead), search in designation.
        6. skill_set column is a comma-separated list of technical skills.
        7. employees.committed_relieving_date is the employee relieving date from project.
        8. employees.project_joined_date is the date employee joined the project.
        9. employee_projects.project_committed_end_date is the project end date.
        8. Do NOT filter designation using "developer".
        9. rm_id references employees.employee_id.
        10. Any token matching pattern ^[A-Za-z0-9]{4}_[A-Za-z0-9]{4}$ could be a project_name but still use LIKE '%' for filtering.
        11. total_exp and vvdn_exp format: "XY ZM" (e.g., 2Y 10M).
            For visualization or comparison:
            - Convert experience to total months:
            (years * 12 + months)
            - Use numeric conversion for bar charts.
        12. When user refers to "internal budgeted projects, Free, Trianee, BU Common, RandD Internal Budgeted, Customer Facing, R and D Shadow, Billable, etc..", filter using deployment ILIKE '%Internal Budgeted%'
            - Do NOT infer internal/billable using project_name or customer unless explicitly requested.
        """

    def __init__(self):
        self.hybrid_engine = HybridSearchEngine(gemini_api_key=settings.gemini_api_key)
        self.client = None

    def extract_json(text: str):
        if not text or not text.strip():
            raise ValueError("Empty response from AI model")

        # Extract first JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid JSON returned by AI: {text}")

        json_str = match.group(0)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing failed: {e}")
        

    def get_client(self):
        if self.client is None:
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key missing")
            self.client = genai.Client(api_key=settings.gemini_api_key)
        return self.client

    def validate_sql(self, query: str):
        FORBIDDEN_KEYWORDS = [
            "insert", "update", "delete", "drop",
            "truncate", "alter", "create"
        ]
        lower = query.lower().strip()

        # Only SELECT
        if not (lower.startswith("select") or lower.startswith("with")):
            raise ValueError("Only SELECT queries are allowed")

        # No multi-statements
        if ";" in lower[:-1]:
            raise ValueError("Multiple statements not allowed")

        # Block dangerous keywords
        for word in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{word}\b", lower):
                raise ValueError(f"Forbidden SQL keyword detected: {word}")

        # Force LIMIT if missing
        # if "limit" not in lower:
        #     query += " LIMIT 100"

        return query

    def _build_system_prompt(self, user_chart_type: str) -> str:
        preferred_chart = (
            user_chart_type
            if user_chart_type and user_chart_type != "None"
            else "None"
        )

        return f"""
            You are an expert HRMS analytics SQL generator.

            Database Engine: PostgreSQL 14

            {self.SCHEMA}

            {self.BUSINESS_RULES}

            User Preferred Chart: {preferred_chart}

            SQL Rules:
            - Generate ONLY SELECT queries.
            - Never generate INSERT, UPDATE, DELETE, DROP, ALTER.
            - Use strictly PostgreSQL-compatible syntax.
            - Use PostgreSQL-specific syntax and functions only.
            - NEVER use REGEXP_SUBSTR.
            - For regex extraction use:
                substring(column from 'regex').
            - Use COUNT(DISTINCT employee_id) for employee counts.
            - Use proper explicit JOIN when needed.
            - When using GROUP BY, include all non-aggregated selected columns.
            - For string filtering strcitly use pattern: column ILIKE '%'.
            - Never use exact equality (=) unless user explicitly says "exact match".
            - If user requests "top N", use ORDER BY <metric> DESC with LIMIT N.
            - Do NOT use backticks.
            - SQL must execute in PostgreSQL 14.

            Chart Type Decision Framework

            IMPORTANT:
            This framework is used ONLY when User Preferred Chart is "None".
            If User Preferred Chart is provided, it MUST be used
            unless technically impossible.

            ------------------------------------------------------

            card:
            - Exactly one row AND one numeric column.
            - No GROUP BY.
            - Used for KPI/single metric.

            line:
            - One time/date dimension
            - One numeric aggregate
            - Used strictly for time series.

            pie:
            - Exactly one categorical column
            - Exactly one numeric aggregate
            - Used for proportion/share
            - Not allowed for time series.

            scatter:
            - Exactly two numeric columns
            - No categorical dimension
            - No aggregation unless explicitly requested.

            radar:
            - One categorical column (required)
            - One numeric aggregate (required)
            - Optional second categorical column becomes radar series
            - Recommended when comparing <= 6 entities

            If chartType = "bar", you MUST follow this structure:

            There are ONLY three valid bar formats:

                Normal Bar:
                - One categorical column
                - One numeric aggregate
                - xAxis = categorical column (STRING)
                - yAxis = numeric column (STRING)
                - groupBy = null

                Multi-Metric Bar:
                - One categorical column
                - Two or more numeric metrics
                - xAxis = categorical column (STRING)
                - yAxis = ARRAY of metric column names
                - groupBy = null

                Grouped Bar (Segmented):
                - Two categorical columns
                - One numeric aggregate
                - xAxis = first categorical column (STRING)
                - groupBy = second categorical column (STRING)
                - yAxis = numeric column (STRING)

            Chart Type Enforcement Rule:

                If user explicitly requests a chart type,
                that chart type MUST be used,
                unless the dataset structure makes it impossible.

            Fallback Priority:
            1. Single aggregate → card
            2. Time series → line
            3. Ranking/comparison → bar
            4. Two numeric metrics (no aggregation) → scatter
            5. One categorical + one metric (filtered to <= 5 entities) → radar
            6. One category + multiple metrics → multi_bar
            7. Two categories + one metric → grouped_bar
            8. Proportion/share → pie
            9. Otherwise → table

            Output Rules:
            - Return ONLY valid raw JSON.
            - No explanations.
            - No markdown.
            - No commentary.
            - No extra fields.

            Return exactly:

            {{
            "sql": "...",
            "chartType": "bar|grouped_bar|multi_bar|scatter|line|pie|table|card",
            "xAxis": "...",
            "yAxis": "...",
            "title": "..."
            }}
            """

    def generate_sql(self, user_prompt: str, user_chart_type: str = None) -> str:
        """
        Generate SQL + chart metadata from natural language.
        """
        try:
            client = self.get_client()
            system_prompt = self._build_system_prompt(user_chart_type)
            full_prompt = f"{system_prompt}\nUser Request: {user_prompt}"
            # response = self.hybrid_engine.generate_sql(full_prompt)
            response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1
                    }
                )

            return response.text.strip()
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise
    
    async def execute_query(self, sql: str):
        try:
            with get_db_session() as session:
                rows = session.execute(text(sql))
            result = [dict(row._mapping) for row in rows]
            return result
        except Exception as e:
            raise
        
    
    async def ai_analytics_service(self, request):
        try:
            # 1️⃣ Generate SQL
            ai_response = self.generate_sql(request.prompt, request.chartType)
            logger.info(f"AI SQL Generation Response: {ai_response}")
            # Parse JSON safely
            parsed = json.loads(ai_response)

            sql = parsed["sql"]
            chart_type = parsed["chartType"]
            x_axis = parsed["xAxis"]
            y_axis = parsed["yAxis"]
            title = parsed["title"]

            # 2️⃣ Validate SQL
            safe_sql = self.validate_sql(sql)
            logger.info(f"Validated SQL Query: {safe_sql}")

            # 3️⃣ Execute
            data = await self.execute_query(safe_sql)

            logger.info("Returned data:",len(data))

            return {
                "chartType": chart_type,
                "xAxis": x_axis,
                "yAxis": y_axis,
                "title": title,
                "data": data
            }
        except Exception as e:
            logger.error(str(e))
            raise
