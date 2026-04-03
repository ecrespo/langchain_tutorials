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
    try:
        # Use Open-Meteo free weather API (no key required)
        # First get coordinates for the city
        geocoding_url = (
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        )
        geo_response = requests.get(geocoding_url)

        geo_response.raise_for_status()

        geo_data = geo_response.json()
        if not geo_data.get("results"):
            return f"Error: City '{city}' not found"

        # Get weather data
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"

        if date:
            weather_url += f"&start_date={date}&end_date={date}"

        weather_response = requests.get(weather_url)

        weather_response.raise_for_status()

        data = weather_response.json()
        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        result = f"Weather in {city}"
        if date and daily.get("time"):
            result += f" on {date}:\n"
            result += f"High: {daily['temperature_2m_max'][0]}°C\n"
            result += f"Low: {daily['temperature_2m_min'][0]}°C\n"
            result += f"Precipitation: {daily['precipitation_sum'][0]}mm"
        else:
            result += f" (current):\n"
            result += f"Temperature: {current.get('temperature', 'N/A')}°C\n"
            result += f"Wind Speed: {current.get('windspeed', 'N/A')} km/h"

        return result
    except Exception as e:
        return f"Error: Failed to get weather - {str(e)}"


# -----NEW CODE-----#


@tool
def book_room(
    hotel_id: int,
    room_type: str,
    check_in_date: date,
    check_out_date: date,
    guest_id: int = 1001,
    api_base_url: str = "https://hotel-booking-five-delta.vercel.app",
) -> str:
    """Book a room in a hotel using the hotel booking API

    Args:
        hotel_id: The ID of the hotel
        room_type: The type of room to book (e.g., 'Deluxe Room', 'Suite')
        check_in_date: Check-in date
        check_out_date: Check-out date
        guest_id: ID of the guest making the reservation (defaults to 1001)
        api_base_url: Base URL of the hotel booking API
    """
    try:
        # GET request to check availability
        availability_response = requests.get(
            f"{api_base_url}/hotels/{hotel_id}/availability",
            params={
                "check_in": check_in_date.isoformat(),
                "check_out": check_out_date.isoformat(),
                "room_type": room_type,
            },
        )

        availability_response.raise_for_status()

        return f"Room '{room_type}' is available at hotel {hotel_id} for {check_in_date} to {check_out_date}"

    except requests.exceptions.ConnectionError:
        return f"Error: Unable to connect to hotel booking API at {api_base_url}"
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred - {str(e)}"


print(
    book_room.invoke(
        {
            "hotel_id": 1,
            "room_type": "Deluxe Room",
            "check_in_date": datetime.now().date(),
            "check_out_date": (datetime.now() + timedelta(days=1)).date(),
        }
    )
)

