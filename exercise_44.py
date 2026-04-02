from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from dotenv import load_dotenv
from devtools import pprint
import requests

load_dotenv()

HOTEL_API_URL = "https://hotel-booking-server-1085074390115.us-east4.run.app"


def search_hotels_db(city: str, check_in: str, check_out: str) -> str:
    """Call the hotel booking API to search for available hotels."""
    response = requests.get(
        f"{HOTEL_API_URL}/hotels/search",
        params={"city": city, "check_in": check_in, "check_out": check_out},
    )
    hotels = response.json()

    if not hotels:
        return "No hotels found matching your criteria."

    formatted = []
    for i, hotel in enumerate(hotels, 1):
        formatted.append(
            f"{i}. {hotel['name']} in {hotel['city']}"
            f" - ${hotel['price_per_night']}/night"
            f" - {hotel['rating']} stars"
        )
    return "\n".join(formatted)


# -----NEW CODE-----#


@tool
def query_hotels(city: str, check_in: str, check_out: str) -> str:
    """Search for available hotels in a city for given dates.

    Args:
        city: City name to search hotels in
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)

    Returns:
        List of available hotels with pricing
    """
    return search_hotels_db(city, check_in, check_out)


class TravelAssistant:
    def __init__(self):
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        self.tools = {"query_hotels": query_hotels}
        self.llm_with_tools = self.llm.bind_tools(self.tools.values())
        self.messages = []

        current_year = datetime.now().year

        # System prompt
        self.system_prompt = f"""You are a helpful travel assistant that 
        can search for hotels and help with trip planning. When users 
        ask about hotels, use the query_hotels tool to search our database. Be conversational and helpful in your responses.
        Your current year is {current_year}."""

        self.messages.append(SystemMessage(content=self.system_prompt))

    def chat(self, message: str):
        # Add user message
        self.messages.append(HumanMessage(content=message))

        # Get AI response with potential tool calls
        response = self.llm_with_tools.invoke(self.messages)
        self.messages.append(response)

        # Check if tools were called
        if response.tool_calls:
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool = self.tools[tool_call["name"]]
                tool_result = tool.invoke(tool_call)
                self.messages.append(tool_result)

            # Get final response after tool execution
            final_response = self.llm_with_tools.invoke(self.messages)
            self.messages.append(final_response)


# Test single tool call
assistant = TravelAssistant()
next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
assistant.chat(f"Find me a hotel in Tokyo for one night on {next_week}")
for msg in assistant.messages:
    msg.pretty_print()

