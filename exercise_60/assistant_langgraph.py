from typing import Annotated

from dotenv import load_dotenv
from IPython.display import Image, display
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from tools import (
    book_room,
    calculate_total_cost,
    claude_websearch,
    get_weather,
    query_hotels,
)
from typing_extensions import TypedDict
from utils import print_message

load_dotenv()

# SETUP

# Tool definitions
custom_tools = [
    query_hotels,
    calculate_total_cost,
    get_weather,
    book_room,
]
provider_tools = [claude_websearch]
mcp_toolset = {
    "type": "mcp_toolset",
    "mcp_server_name": "time-mcp",
}
all_tools = custom_tools + provider_tools + [mcp_toolset]

# MCP configuration
mcp_servers = [
    {
        "type": "url",
        "url": "https://time-mcp-optima-teams-projects-bcf90879.vercel.app/mcp",
        "name": "time-mcp",
    }
]

# LLM configuration
llm = init_chat_model(
    model="claude-sonnet-4-20250514",
    betas=["mcp-client-2025-04-04"],
    mcp_servers=mcp_servers,
)
llm_with_tools = llm.bind_tools(all_tools)

# Load system message once at setup time
with open("prompt2.md") as f:
    system_prompt = f.read()
system_message = SystemMessage(content=system_prompt)

# STATE DEFINITION


# Define state schema with messages using add_messages reducer
class State(TypedDict):
    """Define the state schema for our hotel assistant."""

    messages: Annotated[list[AnyMessage], add_messages]


# NODE DEFINITIONS


# Reasoning node that processes messages and makes decisions
def reason(state: State) -> dict:
    """Reasoning node: LLM analyzes the current context and decides what to do next."""
    # Combine system message with conversation messages
    messages = [system_message] + state["messages"]

    # Print the last message if it is a tool message
    if isinstance(messages[-1], ToolMessage):
        print_message(messages[-1])

    response = llm_with_tools.invoke(messages)
    # Print the response from the LLM
    print_message(response)
    return {"messages": [response]}


# Action node that executes tool calls
act = ToolNode(custom_tools)

# GRAPH CONSTRUCTION

# Build graph with nodes
hotel_assistant_builder = StateGraph(State)
hotel_assistant_builder.add_node("reason", reason)
hotel_assistant_builder.add_node("act", act)

# Define edges for the ReAct cycle
hotel_assistant_builder.add_edge(START, "reason")  # Start with reasoning
hotel_assistant_builder.add_conditional_edges(
    "reason",
    tools_condition,  # Conditionally route to tools if needed
    {"tools": "act", END: END},  # Map tool calls to "act" node
)
hotel_assistant_builder.add_edge("act", "reason")  # After acting, reason again

# Compile the graph
hotel_assistant = hotel_assistant_builder.compile()

if __name__ == "__main__":
    # Visualize the graph
    display(Image(hotel_assistant.get_graph().draw_mermaid_png()))

