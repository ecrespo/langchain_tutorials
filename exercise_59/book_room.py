import requests
from datetime import date
from langchain.tools import tool


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

        # POST request to create reservation
        reservation_data = {
            "hotel_id": hotel_id,
            "guest_id": guest_id,
            "room_type": room_type,
            "check_in_date": check_in_date.isoformat(),
            "check_out_date": check_out_date.isoformat(),
        }

        reservation_response = requests.post(
            f"{api_base_url}/reservations/", json=reservation_data
        )

        reservation_response.raise_for_status()

        reservation = reservation_response.json()
        return (
            f"Room booked successfully! Reservation ID: {reservation['reservation_id']}"
        )

    except requests.exceptions.ConnectionError:
        return f"Error: Unable to connect to hotel booking API at {api_base_url}"
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred - {str(e)}"

