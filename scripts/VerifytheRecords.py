from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

collection = client["fraud_api"]["transactions"]

print(collection.count_documents({}))
print(collection.find_one())