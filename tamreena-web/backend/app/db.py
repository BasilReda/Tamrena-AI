"""
Shared MongoDB client for Tamreena Web BFF.
"""

import os
from typing import Optional
from pymongo import MongoClient

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://mongodb:27017/tamrena"
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "tamrena")
    return client[db_name]


def get_users_collection():
    return get_db()["users"]


def get_live_sessions_collection():
    return get_db()["live_sessions"]


def get_live_session_ownership_collection():
    return get_db()["live_session_ownership"]


# Backward-compatibility aliases
def get_users_table():
    return get_users_collection()


def get_live_sessions_table():
    return get_live_sessions_collection()


def get_live_session_ownership_table():
    return get_live_session_ownership_collection()
