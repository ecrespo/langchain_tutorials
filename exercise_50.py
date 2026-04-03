from datetime import datetime, date, timedelta
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()


import requests

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


# Additional imports for LangChain tools
from langchain_community.tools import DuckDuckGoSearchResults

# Initialize DuckDuckGo search tool
web_search = DuckDuckGoSearchResults(
    name="web_search", output_format="list", num_results=5
)


# -----NEW CODE-----#

# Additional imports for API calls
import requests


@tool
def get_weather(city: str, date: str = None) -> str:
    """Get weather information for a city.

    Args:
        city: Name of the city
        date: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        Weather information including temperature and conditions
    """
    # Use Open-Meteo free geocoding API (no key required)
    # First get coordinates for the city
    geocoding_url = (
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    )
    geo_response = requests.get(geocoding_url)
    geo_data = geo_response.json()

    # For now, just return the coordinates
    if geo_data.get("results"):
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        return f"Coordinates for {city}: Latitude {lat}, Longitude {lon}"
    else:
        return f"City '{city}' not found"


print(get_weather.invoke({"city": "dubai"}))

