import json
import requests
import re

# Load addresses from JSON file
with open("updated_addresses.json", "r", encoding="utf-8") as f:
    addresses = json.load(f)

API_KEY = "AIzaSyB0Jmg8aj4Cq2HLfmo88yoIO7-5Tz9FPMw"
DESTINATION_MARTIN = "Gærtorvet 1, Denmark"
DESTINATION_MARIE = "Smallegade 2, 2000 Frederiksberg, Denmark"

def convert_to_minutes(time_str):
    if not isinstance(time_str, str):
        return float('inf')

    match = re.match(r'(?:(\d+) hour[s]?)?\s*(?:(\d+) min[s]?)?', time_str)
    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return hours * 60 + minutes
    return float('inf')

def get_travel_time(entry, destination):
    origin = f"{entry['address']}, {entry['zipCode']} {entry['city']}, Denmark"

    def fetch_duration(o, d):
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={o}&destination={d}&mode=bicycling&key={API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "OK":
                return convert_to_minutes(data["routes"][0]["legs"][0]["duration"]["text"])
            return float('inf')
        except requests.RequestException as e:
            return float('inf')

    duration_to = fetch_duration(origin, destination)
    duration_back = fetch_duration(destination, origin)

    if duration_to == float('inf') or duration_back == float('inf'):
        return "Error: Could not fetch both directions"

    average_duration = (duration_to + duration_back) // 2

    return average_duration

for entry in addresses:
    martin_time = get_travel_time(entry, DESTINATION_MARTIN)
    marie_time = get_travel_time(entry, DESTINATION_MARIE)
    entry["travel_time_martin"] = martin_time
    entry["travel_time_marie"] = marie_time
    # Calculate combined travel time (average of both)
    if isinstance(martin_time, (int, float)) and isinstance(marie_time, (int, float)):
        entry["travel_time_combined"] = (martin_time + marie_time) // 2
    else:
        entry["travel_time_combined"] = "Error: Could not calculate combined time"

def calculate_scores(properties):
    # Calculate min and max for normalization
    max_price_per_area = max(p['perAreaPrice'] for p in properties)
    min_price_per_area = min(p['perAreaPrice'] for p in properties)
    max_cash_price = max(p['cashPrice'] for p in properties)
    min_cash_price = min(p['cashPrice'] for p in properties)
    max_area = max(p['housingArea'] for p in properties)
    min_area = min(p['housingArea'] for p in properties)
    max_lot_area = max(p['lotArea'] for p in properties)
    min_lot_area = min(p['lotArea'] for p in properties)
    max_travel_time_combined = max(p['travel_time_combined'] for p in properties if isinstance(p['travel_time_combined'], (int, float)))
    min_travel_time_combined = min(p['travel_time_combined'] for p in properties if isinstance(p['travel_time_combined'], (int, float)))

    # Calculate scores
    for p in properties:
        price_per_area_score = 100 - 100 * (p['perAreaPrice'] - min_price_per_area) / (max_price_per_area - min_price_per_area or 1)
        cash_price_score = 100 * (max_cash_price - p['cashPrice']) / (max_cash_price - min_cash_price or 1)
        area_score = 100 * (p['housingArea'] - min_area) / (max_area - min_area or 1)
        lot_area_score = 100 * (p['lotArea'] - min_lot_area) / (max_lot_area - min_lot_area or 1)
        
        if isinstance(p['travel_time_combined'], (int, float)):
            travel_time_score = 100 - 100 * (p['travel_time_combined'] - min_travel_time_combined) / (max_travel_time_combined - min_travel_time_combined or 1)
        else:
            travel_time_score = 0

        p['score'] = round(
            0.01 * cash_price_score +
            0.24 * price_per_area_score +
            0.04 * area_score +
            0.02 * lot_area_score +
            0.70 * travel_time_score
        )

    return properties

calculate_scores(addresses)

addresses.sort(key=lambda x: x["score"], reverse=True)

# Save the updated JSON file
with open("updated_addresses.json", "w", encoding="utf-8") as f:
    json.dump(addresses, f, indent=4, ensure_ascii=False)

print("Updated JSON file created!")