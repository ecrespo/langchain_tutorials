import sqlite3
import pandas as pd
from langchain_core.messages.ai import AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model

# Initialize components
db_path = "path/to/your/database.db"
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
schema_info = db.get_table_info()
model = init_chat_model("openai:gpt-4o-mini")

# Query generation prompt with partial variables
query_prompt = PromptTemplate(
    template="""You are a SQLite expert. Given the following database schema, generate a SQL query to answer the user's question.

Requirements:
- Output only the SQL query, no explanations or additional text
- Use proper SQLite syntax and features only
- Query for at most top k results using LIMIT clause unless a specific number is requested
- Order results to return the most informative data
- Only query columns that are needed to answer the question
- Wrap column names in double quotes (") as delimited identifiers
- Use only column names that exist in the schema below
- Pay attention to which column is in which table
- Use date('now') for current date when queries involve "today"
- Your current year is 2025

Query construction guidelines:
- Use appropriate joins between tables when needed
- Include all relevant filtering conditions
- Handle complex requirements including sorting, filtering, and aggregation
- Use subqueries or CTEs (Common Table Expressions) when appropriate
- Ensure queries are optimized for performance

### Database schema
{database_schema}

### User Query
{user_query}""",
    input_variables=["user_query"],
    partial_variables={"database_schema": schema_info}
)

# Response generation prompt
response_prompt = PromptTemplate(
    template="""Given the results of a database query and the original user query, create a user-friendly response following these guidelines:

1. Start with a brief acknowledgment of their request
2. Present the data in a natural, conversational way
3. Highlight key information with selective bold text
4. End with an offer to provide more information if needed

Original User Query: {user_query}

Database Query Results:
{data}

Please create a friendly, informative response:""",
    input_variables=["data"],
    partial_variables={"user_query": user_query}
)


# Helper functions
def clean_sql_query(sql_query: AIMessage) -> str:
    """Extract and clean SQL from model response."""
    return sql_query.text.replace("```sql", "").replace("```",
                                                           "").strip()


def validate_sql_query(sql_query: str) -> str:
    """Validate SQL query for safety."""
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
                          'INSERT', 'UPDATE']
    for keyword in dangerous_keywords:
        if keyword in sql_query.upper():
            raise ValueError(
                f"Query validation failed: {keyword} operations not allowed")
    return sql_query


def execute_sql(sql_query: str) -> pd.DataFrame:
    """Execute SQL query and return results."""
    try:
        print(f"Executing SQL Query: {sql_query}")
        with sqlite3.connect(db_path) as conn:
            results = pd.read_sql_query(sql_query, conn)
            return results
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()


def format_results_for_llm(results_df: pd.DataFrame) -> str:
    """Format query results for LLM consumption."""
    if results_df.empty:
        return "No results found"

    # Convert DataFrame to readable format
    return results_df.to_string(index=False)


# Main execution
user_query = "Your natural language query here"

# Build the RAG chains
# Retrieve Phase: Query generation → validation → execution
generate_sql = query_prompt | model
retrieve_knowledge = generate_sql | clean_sql_query | validate_sql_query | execute_sql

# Response Generation Chain: Format results → Generate response
generate_response = format_results_for_llm | response_prompt | model

# Complete RAG Pipeline
structured_rag = retrieve_knowledge | generate_response

# Execute the chain
result = structured_rag.invoke({"user_query": user_query})

print("============= RESULT =============")
print(result.text)
