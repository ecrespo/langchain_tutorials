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
prompt_str = f"""
In one sentence, what do you think about skydiving?
"""
print("WITHOUT ROLE")
print(get_response(prompt_str))
print("---------")

# Mom Role
prompt_str = f"""
You are a mom. In one sentence, what do you think about skydiving?
"""
print("WITH ROLE: Mom")
print(get_response(prompt_str))
print("---------")

# Cat Role
prompt_str = f"""
You are a cat. In one sentence, what do you think about skydiving?
"""
print("WITH ROLE: Cat")
print(get_response(prompt_str))

