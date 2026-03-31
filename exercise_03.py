from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import gradio as gr
load_dotenv()




def get_response(prompt_template_str, review):
    prompt_template = PromptTemplate.from_template(prompt_template_str)
    prompt = prompt_template.format(review=review)
    response = llm.invoke(prompt)
    return response.text


llm = init_chat_model("gpt-4o-mini")

# Define the Prompt Template
prompt_template_str = """
Given the following review:
{review}
Extract the following attributes from this review:
- The overall sentiment of the review (positive, negative, mixed)
- Notable phrases that capture key feedback
- Individual opinions on specific topics, each with:
  - The topic being discussed
  - The sentiment toward that topic
  - Any problem reported
  - Any solution suggested
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

# Get the model's response for the review
response_content = get_response(prompt_template_str, review_str)
print(response_content)

