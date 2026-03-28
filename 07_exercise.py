from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()


def get_response(prompt_template_str, review):
    prompt_template = PromptTemplate.from_template(prompt_template_str)
    prompt = prompt_template.format(review=review)
    response = llm.invoke(prompt)
    return response.text


# Define the Prompt Template
prompt_template_str = """
Given the following review:
{review}
Convert the information in this review text into a structured JSON object.
Please include the sentiment of the review and any issues mentioned in the review.
Output the JSON object only, no other text or delimiters.
"""

# Define the review string
review_str = """
{
    "review_id": "R12345",
    "date": "2025-01-01",
    "rating": "★★★☆☆ (3 stars)",
    "text": "I love the discount program in this app - saved 30% on my last order! However, the search functionality is really frustrating. Results are rarely relevant to what I'm looking for. They should implement category filters and improve their search algorithm."
}
"""


# -----NEW CODE-----#

# Configure the LLM
llm = init_chat_model(
    model="gpt-4.1-nano",
    timeout=0.1,  # 100ms timeout
    max_retries=3,  # 3 retries
)

# Get the model's response for the review
response_content = get_response(prompt_template_str, review_str)
print(response_content)

