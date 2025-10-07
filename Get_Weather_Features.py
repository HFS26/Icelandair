import pandas as pd
import requests
from datetime import datetime

# === SETTINGS ===
API_KEY = "JV2EW5EWN94HGNDSXGT72E3U8"

# === LOAD FLIGHT DATA ===
df = pd.read_csv("flight_legs_cleaned_v2.csv", header=None)
df.columns = [f"col_{i+1}" for i in range(df.shape[1])]  # Auto-generate headers

# === IDENTIFY LIKELY COLUMN INDEXES ===
# Find columns that contain 3-letter uppercase airport codes (IATA codes)
origin_candidates = []
destination_candidates = []

for col in df.columns:
    unique_vals = df[col].dropna().astype(str)
    code_like = unique_vals[unique_vals.str.match(r"^[A-Z]{3}$")]
    if len(code_like) > len(df) * 0.05:  # heuristic threshold
        if not origin_candidates:
            origin_candidates.append(col)
        else:
            destination_candidates.append(col)

# Assume first found is Origin, second is Destination
origin_col = origin_candidates[0] if origin_candidates else "col_3"
destination_col = destination_candidates[0] if destination_candidates else "col_6"

# Find columns with date/time values
datetime_candidates = [c for c in df.columns if df[c].astype(str).str.contains(r"\d{4}-\d{2}-\d{2}").any()]
dep_time_col = datetime_candidates[0] if len(datetime_candidates) > 0 else "col_4"
arr_time_col = datetime_candidates[1] if len(datetime_candidates) > 1 else "col_5"

print(f"Detected columns:")
print(f"  Origin -> {origin_col}")
print(f"  Destination -> {destination_col}")
print(f"  Scheduled Departure -> {dep_time_col}")
print(f"  Scheduled Arrival -> {arr_time_col}")

# === CONVERT DATETIMES ===
df[dep_time_col] = pd.to_datetime(df[dep_time_col], format="%m/%d/%Y %H:%M", errors="coerce")
df[arr_time_col] = pd.to_datetime(df[arr_time_col], format="%m/%d/%Y %H:%M", errors="coerce")


# === AIRPORT DICTIONARY ===
# Extract all unique airport codes
unique_airports = set(df[origin_col].dropna().astype(str).unique()) | set(df[destination_col].dropna().astype(str).unique())
AIRPORT_LOCATIONS = {code: code for code in unique_airports}

# === WEATHER FETCH FUNCTION ===
def get_weather(location, date_str, hour_str):
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

# === FETCH WEATHER DATA ===
origin_weather = []
dest_weather = []

for idx, row in df.iterrows():
    origin_code = row[origin_col]
    dest_code = row[destination_col]
    dep_time = row[dep_time_col]
    arr_time = row[arr_time_col]

    if pd.notna(dep_time) and isinstance(origin_code, str):
        dep_date = dep_time.strftime("%Y-%m-%d")
        dep_hour = dep_time.strftime("%H:%M:%S")
        origin_weather.append(get_weather(AIRPORT_LOCATIONS[origin_code], dep_date, dep_hour))
    else:
        origin_weather.append({})

    if pd.notna(arr_time) and isinstance(dest_code, str):
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
