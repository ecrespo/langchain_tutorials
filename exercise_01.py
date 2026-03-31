from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import gradio as gr
load_dotenv()

prompt_template_str = """
Your task is to explain the concept of **{concept}** to me in a way that is:

1. Clear and intuitive
2. Concise (in under 100 words)
3. Tailored specifically to me and what I already know

Use the following information about me to personalize your explanations:

- Role: Lead Software Engineer
- Current Goal: Building a RAG (Retrieval-Augmented Generation) system

The personalization should be subtle and natural. Avoid forced references to my background that don't genuinely enhance my understanding of the concept.
"""

# Create a prompt template
prompt_template = PromptTemplate.from_template(prompt_template_str)
# Define the input variable
input_text = "Natural Language Processing"
# Create a model interface
model = init_chat_model("gpt-4o-mini", model_provider="openai")


def generate_explanation(input_text:str)->str:
  prompt = prompt_template.format(concept=input_text)
  response = model.invoke(prompt)
  return response.content



demo = gr.Interface(
    fn=generate_explanation,
    inputs=[gr.Textbox(label="Enter a concept", lines=1)],
    outputs=[gr.Textbox(label="Explanation", lines=5)],
    flagging_mode="never",
    title="Concept Explainer",
    description="Get personalized explanations for any concept"
)

demo.launch()
