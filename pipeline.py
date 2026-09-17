import requests
import json
import csv
from pathlib import Path

url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

params = {
    "format": "geojson",
    "starttime": "2026-08-15",
    "endtime": "2026-08-29",
    "minmagnitude": 2.5
}
try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

except requests.exceptions.RequestException as e:
    print("Request failed:", e)
    exit()
Path("data/raw").mkdir(parents=True, exist_ok=True)

with open("data/raw/earthquakes.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print("Earthquake data saved successfully!")
all_records = data["features"]

event_ids = [record["id"] for record in all_records]

Path("data/raw/extracted_ids.txt").write_text(
    "\n".join(event_ids),
    encoding="utf-8"
)

print(f"Extracted {len(event_ids)} event ids.")
print("Number of records:", len(all_records))

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
with open(RAW_DIR / "earthquakes.json", "r", encoding="utf-8") as file:
    data = json.load(file)

records = data["features"]

print("Loaded records:", len(records))  
earthquakes = []

for record in records:
    if record["properties"]["type"] == "earthquake":
        earthquakes.append(record)

print("Earthquake records:", len(earthquakes))
fields = ["felt", "cdi", "mmi", "alert", "nst", "dmin", "gap"]

for field in fields:
    missing = 0

    for record in earthquakes:
        value = record["properties"].get(field)

        if value is None:
            missing += 1

    print(field, ":", missing, "missing")
    processed = []

for record in earthquakes:
    properties = record["properties"]

    row = {
        "id": record["id"],
        "magnitude": properties["mag"],
        "place": properties["place"],
        "time": properties["time"],
        "type": properties["type"],
        "nst": properties["nst"],
        "dmin": properties["dmin"],
        "gap": properties["gap"]
    }

    processed.append(row)

print("Processed records:", len(processed))
print(processed[0])
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

with open(PROCESSED_DIR / "earthquakes_processed.json", "w", encoding="utf-8") as file:
    json.dump(processed, file, indent=4)

print("Processed data saved successfully!")
magnitudes = [
    record["magnitude"]
    for record in processed
    if record["magnitude"] is not None
]

print("Minimum magnitude:", min(magnitudes))
print("Maximum magnitude:", max(magnitudes))
print("Average magnitude:", sum(magnitudes) / len(magnitudes))
strongest = sorted(
    processed,
    key=lambda record: record["magnitude"],
    reverse=True
)

print("\nTop 5 strongest earthquakes:")

for record in strongest[:5]:
    print(
        record["magnitude"],
        "-",
        record["place"]
    )

csv_path = PROCESSED_DIR / "earthquakes_processed.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=processed[0].keys()
    )

    writer.writeheader()
    writer.writerows(processed)

print("CSV file saved successfully!")