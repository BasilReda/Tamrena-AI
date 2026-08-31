"""
MongoDB-backed table adapter for Tamrena-Workout — replacing DynamoDB.
Provides MongoTableAdapter which exposes the exact .get_item(), .put_item(),
.update_item(), .query(), .scan(), and .delete_item() interface used throughout
the codebase so all agent tools and pipelines query MongoDB cleanly.
"""

import os
from typing import Optional
from pymongo import MongoClient

from config import (
    COACH_MESSAGES_TABLE_NAME,
    CORRECTIVE_RESULTS_TABLE_NAME,
    EXERCISES_TABLE_NAME,
    INBODY_SCANS_TABLE_NAME,
    PLAN_ADJUSTMENTS_TABLE_NAME,
    PLAN_SESSIONS_TABLE_NAME,
    PROGRESS_REPORTS_TABLE_NAME,
    WORKOUT_FEEDBACK_TABLE_NAME,
)

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://mongodb:27017/tamrena"
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return _mongo_client


def get_mongo_db():
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "tamrena")
    return client[db_name]


class MongoTableAdapter:
    def __init__(self, collection_name: str):
        self.table_name = collection_name
        self.collection_name = collection_name

    @property
    def collection(self):
        return get_mongo_db()[self.collection_name]

    @property
    def table_status(self):
        return "ACTIVE"

    def describe_table(self):
        return {"Table": {"TableStatus": "ACTIVE"}}

    def load(self):
        pass

    def _get_pk(self, doc: dict) -> str:
        for pk in [
            "session_id",
            "exercise_id",
            "scan_id",
            "submission_id",
            "feedback_id",
            "report_id",
            "adjustment_id",
            "user_id",
            "message_id",
            "id",
        ]:
            if pk in doc:
                return pk
        return list(doc.keys())[0] if doc else "id"

    def get_item(self, Key: dict) -> dict:
        doc = self.collection.find_one(Key, {"_id": 0})
        return {"Item": doc} if doc else {}

    def put_item(self, Item: dict) -> dict:
        item_copy = dict(Item)
        item_copy.pop("_id", None)
        pk = self._get_pk(item_copy)
        if pk in item_copy:
            self.collection.replace_one({pk: item_copy[pk]}, item_copy, upsert=True)
        else:
            self.collection.insert_one(item_copy)
        return {}

    def update_item(
        self,
        Key: dict,
        UpdateExpression: str = "",
        ExpressionAttributeValues: dict = None,
        ExpressionAttributeNames: dict = None,
    ) -> dict:
        set_fields = {}
        if ExpressionAttributeValues:
            for k, v in ExpressionAttributeValues.items():
                clean_k = k.lstrip(":")
                if ExpressionAttributeNames:
                    for placeholder, actual in ExpressionAttributeNames.items():
                        if placeholder.lstrip("#") == clean_k or clean_k == placeholder.lstrip("#"):
                            clean_k = actual
                set_fields[clean_k] = v

        if set_fields:
            self.collection.update_one(Key, {"$set": set_fields}, upsert=True)
        return {}

    def query(
        self,
        IndexName: str = None,
        KeyConditionExpression: str = "",
        ExpressionAttributeValues: dict = None,
        ScanIndexForward: bool = True,
        Limit: int = 0,
        ProjectionExpression: str = None,
        ExpressionAttributeNames: dict = None,
    ) -> dict:
        filter_dict = {}
        if ExpressionAttributeValues:
            for k, v in ExpressionAttributeValues.items():
                if k == ":uid":
                    filter_dict["user_id"] = v
                elif k == ":sid":
                    filter_dict["previous_session_id"] = v
                elif k == ":m":
                    filter_dict["primary_muscle"] = v
                elif k == ":mt":
                    filter_dict["movement_type"] = v
                else:
                    clean_k = k.lstrip(":")
                    filter_dict[clean_k] = v

        sort_order = 1 if ScanIndexForward else -1
        cursor = self.collection.find(filter_dict, {"_id": 0})
        try:
            cursor = cursor.sort("created_at", sort_order)
        except Exception:
            pass

        if Limit > 0:
            cursor = cursor.limit(Limit)

        items = list(cursor)
        return {"Items": items, "Count": len(items)}

    def scan(self) -> dict:
        items = list(self.collection.find({}, {"_id": 0}))
        return {"Items": items, "Count": len(items)}

    def delete_item(self, Key: dict) -> dict:
        self.collection.delete_one(Key)
        return {}


def get_resource():
    return None


def get_plan_sessions_table():
    return MongoTableAdapter(PLAN_SESSIONS_TABLE_NAME)


def get_exercises_table():
    return MongoTableAdapter(EXERCISES_TABLE_NAME)


def get_inbody_scans_table():
    return MongoTableAdapter(INBODY_SCANS_TABLE_NAME)


def get_workout_feedback_table():
    return MongoTableAdapter(WORKOUT_FEEDBACK_TABLE_NAME)


def get_corrective_results_table():
    return MongoTableAdapter(CORRECTIVE_RESULTS_TABLE_NAME)


def get_progress_reports_table():
    return MongoTableAdapter(PROGRESS_REPORTS_TABLE_NAME)


def get_plan_adjustments_table():
    return MongoTableAdapter(PLAN_ADJUSTMENTS_TABLE_NAME)


def get_coach_messages_table():
    return MongoTableAdapter(COACH_MESSAGES_TABLE_NAME)
