from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize the LLM
llm = Ollama(model="qwen2:0.5b")  

# Enhanced HR-aware prompt
prompt_template = PromptTemplate(
    input_variables=["query"],
    template="""
You are an HR assistant. Convert this natural language query into a database-friendly form.
Return:
- SQL query only
- Relevant fields
- UI actions
- Short chat response

Query: {query}
Format:
SQL: ...
Fields: ...
UI_actions: ...
Chat_response: ...


1. **Understanding Queries**
   - Interpret natural language queries from users.
   - Recognize references to employee attributes, departments, status, roles, or other HR metadata.
   - Identify when a query is general (semantic) or specific (structured).

2. **Generating Structured Queries**
   - Convert natural language into:
     - SQL queries for the HRMS relational database, OR
     - Semantic queries (vector embeddings) for Vector Database retrieval.
   - Ensure queries accurately map to HRMS fields.
   - Example:
     - User: "Who all are in free pool?"
     - Output (SQL): `SELECT id, name, status FROM employees WHERE status='free_pool';`
     - Vector DB embedding: semantic representation of the query.

3. **Retrieving Data**
   - Retrieve data from HRMS DB or Vector DB as required.
   - Handle cases where multiple records match the query.
   - Ensure sensitive information is not exposed unnecessarily.
"""
)

# Create a chain
chain = LLMChain(llm=llm, prompt=prompt_template)

def process_query(user_query: str):
    response = chain.run(query=user_query)
    
    # Simple parsing of LLM output (assumes LLM returns in exact format)
    lines = response.split("\n")
    sql = lines[0].replace("SQL:","").strip()
    fields = [f.strip() for f in lines[1].replace("Fields:","").split(",")]
    ui_actions = [a.strip() for a in lines[2].replace("UI_actions:","").split(",")]
    chat_response = lines[3].replace("Chat_response:","").strip()
    
    return sql, fields, ui_actions, chat_response