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


# (2) SPLITTING WITH OVERLAP

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

all_splits = text_splitter.split_documents(docs)


# -----NEW CODE-----#

# (3) EMBEDDING, INDEXING & SAVING

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import random

embeddings = OpenAIEmbeddings()

# Sample a small subset of splits for faster processing
random.seed(42)
sample_size = min(100, len(all_splits))
sample_splits = random.sample(all_splits, sample_size)

# Embed the document chunks, index them, and save to a vector store
vector_store = FAISS.from_documents(sample_splits, embeddings)

vector_store.save_local("faiss_index.db")

results = vector_store.similarity_search("What is artificial intelligence?", k=5)
print(f"Found {len(results)} relevant chunks")
print(f"\nTop result preview: {results[0].page_content[:200]}...")
print(f"\n2nd result preview: {results[1].page_content[:200]}...")

