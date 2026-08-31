"""
MongoDB-backed table adapter for Tamrena-Workout — replacing DynamoDB.
Provides MongoTableAdapter which exposes the exact .get_item(), .put_item(),
.update_item(), .query(), .scan(), and .delete_item() interface used throughout
the codebase so all agent tools and pipelines query MongoDB cleanly.
"""

import os
import re
from decimal import Decimal
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


def _mongo_encode(value):
    """Recursively convert values BSON/pymongo cannot encode.

    Much of this codebase still wraps floats in ``Decimal`` for the old
    DynamoDB Number type (see ``pipeline/inbody_history._dec``). bson has no
    Decimal codec, so every such write blew up with
    ``InvalidDocument: cannot encode object: Decimal(...)``. Normalise
    Decimal -> int/float on the way into MongoDB.
    """
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _mongo_encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mongo_encode(v) for v in value]
    return value


_CMP_OPS = {
    "=": lambda v: v,
    "<>": lambda v: {"$ne": v},
    ">": lambda v: {"$gt": v},
    ">=": lambda v: {"$gte": v},
    "<": lambda v: {"$lt": v},
    "<=": lambda v: {"$lte": v},
}


def _parse_kv_expression(expr, values, names=None):
    """Translate the small subset of DynamoDB Key/FilterExpression syntax this
    codebase uses into a MongoDB filter dict.

    Supported: ``field <op> :placeholder`` clauses joined by ``AND``, where
    <op> is one of = <> < <= > >=, plus ``begins_with(field, :placeholder)``.
    ``#alias`` attribute-name placeholders are resolved via ``names``.
    Anything unrecognised is skipped (callers post-filter in Python) rather
    than silently matching nothing.
    """
    names = names or {}
    values = values or {}
    mongo_filter: dict = {}
    expr = (expr or "").strip()
    if not expr:
        return mongo_filter

    for clause in expr.split(" AND "):
        clause = clause.strip()
        if not clause:
            continue

        if clause.lower().startswith("begins_with(") and clause.endswith(")"):
            inner = clause[clause.index("(") + 1: -1]
            field_tok, ph = (p.strip() for p in inner.split(",", 1))
            field = names.get(field_tok, field_tok)
            prefix = values.get(ph, ph)
            mongo_filter[field] = {"$regex": f"^{re.escape(str(prefix))}"}
            continue

        matched_op = next(
            (op for op in ("<>", ">=", "<=", "=", ">", "<") if f" {op} " in f" {clause} "),
            None,
        )
        if not matched_op:
            continue
        lhs, rhs = (p.strip() for p in clause.split(matched_op, 1))
        field = names.get(lhs, lhs)
        value = values.get(rhs, rhs)
        condition = _CMP_OPS[matched_op](value)
        if field in mongo_filter and isinstance(mongo_filter[field], dict) and isinstance(condition, dict):
            mongo_filter[field].update(condition)
        else:
            mongo_filter[field] = condition

    return mongo_filter


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
    def __init__(self, collection_name: str, primary_key: Optional[str] = None):
        self.table_name = collection_name
        self.collection_name = collection_name
        # The item field that uniquely identifies a row (the DynamoDB
        # partition key). put_item replaces the doc with the same value here.
        # Set explicitly per table — the _get_pk() heuristic below is only a
        # fallback and gets it wrong for tables that carry both a per-row id
        # and a shared session_id/user_id (e.g. it would collapse every
        # feedback row for a session into one document).
        self.primary_key = primary_key

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
        item_copy = _mongo_encode(dict(Item))
        item_copy.pop("_id", None)
        pk = self.primary_key or self._get_pk(item_copy)
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
            self.collection.update_one(
                _mongo_encode(Key), {"$set": _mongo_encode(set_fields)}, upsert=True
            )
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
        filter_dict = _parse_kv_expression(
            KeyConditionExpression, ExpressionAttributeValues, ExpressionAttributeNames
        )

        sort_order = 1 if ScanIndexForward else -1
        cursor = self.collection.find(_mongo_encode(filter_dict), {"_id": 0})
        try:
            cursor = cursor.sort("created_at", sort_order)
        except Exception:
            pass

        if Limit > 0:
            cursor = cursor.limit(Limit)

        items = list(cursor)
        return {"Items": items, "Count": len(items)}

    def scan(
        self,
        FilterExpression: str = "",
        ExpressionAttributeValues: dict = None,
        ExpressionAttributeNames: dict = None,
        ExclusiveStartKey: dict = None,
        ProjectionExpression: str = None,
        Limit: int = 0,
        IndexName: str = None,
        **_ignored,
    ) -> dict:
        """DynamoDB-style Scan with optional FilterExpression (see
        ``_parse_kv_expression`` for the supported syntax). Mongo returns the
        whole result set in one shot, so pagination (ExclusiveStartKey /
        LastEvaluatedKey) is a no-op.
        """
        mongo_filter = _parse_kv_expression(
            FilterExpression, ExpressionAttributeValues, ExpressionAttributeNames
        )
        cursor = self.collection.find(_mongo_encode(mongo_filter), {"_id": 0})
        if Limit and Limit > 0:
            cursor = cursor.limit(Limit)
        items = list(cursor)
        return {"Items": items, "Count": len(items)}

    def delete_item(self, Key: dict) -> dict:
        self.collection.delete_one(Key)
        return {}


def get_resource():
    return None


def get_plan_sessions_table():
    return MongoTableAdapter(PLAN_SESSIONS_TABLE_NAME, primary_key="session_id")


def get_exercises_table():
    return MongoTableAdapter(EXERCISES_TABLE_NAME, primary_key="exercise_id")


def get_inbody_scans_table():
    return MongoTableAdapter(INBODY_SCANS_TABLE_NAME, primary_key="scan_id")


def get_workout_feedback_table():
    return MongoTableAdapter(WORKOUT_FEEDBACK_TABLE_NAME, primary_key="feedback_id")


def get_corrective_results_table():
    return MongoTableAdapter(CORRECTIVE_RESULTS_TABLE_NAME, primary_key="result_id")


def get_progress_reports_table():
    # PK is new_session_id (one report per monthly review) — see
    # pipeline/monthly_progress.record_progress_report.
    return MongoTableAdapter(PROGRESS_REPORTS_TABLE_NAME, primary_key="new_session_id")


def get_plan_adjustments_table():
    return MongoTableAdapter(PLAN_ADJUSTMENTS_TABLE_NAME, primary_key="adjustment_id")


def get_coach_messages_table():
    return MongoTableAdapter(COACH_MESSAGES_TABLE_NAME, primary_key="message_id")
