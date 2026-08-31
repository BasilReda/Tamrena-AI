"""
User accounts — stored in MongoDB `users` collection (see app/db.py).
Username + password is the main sign-in method. Usernames are normalized
to lowercase for storage and lookup.
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from app.db import get_users_collection


def _serialize(item: dict) -> dict:
    created_at = item.get("created_at")
    if isinstance(created_at, str):
        created_at_dt = datetime.fromisoformat(created_at)
    elif isinstance(created_at, datetime):
        created_at_dt = created_at
    else:
        created_at_dt = datetime.now(timezone.utc)

    return {
        "id": item["user_id"],
        "username": item["username"],
        "created_at": created_at_dt,
    }


def get_user_by_id(user_id: str) -> Optional[dict]:
    if not isinstance(user_id, str) or not user_id:
        return None
    item = get_users_collection().find_one({"user_id": user_id})
    return _serialize(item) if item else None


def get_user_by_username(username: str) -> Optional[dict]:
    """Internal use only (login needs password_hash) — returns the raw dict."""
    item = get_users_collection().find_one({"username": username.lower()})
    return item


def create_user(username: str, password: str) -> dict:
    normalized = username.lower()
    if get_user_by_username(normalized):
        raise ValueError("Username is already taken.")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    item = {
        "user_id": secrets.token_hex(12),
        "username": normalized,
        "password_hash": password_hash.decode("utf-8"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    get_users_collection().insert_one(item)
    return _serialize(item)


def verify_password(username: str, password: str) -> Optional[dict]:
    """Returns the public-safe user dict if username+password match, else None."""
    item = get_user_by_username(username)
    if item is None:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), item["password_hash"].encode("utf-8")):
        return None
    return _serialize(item)


def get_last_nutrition_run_id(user_id: str) -> Optional[str]:
    item = get_users_collection().find_one({"user_id": user_id})
    return item.get("last_nutrition_run_id") if item else None


def set_last_nutrition_run_id(user_id: str, run_id: str) -> None:
    get_users_collection().update_one(
        {"user_id": user_id},
        {"$set": {"last_nutrition_run_id": run_id}},
    )
