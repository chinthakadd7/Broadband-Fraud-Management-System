from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

try:
    client.admin.command("ping")
    print("✅ Connected to MongoDB successfully!")

    print("Databases:")
    print(client.list_database_names())

except Exception as e:
    print("❌ Connection failed")
    print(e)