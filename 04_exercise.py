from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from devtools import pprint
import os
from dotenv import load_dotenv
load_dotenv()


class Opinion(BaseModel):
    topic: str = Field(description="The topic of the opinion")
    sentiment: str = Field(description="The sentiment of the opinion")
    problem: Optional[str] = Field(description="The problem of the opinion, if any.")
    suggested_solution: Optional[str] = Field(
        description="The suggested solution of the opinion, if any."
    )


class StructuredReview(BaseModel):
    review_id: str = Field(description="The ID of the review", pattern=r"^R\d{5}$")
    overall_sentiment: str = Field(description="The sentiment of the review")
    notable_phrases: list[str] = Field(description="The notable phrases of the review")
    opinions: list[Opinion] = Field(description="The opinions of the review")


llm = init_chat_model(model="gpt-4.1-mini", temperature=0)


review_text = """
review_id: R12345
date: 2025-01-01
rating: ★★★☆☆ (3 stars)
text: I love the discount program in this app - saved 30% on my last order! However, the search functionality is really frustrating. Results are rarely relevant to what I’m looking for. They should implement category filters and improve their search algorithm.
"""

prompt = f"Extract structured data from this review:\n{review_text}"




# Create a structured LLM that returns validated Pydantic objects
structured_llm = llm.with_structured_output(StructuredReview)


# This is the schema that gets sent to the LLM
# pprint(StructuredReview.model_json_schema())

# Invoke and get a validated Pydantic object directly
structured_review = structured_llm.invoke(prompt)

pprint(structured_review)

# Access fields directly
print(f"\nReview ID: {structured_review.review_id}")
print(f"Sentiment: {structured_review.overall_sentiment}")
print(f"Number of opinions: {len(structured_review.opinions)}")


