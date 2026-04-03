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
        # Configure MCP server for time functionality
        mcp_servers = [
            {
                "type": "url",
                "url": "https://time-mcp-optima-teams-projects-bcf90879.vercel.app/mcp",
                "name": "time-mcp",
            }
        ]

        # Initialize LLM with MCP support
        self.llm = init_chat_model(
            model="claude-sonnet-4-20250514",
            betas=["mcp-client-2025-04-04"],
            mcp_servers=mcp_servers,
        )

        # Reference MCP toolset so the LLM can use MCP server tools
        mcp_toolset = {
            "type": "mcp_toolset",
            "mcp_server_name": "time-mcp",
        }
        self.llm = self.llm.bind_tools([mcp_toolset])
        self.messages = []

        self.system_prompt = """The MCP time server provides tools for 
        current time, timezone conversions, and date calculations. Use 
        these to time or time zone related requests. Be conversational and 
        helpful in your responses."""

        self.messages.append(SystemMessage(content=self.system_prompt))

    def chat(self, message: str):
        # Add user message
        self.messages.append(HumanMessage(content=message))

        # Get AI response
        response = self.llm.invoke(self.messages)
        self.messages.append(response)


# Test MCP time functionality
assistant = TravelAssistant()
# Test 1: Current time in different timezone
assistant.chat("I'm in Dubai, what's the current time in Tokyo?")
print("We have a total of", len(assistant.messages), "messages")
for msg in assistant.messages[:-1]:
    msg.pretty_print()
print("================ AI Message ================")
print(assistant.messages[-1].text)
print("================ System Tool Calls ================")
print(assistant.messages[-1].tool_calls)
print("================ Internal LLM Tool Calls ================")
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

