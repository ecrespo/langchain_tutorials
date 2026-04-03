from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Platform will handle these imports automatically:
from query_hotels import query_hotels
from calculate_cost import calculate_total_cost
from weather import get_weather
from book_room import book_room

load_dotenv()


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

        # Initialize LLM with MCP support and provider web search
        self.llm = init_chat_model(
            model="claude-sonnet-4-20250514",
            betas=["mcp-client-2025-04-04"],
            mcp_servers=mcp_servers,
        )

        # Configure provider's built-in web search
        claude_websearch = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }

        # Configure MCP toolset reference
        mcp_toolset = {
            "type": "mcp_toolset",
            "mcp_server_name": "time-mcp",
        }

        # Set up self-managed tools
        self.tools = {
            "query_hotels": query_hotels,
            "calculate_total_cost": calculate_total_cost,
            "get_weather": get_weather,
            "book_room": book_room,
            "web_search": claude_websearch,  # Provider tool
            "mcp_toolset": mcp_toolset,  # MCP tool
        }

        # Bind all tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools.values())
        self.messages = []

        # Read prompt from file
        with open("prompt2.md", "r") as f:
            system_prompt = f.read()

        self.messages.append(SystemMessage(content=system_prompt))

    def chat(self, message: str):
        # Keep track of tool call sequence
        self.current_sequence = []

        # Add user message
        self.messages.append(HumanMessage(content=message))

        # Loop to handle serial tool calls
        while True:
            # Get AI response
            response = self.llm_with_tools.invoke(self.messages)
            self.messages.append(response)

            if not response.tool_calls:
                # No more tools to call
                break

            # Process tool calls
            for tool_call in response.tool_calls:
                self.current_sequence.append(tool_call["name"])

                # Only process self-managed tools
                # Provider and MCP tools are handled automatically
                if tool_call["name"] in [
                    "query_hotels",
                    "calculate_total_cost",
                    "get_weather",
                    "book_room",
                ]:
                    tool = self.tools[tool_call["name"]]
                    tool_result = tool.invoke(tool_call)
                    self.messages.append(tool_result)

        # Store sequence for debugging
        self.tool_sequence = self.current_sequence

