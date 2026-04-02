import sqlite3
import pandas as pd
from langchain_core.messages.ai import AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Load environment variables from both .env and .env.local
load_dotenv()

db_path = "data/retrieval-augmented-generation/structured-retrieval/hotels.db"
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")


# Extract table information from the database
db_info = db.get_table_info()


generate_sql_prompt_template_str = """
You are a SQLite expert. Given the following database schema, generate a SQL query to answer the user's question.

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

## Database schema
{database_schema}

## User Query
{user_query}
"""


generate_sql_prompt = PromptTemplate(
    template=generate_sql_prompt_template_str,
    input_variables=["user_query"],
    partial_variables={"database_schema": db_info},
)

model = init_chat_model("openai:gpt-4o-mini")

user_query = "Looking for places to stay in Tokyo that have hot springs between March 3-10 next year"

# SQL Generation Chain
generate_sql = generate_sql_prompt | model

"""Although we can execute the query right away but nothing makes sure that it is valid syntax. This step is expected to fail."""

# -----NEW CODE-----#


def execute_sql(sql_query):
    """Execute SQL query and return results as DataFrame"""
    try:
        print(f"Executing SQL Query: {sql_query}")

        # Execute the query
        with sqlite3.connect(db_path) as conn:
            results = pd.read_sql_query(sql_query, conn)
            return results

    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()


# Knowledge Retrieval Chain
retrieve_knowledge = generate_sql | execute_sql

result = retrieve_knowledge.invoke({"user_query": user_query})

print(result)

