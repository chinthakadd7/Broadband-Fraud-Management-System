from pathlib import Path

import pandas as pd
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["fraud_api"]
collection = db["transactions"]

# Read CSV
csv_path = Path(__file__).resolve().parents[1] / "training" / "synthetic_broadband_fraud_data.csv"
df = pd.read_csv(csv_path)

# Replace NaN with None (MongoDB stores None as null)
df = df.where(pd.notnull(df), None)

# Convert dataframe to list of dictionaries
records = df.to_dict(orient="records")

# Clear old records (optional)
collection.delete_many({})

# Insert all records
collection.insert_many(records)

print(f"Inserted {len(records)} records into MongoDB.")