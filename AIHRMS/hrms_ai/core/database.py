"""
Database connection and session management
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Generator

from ..config.settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator:
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database tables in public schema"""
    try:
        with engine.connect() as conn:
            logger.info("Database Initialization...")
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id VARCHAR(50) PRIMARY KEY,
                    display_name VARCHAR(255),
                    employee_ou_type VARCHAR(100),
                    employee_department VARCHAR(100),
                    total_exp VARCHAR(50),
                    vvdn_exp VARCHAR(50),
                    designation VARCHAR(100),
                    sub_department VARCHAR(100),
                    tech_group VARCHAR(100),
                    emp_location VARCHAR(100),
                    rm_id VARCHAR(50),
                    rm_name VARCHAR(255),
                    skill_set TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """))
            
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_name VARCHAR(50) PRIMARY KEY,
                    customer VARCHAR(255),
                    project_department VARCHAR(100),
                    project_industry VARCHAR(100),
                    project_status VARCHAR(50),
                    delivery_owner_emp_id VARCHAR(50),
                    delivery_owner VARCHAR(255),
                    pm VARCHAR(255),
                    project_category VARCHAR(255),
                    project_committed_end_date DATE,
                    project_extended_end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ))

            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS employee_projects (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(50) REFERENCES employees(employee_id),
                    project_name VARCHAR(50) REFERENCES projects(project_name),
                    project_joined_date DATE,
                    start_date DATE,
                    end_date DATE,
                    role VARCHAR(100),
                    deployment VARCHAR(100),
                    committed_relieving_date DATE,
                    extended_relieving_date DATE,
                    occupancy INTEGER DEFAULT 0,
                    created_by_employee_id VARCHAR(50),
                    created_by_display_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ))
            
            conn.execute(text("""CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_requirements (
                id SERIAL PRIMARY KEY,
                project_name VARCHAR(50) REFERENCES projects(project_name),
                requirements TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_requirement_suggestions (
                id SERIAL PRIMARY KEY,
                project_requirement_id INTEGER REFERENCES project_requirements(id),
                suggestion TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            """))

            logger.info("📈 Creating performance indexes...")

            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

            indexes = [
                # Employees
                    "CREATE INDEX IF NOT EXISTS idx_emp_skill_set_trgm ON employees USING gin (skill_set gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_emp_tech_group_trgm ON employees USING gin (tech_group gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_emp_location_trgm ON employees USING gin (emp_location gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_emp_display_name_trgm ON employees USING gin (display_name gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_emp_department_trgm ON employees USING gin (employee_department gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_emp_designation ON employees (designation)",
                # Projects
                    "CREATE INDEX IF NOT EXISTS idx_proj_customer_trgm ON projects USING gin (customer gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_proj_project_committed_end_date ON projects (project_committed_end_date)",
                    "CREATE INDEX IF NOT EXISTS idx_proj_project_extended_end_date ON projects (project_extended_end_date)",
                # Employee Projects
                    "CREATE INDEX IF NOT EXISTS idx_ep_employee_id ON employee_projects (employee_id)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_project_id ON employee_projects (project_name)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_employee_project ON employee_projects (employee_id, project_name)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_occupancy ON employee_projects (occupancy)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_deployment_trgm ON employee_projects USING gin (deployment gin_trgm_ops)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_joined_date ON employee_projects (project_joined_date)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_committed_relieving_date ON employee_projects (committed_relieving_date)",
                    "CREATE INDEX IF NOT EXISTS idx_ep_extended_relieving_date ON employee_projects (extended_relieving_date)"
                ]
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0]
                    logger.info(f"✅ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Index creation failed: {e}")

            conn.commit()
            logger.info("✅ Database tables and indexes initialized successfully")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise