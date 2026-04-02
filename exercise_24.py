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


# Define evaluator model
class ConversationEval(BaseModel):
    task_completeness: float = Field(
        description="How well did the assistant complete the diet planning task? (0-1)"
    )
    task_completeness_explanation: str = Field(
        description="Explanation for the task completeness score"
    )
    medical_soundness: float = Field(
        description="Does the diet advice follow safe, evidence-based nutritional guidelines? (0-1)"
    )
    medical_soundness_explanation: str = Field(
        description="Explanation for the medical soundness score"
    )
    efficiency: float = Field(
        description="How efficiently did the assistant complete the task? (0-1)"
    )
    efficiency_explanation: str = Field(
        description="Explanation for the efficiency score"
    )
    coherence: float = Field(description="How coherent were the responses? (0-1)")
    coherence_explanation: str = Field(
        description="Explanation for the coherence score"
    )


def conversation_quality_evaluator(
        inputs: dict, outputs: dict, reference_outputs: dict = None
):
    """
    Evaluates the quality of a conversation using an LLM as judge.
    Returns scores for coherence, task completeness, and efficiency.
    """
    # Extract conversation from inputs
    conversation = inputs.get("conversation", [])

    # Format conversation for the prompt
    conversation_text = ""
    for msg in conversation:
        conversation_text += f"{msg['role'].upper()}: {msg['content']}\n\n"

    # Define the evaluation prompt
    evaluation_prompt = f"""
        Evaluate this diet planning assistant conversation on four criteria (0-1 scale):

        1. **Task Completeness**: How effectively does the assistant help create a personalized diet plan?
           - 1.0: Delivers a complete, personalized meal plan that addresses all user requirements
           - 0.5: Partial plan or missing key personalization elements
           - 0.0: Fails to produce a usable meal plan

        2. **Efficiency**: How efficiently does the assistant gather information and reach a solution?
           - 1.0: Gathers necessary information with minimal back-and-forth, no redundant questions
           - 0.5: Some unnecessary questions or repetition, but reaches the goal
           - 0.0: Excessive questions, significant repetition, or very inefficient process

        3. **Coherence**: How well does the assistant maintain context throughout the conversation?
           - 1.0: Perfectly remembers and builds upon all previous information
           - 0.5: Generally maintains context with occasional lapses
           - 0.0: Frequently forgets information or contradicts previous statements

        4. **Medical Soundness**: Does the diet advice follow safe, evidence-based nutritional guidelines?
           - 1.0: All recommendations are nutritionally sound and safe
           - 0.5: Mostly sound advice with minor questionable suggestions
           - 0.0: Contains potentially harmful or medically unsound recommendations

        Provide a score between 0.0 (poor) and 1.0 (excellent) for each criterion.
        For each score, provide a separate explanation justifying your rating.

        ---
        CONVERSATION:
        {conversation_text}
        """

    # Create the evaluator
    evaluator = create_llm_as_judge(
        model="gpt-4o",
        prompt=evaluation_prompt,
        continuous=True,
        feedback_key="conversation_eval",
        output_schema=ConversationEval,
    )

    # Run the evaluation
    eval_result = evaluator(inputs={"prompt": evaluation_prompt})

    # Convert the result to the format expected by LangSmith
    return [
        {
            "key": "task_completeness",
            "score": eval_result.task_completeness,
            "comment": eval_result.task_completeness_explanation,
        },
        {
            "key": "medical_soundness",
            "score": eval_result.medical_soundness,
            "comment": eval_result.medical_soundness_explanation,
        },
        {
            "key": "efficiency",
            "score": eval_result.efficiency,
            "comment": eval_result.efficiency_explanation,
        },
        {
            "key": "coherence",
            "score": eval_result.coherence,
            "comment": eval_result.coherence_explanation,
        },
    ]


# -----NEW CODE-----#


def empty_function(x):
    return None


# Initialize LangSmith client
client = Client()

# Load and format conversations
examples = load_conversations()
print(f"Loaded {len(examples)} conversations")

# Create LangSmith dataset
dataset_name = "Diet Assistant Conversations"
create_dataset(client, dataset_name, examples)

# Run evaluation with LLM-as-judge
results = evaluate(
    empty_function,
    data=dataset_name,
    evaluators=[conversation_quality_evaluator],
    experiment_prefix="Diet Assistant Evaluation",
)

results_df = results.to_pandas()

eval_summary_df = (
    results_df.agg(
        {
            "feedback.task_completeness": "mean",
            "feedback.medical_soundness": "mean",
            "feedback.efficiency": "mean",
            "feedback.coherence": "mean",
        }
    )
    .reset_index()
    .rename(columns={"index": "metric", 0: "score"})
)

print(eval_summary_df.to_markdown(index=False))

