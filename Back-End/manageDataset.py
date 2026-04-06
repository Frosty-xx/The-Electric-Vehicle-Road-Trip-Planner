import requests
import json

url = "https://api.openchargemap.io/v3/poi/"

params = {
    "output": "json",
    "countrycode": "TN",
    "maxresults": 30,     
}

headers = {
    "X-API-Key": "e9bf02f0-1b99-4f5c-bd93-487fe7779998"
}

response = requests.get(url, params=params, headers=headers)

data = response.json()

with open("charging_stations_raw.json", "w") as f:
    json.dump(data, f, indent=4)

print("Data saved!")

cleaned_data = []

for station in data:
    item = {
        "name": station.get("AddressInfo", {}).get("Title"),
        "latitude": station.get("AddressInfo", {}).get("Latitude"),
        "longitude": station.get("AddressInfo", {}).get("Longitude"),
        "power_kw": None,
    }


    connections = station.get("Connections", [])
    for conn in connections:
        if conn.get("PowerKW"):
            item["power_kw"] = conn["PowerKW"]

    cleaned_data.append(item)


with open("charging_stations.json", "w") as f:
    json.dump(cleaned_data, f, indent=4)

print("Cleaned dataset ready!")


vehicle_data = {
    "name": "Hyundai Ioniq 5",
    "battery_kwh": 77.4,
    "range_km": 480,
    "consumption_kwh_per_km": 77.4 / 480
}

with open("vehicle.json", "w") as f:
    json.dump(vehicle_data, f, indent=4)

final_dataset = {
    "vehicle": vehicle_data,
    "charging_stations": cleaned_data
}

with open("ev_dataset.json", "w") as f:
    json.dump(final_dataset, f, indent=4)

print("Final dataset created!")