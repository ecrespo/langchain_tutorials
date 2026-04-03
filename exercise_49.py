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


@tool
def calculate_total_cost(
    price_per_night: float, num_nights: int, tax_rate: float = 0.05
) -> str:
    """Calculate total hotel cost including taxes.

    Args:
        price_per_night: Hotel rate per night
        num_nights: Number of nights
        tax_rate: Tax rate (default 5%)

    Returns:
        Detailed cost breakdown
    """
    subtotal = price_per_night * num_nights
    tax = subtotal * tax_rate
    total = subtotal + tax

    return f"""Cost Breakdown:
- Rate: ${price_per_night:.2f} x {num_nights} nights = ${subtotal:.2f}
- Tax ({tax_rate * 100}%): ${tax:.2f}
- Total: ${total:.2f}"""


# -----NEW CODE-----#

# Additional imports for LangChain tools
from langchain_community.tools import DuckDuckGoSearchResults

# Initialize DuckDuckGo search tool, setting the name to "web_search" is important
web_search = DuckDuckGoSearchResults(
    name="web_search", output_format="list", num_results=5
)


class TravelAssistant:
    def __init__(self):
        self.llm = init_chat_model("gpt-4o-mini", model_provider="openai")
        self.tools = {
            "web_search": web_search,  # LangChain provided tool
            "query_hotels": query_hotels,
            "calculate_total_cost": calculate_total_cost,
        }
        self.llm_with_tools = self.llm.bind_tools(self.tools.values())
        self.messages = []

        current_year = datetime.now().year

        self.system_prompt = f"""You are a helpful travel assistant that 
        can search the web and find hotels. When users ask about events 
        or locations, first use web_search to find current information. 
        Then use query_hotels to find nearby accommodations. This allows 
        you to handle queries about events, landmarks, or activities. Be conversational and helpful in your responses.
        Your current year is {current_year}."""

        self.messages.append(SystemMessage(content=self.system_prompt))

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
                tool = self.tools[tool_call["name"]]
                tool_result = tool.invoke(tool_call)
                self.messages.append(tool_result)

        # Store sequence for printing
        self.tool_sequence = self.current_sequence


assistant = TravelAssistant()
assistant.chat("Find me a hotel in Tokyo in time to witness this year's Marathon")
for msg in assistant.messages:
    msg.pretty_print()

