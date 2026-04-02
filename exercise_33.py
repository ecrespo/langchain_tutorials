import sqlite3
import pandas as pd
from langchain_core.messages.ai import AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Load environment variables from both .env and .env.local
load_dotenv()

db_path = "data/hotels.db"
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")


# Extract table information from the database
db_info = db.get_table_info()
print(db_info)