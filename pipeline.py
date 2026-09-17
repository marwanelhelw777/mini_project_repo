import csv
import json
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

PARAMS = {
    "format": "geojson",
    "starttime": "2026-08-15",
    "endtime": "2026-08-29",
    "minmagnitude": 2.5,
}


def fetch_data():
    """Fetch earthquake data from the USGS Earthquake API."""
    try:
        response = requests.get(API_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None


def save_raw_data(data):
    """Save the raw API response and extracted event IDs."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / "earthquakes.json"
    with open(raw_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    records = data.get("features", [])
    event_ids = [record.get("id") for record in records if record.get("id")]

    ids_path = RAW_DIR / "extracted_ids.txt"
    ids_path.write_text("\n".join(event_ids), encoding="utf-8")

    print("Earthquake data saved successfully!")
    print(f"Extracted {len(event_ids)} event IDs.")


def process_data(data):
    """Filter and transform earthquake records."""
    records = data.get("features", [])
    earthquakes = []

    for record in records:
        properties = record.get("properties", {})
        if properties.get("type") == "earthquake":
            earthquakes.append(record)

    print("Loaded records:", len(records))
    print("Earthquake records:", len(earthquakes))

    fields = ["felt", "cdi", "mmi", "alert", "nst", "dmin", "gap"]

    for field in fields:
        missing = sum(
            1
            for record in earthquakes
            if record.get("properties", {}).get(field) is None
        )
        print(field, ":", missing, "missing")

    processed = []

    for record in earthquakes:
        properties = record.get("properties", {})

        row = {
            "id": record.get("id"),
            "magnitude": properties.get("mag"),
            "place": properties.get("place"),
            "time": properties.get("time"),
            "type": properties.get("type"),
            "nst": properties.get("nst"),
            "dmin": properties.get("dmin"),
            "gap": properties.get("gap"),
        }

        processed.append(row)

    return processed


def save_processed_data(processed):
    """Save processed earthquake data as JSON and CSV."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    json_path = PROCESSED_DIR / "earthquakes_processed.json"
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(processed, file, indent=4)

    csv_path = PROCESSED_DIR / "earthquakes_processed.csv"

    if processed:
        with open(csv_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=processed[0].keys())
            writer.writeheader()
            writer.writerows(processed)

    print("Processed data saved successfully!")


def analyze_data(processed):
    """Print basic earthquake statistics."""
    magnitudes = [
        record["magnitude"]
        for record in processed
        if record["magnitude"] is not None
    ]

    if not magnitudes:
        print("No magnitude data available.")
        return

    print("Minimum magnitude:", min(magnitudes))
    print("Maximum magnitude:", max(magnitudes))
    print("Average magnitude:", sum(magnitudes) / len(magnitudes))

    strongest = sorted(
        processed,
        key=lambda record: record["magnitude"] or float("-inf"),
        reverse=True,
    )

    print("\nTop 5 strongest earthquakes:")

    for record in strongest[:5]:
        print(record["magnitude"], "-", record["place"])


def main():
    data = fetch_data()

    if data is None:
        return

    save_raw_data(data)

    processed = process_data(data)

    if not processed:
        print("No earthquake records found.")
        return

    print("Processed records:", len(processed))
    print(processed[0])

    save_processed_data(processed)
    analyze_data(processed)


if __name__ == "__main__":
    main()
