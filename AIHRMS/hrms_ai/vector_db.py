# import chromadb
# from chromadb.config import Settings

# client = chromadb.Client(
#     Settings(
#         persist_directory="./vector_db",  # folder to store the DB
#         chroma_db_impl="duckdb+parquet"   # implementation type
#     )
# )

# # Create or get a collection for employees
# collection = client.get_or_create_collection(name="employees")

# def add_employee_embedding(emp_id, embedding, metadata):
#     collection.add(
#         ids=[str(emp_id)],
#         embeddings=[embedding],
#         metadatas=[metadata]
#     )

# def search_employee(query_embedding, top_k=5):
#     results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
#     return results


# Example: Using Chroma
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./vector_db"))

collection = client.get_or_create_collection(name="employees")
collection.add(
    documents=[emp["name"] + " " + emp["skills"] for emp in employees],
    metadatas=[{"id": emp["id"], "department": emp["department"]} for emp in employees],
    ids=[str(emp["id"]) for emp in employees]
)
