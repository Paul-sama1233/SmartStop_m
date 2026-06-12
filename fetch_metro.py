import urllib.request
import urllib.parse
import json

query = """
[out:json][timeout:25];
node["station"="subway"](41.1,69.1,41.5,69.5);
out body;
"""

url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": query}).encode()

req = urllib.request.Request(
    url,
    data=data,
    method="POST",
    headers={
        "User-Agent": "Mozilla/5.0 SmartStop/1.0",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

print("Запрашиваем данные из Overpass API...")

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())

    stations = result.get("elements", [])
    print(f"Найдено станций: {len(stations)}\n")

    for s in sorted(
        stations,
        key=lambda x: x.get("tags", {}).get("name:ru", x.get("tags", {}).get("name", ""))
    ):
        tags = s.get("tags", {})
        name_ru = tags.get("name:ru", "")
        name = tags.get("name", "")
        display_name = name_ru or name
        lat = s.get("lat")
        lon = s.get("lon")
        line = tags.get("line", tags.get("colour", "?"))
        print(f"  ('{display_name}', {lat}, {lon}),  # {line}")

except Exception as e:
    print(f"Ошибка: {e}")