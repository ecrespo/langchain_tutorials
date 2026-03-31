import datetime
import json
from devtools import pprint
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

load_dotenv()


# Define response schema
class Review(BaseModel):
    review_id: str = Field(description="The ID of the review", pattern=r"^R\d{5}$")
    rating: str = Field(
        description="The rating of the review",
        pattern=r"^★{1,5}☆{0,4} \(\d star(?:s)?\)$",
    )
    date: datetime.date = Field(
        description="The date of the review", format="YYYY-MM-DD"
    )
    text: str = Field(
        description="The text of the review", min_length=1, max_length=1000
    )


class Opinion(BaseModel):
    topic: str = Field(
        description="The topic of the opinion, one of (App Functionality, UI & UX, Payment & Checkout, Product Information, Order Operations, Customer Service)"
    )
    sentiment: str = Field(
        description="The sentiment of the opinion (positive, negative, neutral, or mixed)"
    )
    problem: Optional[str] = Field(
        default=None, description="The problem mentioned, if any"
    )
    suggested_solution: Optional[str] = Field(
        default=None, description="A suggested solution to the problem, if applicable"
    )


class StructuredReview(BaseModel):
    review_id: str = Field(description="The ID of the review")
    overall_sentiment: str = Field(
        description="The overall sentiment of the review (positive, negative, neutral, or mixed)"
    )
    notable_phrases: list[str] = Field(
        description="Notable phrases or quotes from the review"
    )
    opinions: list[Opinion] = Field(
        description="List of opinions expressed in the review"
    )


llm = init_chat_model(model="gpt-4.1-nano", temperature=0)

# Create a structured LLM that returns validated Pydantic objects
structured_llm = llm.with_structured_output(StructuredReview)


def get_response(prompt_template_str, review, format_instructions):
    prompt_template = PromptTemplate.from_template(prompt_template_str)
    prompt = prompt_template.format(
        review=review, format_instructions=format_instructions
    )
    response = structured_llm.invoke(prompt)
    return response


# Call the LLM to extract the structured review
def extract_structured_review(review_data):
    try:
        Review.model_validate(review_data)
    except ValidationError as e:
        print(f"Input validation error: {e}")
        print("Proceeding with extraction despite validation errors")

    format_instructions = StructuredReview.model_json_schema()

    # Define the prompt template
    prompt_template_str = """
Given the following review:
```
{review}
```

Convert it into a structured JSON object that conforms to the following schema:
{format_instructions}

Output the JSON object only, no other text or delimiters.
"""

    review_str = json.dumps(review_data, indent=4)
    structured_review = get_response(
        prompt_template_str, review_str, format_instructions
    )

    return structured_review


def load_examples():
    evaluation_dataset_path = "data/data_17.json"

    # Load the evaluation dataset
    with open(evaluation_dataset_path, "r", encoding="utf-8") as file:
        examples = json.load(file)

    return examples


# -----NEW CODE-----#
# Import LangSmith-related libraries
from langsmith import Client
from langsmith.evaluation import evaluate
from openevals.llm import create_llm_as_judge

client = Client()  # Initialize LangSmith client

dataset_name = "app_reviews_01"


if client.has_dataset(dataset_name=dataset_name):
    print(f"Using existing dataset: {dataset_name}")
else:
    # Create a new dataset if not found
    print(f"Creating new dataset: {dataset_name}")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Dataset for evaluating app review structured extraction",
    )

    examples = load_examples()
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"Dataset Created with {len(examples)} examples")

