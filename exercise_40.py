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


# -----NEW CODE-----#

# (2) SPLITTING WITHOUT OVERLAP

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

all_splits = text_splitter.split_documents(docs)

print(f"Created {len(all_splits)} chunks without overlap")
print(f"\nEnd of first chunk: ...{all_splits[0].page_content[-250:]}")
print(f"\nStart of second chunk: {all_splits[1].page_content[:250]}...")

