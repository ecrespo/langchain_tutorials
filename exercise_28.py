from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
import os

# Using an older lighter model to make it easier to demonstrate
model = init_chat_model("claude-haiku-4-5-20251001", model_provider="anthropic")


def get_response(prompt_str):
    prompt_template = PromptTemplate.from_template(prompt_str)
    prompt = prompt_template.format()
    response = model.invoke(prompt)
    return response.text


# -----NEW CODE-----#

# Without Role
prompt_str = f""" Is this equation solved correctly below?
2x - 3 = 9
2x = 6
x = 3
"""
print("WITHOUT ROLE")
print(get_response(prompt_str))
print("---------")

# With Role
prompt_str = f"""
You are a thoughtful mathematician. Especially gifted at methodically 
solving equations.
Is this equation solved correctly below?
2x - 3 = 9
2x = 6
x = 3
"""
print("WITH ROLE")
print(get_response(prompt_str))

