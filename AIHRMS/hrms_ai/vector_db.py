import chromadb

# Use new ChromaDB client syntax
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="employees")

def add_employee_embedding(emp_id, embedding, metadata):
    collection.add(
        ids=[str(emp_id)],
        embeddings=[embedding],
        metadatas=[metadata]
    )

def search_employee(query_embedding, top_k=5):
    try:
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
        return results
    except:
        return {"ids": [], "documents": [], "metadatas": []}
