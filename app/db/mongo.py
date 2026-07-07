"""
MongoDB connection helpers and a minimal repository for stored transactions.
"""

import os
import importlib
from typing import Any, Optional

from dotenv import find_dotenv, load_dotenv


# Load environment variables from a local .env file if present.
load_dotenv(find_dotenv(), override=False)

DEFAULT_MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DEFAULT_MONGODB_DB = os.getenv("MONGODB_DB", "fraud_api")
DEFAULT_MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "transactions")

_client: Optional[Any] = None


def get_client() -> Any:
    global _client
    if _client is None:
        try:
            pymongo = importlib.import_module("pymongo")
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised only when the driver is absent locally
            raise RuntimeError("pymongo is not installed. Install requirements.txt to use MongoDB-backed endpoints.") from exc
        _client = pymongo.MongoClient(DEFAULT_MONGODB_URI)
    return _client


def get_database():
    return get_client()[DEFAULT_MONGODB_DB]


def get_collection(collection_name: Optional[str] = None):
    return get_database()[collection_name or DEFAULT_MONGODB_COLLECTION]


class MongoTransactionRepository:
    def fetch_transactions(self, collection_name: Optional[str] = None, customer_id: Optional[str] = None, skip: int = 0, limit: Optional[int] = None):
        query = {}
        if customer_id:
            query["customer_id"] = customer_id

        cursor = get_collection(collection_name).find(query).sort("_id", 1).skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)

        documents = list(cursor)

        for doc in documents:
             doc["_id"] = str(doc["_id"])

        return documents