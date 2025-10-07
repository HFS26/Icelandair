import pandas as pd
import requests
from datetime import datetime

# === SETTINGS ===
API_KEY = "JV2EW5EWN94HGNDSXGT72E3U8"

# Map known airports to queryable location names (you can add more)
AIRPORT_LOCATIONS = {
    "KEF": "Keflavik, Iceland",
    "JFK": "New York JFK, USA",
    "LHR": "London Heathrow, UK",
    "HND": "Tokyo Haneda, Japan",
    "SYD": "Sydney, Australia",
    "VRN": "Verona, Italy"
}

# === WEATHER FETCH FUNCTION ===
def get_weather(location, date_str, hour_str):
    """Fetch hourly weather for given location, date, and hour."""
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        f"{location}/{date_str}/{date_str}"
        f"?unitGroup=metric&include=hours&key={API_KEY}&contentType=json"
    )
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
        data = response.json()
        for day in data.get("days", []):
            for hour in day.get("hours", []):
                if hour["datetime"].startswith(hour_str[:2]):
                    return {
                        "temp": hour.get("temp"),
                        "humidity": hour.get("humidity"),
                        "windspeed": hour.get("windspeed"),
                        "pressure": hour.get("pressure"),
                        "visibility": hour.get("visibility"),
                        "cloudcover": hour.get("cloudcover"),
                        "conditions": hour.get("conditions")
                    }
    except Exception:
        return {}
    return {}

# === LOAD FLIGHT DATA ===
df = pd.read_csv("flight_legs_cleaned_v2.csv", header=None)

# Rename columns for clarity (based on your structure)
df.columns = [
    "FlightDate","FlightNumber","Origin","SchedDepDateTime",
    "SchedArrDateTime","Destination","Dep2","Arr2","Class",
    "FlightType","DelayReason","DelayCategory","DelayDescription",
    "DelayCount","Status"
]

# Clean datetime formats
df["SchedDepDateTime"] = pd.to_datetime(df["SchedDepDateTime"], errors="coerce")
df["SchedArrDateTime"] = pd.to_datetime(df["SchedArrDateTime"], errors="coerce")

# Prepare containers for weather data
origin_weather = []
dest_weather = []

# === FETCH LOOP ===
for idx, row in df.iterrows():
    # Origin airport and departure
    origin_code = row["Origin"]
    dest_code = row["Destination"]

    dep_time = row["SchedDepDateTime"]
    arr_time = row["SchedArrDateTime"]

    if pd.notna(dep_time) and origin_code in AIRPORT_LOCATIONS:
        dep_date = dep_time.strftime("%Y-%m-%d")
        dep_hour = dep_time.strftime("%H:%M:%S")
        origin_weather.append(get_weather(AIRPORT_LOCATIONS[origin_code], dep_date, dep_hour))
    else:
        origin_weather.append({})

    if pd.notna(arr_time) and dest_code in AIRPORT_LOCATIONS:
        arr_date = arr_time.strftime("%Y-%m-%d")
        arr_hour = arr_time.strftime("%H:%M:%S")
        dest_weather.append(get_weather(AIRPORT_LOCATIONS[dest_code], arr_date, arr_hour))
    else:
        dest_weather.append({})

# === MERGE WEATHER FEATURES ===
df_origin = pd.DataFrame(origin_weather).add_prefix("Origin_")
df_dest = pd.DataFrame(dest_weather).add_prefix("Dest_")
df_final = pd.concat([df, df_origin, df_dest], axis=1)

# === SAVE RESULT ===
df_final.to_csv("flight_legs_with_weather.csv", index=False)
print("Weather features successfully added and saved to flight_legs_with_weather.csv")
