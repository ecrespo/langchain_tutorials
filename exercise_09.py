from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Define the system message
SYSTEM_MESSAGE = (
    "You are a diet planning assistant. Help users create balanced meal plans "
    "based on their goals, dietary needs, and preferences. Ask about one topic "
    "at a time to avoid overwhelming the user."
)

# Initialize the model
model = init_chat_model(model="gpt-4o-mini")

# Step 1: Define the system message
system_msg = SystemMessage(content=SYSTEM_MESSAGE)

# Step 2: Initialize the conversation list with system message
conversation = [system_msg]

# Step 3: Receive the user's message and append it to the conversation
user_msg = "Hello, I want to lose weight"
conversation.append(HumanMessage(content=user_msg))

# Step 4: Send the conversation to the model
response = model.invoke(conversation)

# Step 5: Get the response and append it to the conversation
conversation.append(AIMessage(content=response.text))

# Step 6: Display the conversation (return to user)
print("Conversation history:")
for msg in conversation:
    print("-" * 40)
    content = msg.text[:200] + "..." if len(msg.text) > 200 else msg.text
    print(f"{msg.__class__.__name__}: {content}")

