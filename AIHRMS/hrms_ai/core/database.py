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
            # Create employees table in public schema (removed role, deployment, occupancy)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id VARCHAR(50) PRIMARY KEY,
                    display_name VARCHAR(255),
                    employee_ou_type VARCHAR(100),
                    employee_department VARCHAR(100),
                    delivery_owner_emp_id VARCHAR(50),
                    delivery_owner VARCHAR(255),
                    joined_date VARCHAR(50),
                    created_by_employee_id VARCHAR(50),
                    created_by_display_name VARCHAR(255),
                    pm VARCHAR(255),
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
                )
            """))
            
            # Remove redundant columns if they exist
            try:
                conn.execute(text("ALTER TABLE employees DROP COLUMN IF EXISTS role"))
                conn.execute(text("ALTER TABLE employees DROP COLUMN IF EXISTS deployment"))
                conn.execute(text("ALTER TABLE employees DROP COLUMN IF EXISTS occupancy"))
            except Exception as e:
                logger.info(f"Column removal info: {e}")

            conn.execute(text("""
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS committed_relieving_date DATE,
                ADD COLUMN IF NOT EXISTS extended_relieving_date DATE;
            """))
            
            # Create employee_projects table in public schema
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employee_projects (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(50) REFERENCES employees(employee_id),
                    project_name VARCHAR(255),
                    customer VARCHAR(255),
                    project_department VARCHAR(100),
                    project_industry VARCHAR(100),
                    project_status VARCHAR(100),
                    occupancy INTEGER DEFAULT 0,
                    start_date DATE,
                    end_date DATE,
                    role VARCHAR(100),
                    deployment VARCHAR(100),
                    project_extended_end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Add new columns to existing table if they don't exist
            conn.execute(text("""
                ALTER TABLE employee_projects 
                ADD COLUMN IF NOT EXISTS occupancy INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS start_date DATE,
                ADD COLUMN IF NOT EXISTS end_date DATE,
                ADD COLUMN IF NOT EXISTS role VARCHAR(100),
                ADD COLUMN IF NOT EXISTS deployment VARCHAR(100),
                ADD COLUMN IF NOT EXISTS project_extended_end_date DATE,
                ADD COLUMN IF NOT EXISTS project_committed_end_date DATE;
            """))
            
            # Create performance indexes for ultra-fast text search
            logger.info("📈 Creating performance indexes...")
            
            # Create trigram extension if not exists
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            
            # Create trigram indexes for fuzzy text search
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_skill_set_trgm ON employees USING gin (skill_set gin_trgm_ops)",
                "CREATE INDEX IF NOT EXISTS idx_tech_group_trgm ON employees USING gin (tech_group gin_trgm_ops)", 
                "CREATE INDEX IF NOT EXISTS idx_emp_location_trgm ON employees USING gin (emp_location gin_trgm_ops)",
                "CREATE INDEX IF NOT EXISTS idx_display_name_trgm ON employees USING gin (display_name gin_trgm_ops)",
                "CREATE INDEX IF NOT EXISTS idx_employee_department_trgm ON employees USING gin (employee_department gin_trgm_ops)",
                # Regular indexes for exact matches
                "CREATE INDEX IF NOT EXISTS idx_employee_id ON employees (employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_designation ON employees (designation)",
                # Project table indexes
                "CREATE INDEX IF NOT EXISTS idx_ep_employee_id ON employee_projects (employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_ep_deployment_trgm ON employee_projects USING gin (deployment gin_trgm_ops)",
                "CREATE INDEX IF NOT EXISTS idx_ep_project_name_trgm ON employee_projects USING gin (project_name gin_trgm_ops)"
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