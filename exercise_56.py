from datetime import datetime, date
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from dotenv import load_dotenv
from devtools import pprint

load_dotenv()


# -----NEW CODE-----#


class TravelAssistant:
    def __init__(self):
        # Initialize LLM with provider's built-in web search
        self.llm = init_chat_model(
            "claude-sonnet-4-20250514", model_provider="anthropic"
        )

        # Note: In real implementation, you would enable provider tools like this:
        # self.llm = init_chat_model("gpt-4o-mini", tools=[{"type": "web_search"}])
        # For demo, we'll continue with our tools

        claude_websearch = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }

        self.tools = {
            "web_search": claude_websearch,
        }
        self.llm_with_tools = self.llm.bind_tools(self.tools.values())
        self.messages = []

        self.system_prompt = """You are a helpful travel assistant with 
        access to web search and hotel search capabilities. Use the 
        built-in web search to find current information about events 
        and locations. Then use other tools as needed to help with travel planning. Be conversational and helpful in your responses."""

        self.messages.append(SystemMessage(content=self.system_prompt))

    def chat(self, message: str):
        # Add user message
        self.messages.append(HumanMessage(content=message))

        # Get AI response
        response = self.llm_with_tools.invoke(self.messages)
        self.messages.append(response)


# Test with provider tools
assistant = TravelAssistant()
assistant.chat("When is the next Tokyo Marathon?")

print("We have a total of", len(assistant.messages), "messages")
for msg in assistant.messages[:-1]:
    msg.pretty_print()
print("================ AI Message ================")
print(assistant.messages[-1].text)
print("================ Tool Calls ================")
print(assistant.messages[-1].tool_calls)
print("=========== Internal LLM Tool Calls & Results =============")
print(
    "\n".join(
        [
            repr(
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "tool_use_id": d.get("tool_use_id"),
                    "type": d.get("type"),
                    "args": d.get("args"),
                }
            )
            for d in assistant.messages[-1].content
            if d["type"] != "text"
        ]
    )
)

