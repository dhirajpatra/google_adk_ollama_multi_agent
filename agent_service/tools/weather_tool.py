# tools/weather_tool.py
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv
from tools.ipinfo import get_current_location
import os
from typing import Optional

logging.basicConfig(level=logging.INFO)
load_dotenv()

class WeatherToolArgs(BaseModel):
    city: str = Field(description="The city to get the weather for.")
    unit: Optional[str] = Field(default="celsius", description="The unit of temperature (default is Celsius).")

def get_weather_report(city: str, unit: str = "celsius", tool_call_id: Optional[str] = None) -> dict:
    """Retrieves the current weather report for a specified city.

    Returns:
        dict: A dictionary containing the weather information with a 'status' key
              ('success' or 'error') and a 'report' key with the weather details if
              successful, or an 'error_message' if an error occurred.
    """
    logging.info(f"[get_weather_report] Called for city: {city} (unit: {unit})")
    city_normalized = city.lower().replace(" ", "")

    # Base mock data in Celsius (expanded for more Indian cities)
    mock_weather_db_celsius = {
        "newyork": {"condition": "sunny", "temp": 25},
        "london": {"condition": "cloudy", "temp": 15},
        "tokyo": {"condition": "light rain", "temp": 18},
        "chicago": {"condition": "sunny", "temp": 25},
        "toronto": {"condition": "partly cloudy", "temp": 30},
        "chennai": {"condition": "rainy", "temp": 35},
        "bengaluru": {"condition": "sunny", "temp": 30},
        "newdelhi": {"condition": "cloudy", "temp": 40},
        "kolkata": {"condition": "sunny", "temp": 38},
        "mumbai": {"condition": "cloudy", "temp": 32},
        "vijayapura": {"condition": "pleasant", "temp": 33}, # Added Vijayapura
        "hyderabad": {"condition": "warm", "temp": 34},
        "pune": {"condition": "clear", "temp": 31},
    }

    if city_normalized in mock_weather_db_celsius:
        data = mock_weather_db_celsius[city_normalized]
        temp = data["temp"]
        temp_unit = "°C"

        if unit.lower() in ["fahrenheit", "f"]:
            temp = (temp * 9/5) + 32
            temp_unit = "°F"

        report = f"The weather in {city.title()} is {data['condition']} with a temperature of {int(temp)}{temp_unit}."
        return {"status": "success", "report": report}
    else:
        return {"status": "error", "error_message": f"Weather information for '{city}' is not available."}

# ADK function tool
weather_tool = FunctionTool(func=get_weather_report)
