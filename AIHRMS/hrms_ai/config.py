import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://user:password@localhost/hrms_db")
VECTOR_PATH = "./vector_db"
