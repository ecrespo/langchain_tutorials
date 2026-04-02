import pandas as pd
from langchain_core.messages.ai import AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import csv

csv.field_size_limit(131072 * 10)

load_dotenv()


# (1) DOCUMENT LOADING

from langchain_community.document_loaders.csv_loader import CSVLoader

loader = CSVLoader(
    file_path="data/retrieval-augmented-generation/semantic-retrieval/podcast.csv",
    source_column="text",
    metadata_columns=["id", "guest", "title"],
)

docs = loader.load()

print(f"Loaded {len(docs)} documents")
print(f"\nFirst doc preview: {str(docs[0])[:300]}...")

