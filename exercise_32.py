import datetime
import json
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from devtools import pprint

load_dotenv()


# Define response schema
class Opinion(BaseModel):
    topic: str = Field(
        description="The topic of the opinion, one of (App Functionality, UI & UX, Payment & Checkout, Product Information, Order Operations, Customer Service)"
    )
    sentiment: str = Field(
        description="The sentiment of the opinion (positive, negative, neutral, or mixed)"
    )
    problem: Optional[str] = Field(
        description="The problem mentioned, if any", default=""
    )
    suggested_solution: Optional[str] = Field(
        description="A suggested solution to the problem, if applicable", default=""
    )


class StructuredReview(BaseModel):
    review_id: str = Field(description="The ID of the review")
    overall_sentiment: str = Field(
        description="The overall sentiment of the review (positive, negative, neutral, or mixed)"
    )
    notable_phrases: list[str] = Field(
        description="Notable phrases or quotes from the review verbatim (max 3 phrases, each under 100 characters)"
    )
    opinions: list[Opinion] = Field(
        description="List of opinions expressed in the review"
    )


# Prompt Template String
prompt_template_str = """Given the following review:

{review}

Convert it into a structured JSON object that conforms to the following schema:

{output_structure}

Output the JSON object only, no other text or delimiters."""

# Review to process
review = {
    "review_id": "R73482",
    "rating": "★★★☆☆ (3 stars)",
    "date": "2025-01-15",
    "text": "Love the loyalty program and the easy checkout! But I have to re-enter my payment information every time, and the app is getting slower with each update.",
}

# Extract output structure from the Pydantic model
output_structure = StructuredReview.model_json_schema()

# Convert review to string format
review_str = json.dumps(review, indent=4)


# -----NEW CODE-----#

# Prompt Template
prompt = PromptTemplate(
    template=prompt_template_str,
    input_variables=["review"],
    partial_variables={"output_structure": output_structure},
)

# LLM with structured output
llm = init_chat_model(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(StructuredReview)

# Define Chain - simpler with structured output!
review_extraction_chain = prompt | structured_llm

# Execute the chain
structured_review = review_extraction_chain.invoke({"review": review_str})

# Let's look at the intermediate outputs:
print("\n\nINTERMEDIATE OUTPUTS:")

# Just the prompt
formatted_prompt = prompt.format(review=review_str)
print("\nFORMATTED PROMPT (first 200 chars):")
print(formatted_prompt[:200] + "...")

# Full chain result - returns Pydantic object directly
final_result = review_extraction_chain.invoke({"review": review_str})
print("\nLLM RESPONSE:")
print(final_result)
print("\nFINAL PARSED RESULT:")
print(f"Review ID: {final_result.review_id}")
print(f"Overall Sentiment: {final_result.overall_sentiment}")
print(f"Number of opinions: {len(final_result.opinions)}")

