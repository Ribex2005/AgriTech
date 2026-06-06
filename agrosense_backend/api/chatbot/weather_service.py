import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather(location):
    if not API_KEY:
        return "Weather API key not found."

    url = f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if "cod" not in data or data["cod"] != 200:
            return "Location not found."


        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]

        return (
            f"Weather in {location}:\n"
            f"Temperature: {temperature}°C\n"
            f"Humidity: {humidity}%\n"
            f"Condition: {description}"
        )

    except Exception as e:
        return "Error fetching weather data."