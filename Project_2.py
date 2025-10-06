import requests

icao = "BIKF"
url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=raw&hours=1"

response = requests.get(url)
print(response.text)  # Example: BIRK 231800Z 17015KT 9999 SCT020 08/05 Q1015
