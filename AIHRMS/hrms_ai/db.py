import psycopg2
import psycopg2.extras

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    database="hrms",
    user="your_user",
    password="your_password"
)

def execute_query(sql_query: str):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql_query)
        results = cur.fetchall()
    return results
