from langchain_community.vectorstores import FAISS
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# KNOWLEDGE RETRIEVAL

# Load the FAISS vector store
vector_store_path = "data/retrieval-augmented-generation/semantic-retrieval"

vector_store = FAISS.load_local(
    vector_store_path,
    embeddings=OpenAIEmbeddings(),
    allow_dangerous_deserialization=True,
)


# Function to retrieve knowledge from the vector store
def retrieve_knowledge(input: dict, k=10) -> dict:
    return {
        "context": vector_store.similarity_search(input["question"], k=k),
        "question": input["question"],
    }


# RESPONSE GENERATION

# Load prompt
with open("prompt.md", "r") as f:
    prompt_template_str = f.read()

# Create the prompt template
prompt = PromptTemplate(
    template=prompt_template_str, input_variables=["question", "context"]
)

# Initialize the model
model = init_chat_model(model="gpt-4o-mini")

# Generate the response
generate_response = prompt | model

# SEMANTIC RAG

# Retrieve knowledge then generate response
semantic_rag = retrieve_knowledge | generate_response

# Test pipeline
import textwrap

question = "What is artificial intelligence?"
result = semantic_rag.invoke({"question": question})
for line in result.text.split("\n"):
    print(textwrap.fill(line, width=80) if line.strip() else "")

