from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import gradio as gr
load_dotenv()

# Model: gpt-4o-mini | Provider: openai

template = """You are a professional resume writer. 
Given the following brief description of work experience, generate a polished, 
professional resume summary that highlights key achievements and skills.

Work experience description:
{experience}

Write a compelling professional summary (2-3 sentences) suitable for a resume:"""


prompt = PromptTemplate(
    input_variables=["experience"],
    template=template
)

model = init_chat_model("gpt-4o-mini", model_provider="openai")

experience_input = """
5 years as a backend developer working with Python and FastAPI, 
building REST APIs for fintech companies. Led a team of 3 developers 
and reduced API response time by 40%. For a senior backend engineering position
"""


def generate_resume_summary(experience_input:str)->str:
  formatted_prompt = prompt.format(experience=experience_input)
  response = model.invoke(formatted_prompt)

  return response.content


demo = gr.Interface(
    fn=generate_resume_summary,  # your function name
    inputs=[gr.Textbox(label="Enter work experience", lines=3)],
    outputs=[gr.Textbox(label="Professional Summary", lines=5)],
    flagging_mode="never",
    title="Resume Section Writer",
    description="Generate polished resume summaries from work experience"
)

demo.launch()