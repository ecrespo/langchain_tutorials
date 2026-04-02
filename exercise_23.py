import sqlite3
import os
import json
from langsmith import Client, evaluate
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv
from pprint import pprint
from openevals.llm import create_llm_as_judge

load_dotenv()

# Constants
DB_PATH = "data/llm-application-evaluation/conversation-evaluation/chat_history.db"


def load_conversations():
    """Load conversations from SQLite DB and format for evaluation"""
    conversations = {}

    # Connect to DB and fetch conversations
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM message_store ORDER BY session_id, id")

    # Process results
    for row in cursor.fetchall():
        session_id = row[1]
        message_data = json.loads(row[2])

        # Skip system messages
        if message_data.get("type") == "system":
            continue

        # Initialize conversation list for this session if needed
        if session_id not in conversations:
            conversations[session_id] = []

        # Get content and role
        content = message_data.get("data", {}).get("content", "")
        role = "user" if message_data.get("type") == "human" else "assistant"

        conversations[session_id].append({"role": role, "content": content})

    # Format for LangSmith
    examples = []
    for messages in conversations.values():
        if len(messages) >= 2:  # Only include conversations with at least one exchange
            examples.append({"inputs": {"conversation": messages}})

    return examples


def create_dataset(client: Client, dataset_name: str, examples: List[Dict]):
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Using existing dataset: {dataset_name}")
    else:
        dataset = client.create_dataset(
            dataset_name, description="Evaluation dataset for conversation quality"
        )
        client.create_examples(
            inputs=[ex["inputs"] for ex in examples], dataset_id=dataset.id
        )
        print(f"Created new dataset: {dataset_name}")


# Initialize LangSmith client
client = Client()

# Load and format conversations
examples = load_conversations()
print(f"Loaded {len(examples)} conversations")

# Create LangSmith dataset
dataset_name = "Diet Assistant Conversations"
create_dataset(client, dataset_name, examples)

