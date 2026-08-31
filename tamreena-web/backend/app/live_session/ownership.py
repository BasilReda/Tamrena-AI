"""
Owner lookup for Computer-Vision resources (upload ids, cv session ids).
Uses MongoDB live_session_ownership collection.
"""

from datetime import datetime, timezone
from typing import Optional

from app.db import get_live_session_ownership_collection


def record_ownership(resource_id: str, owner_user_id: str, resource_type: str) -> None:
    get_live_session_ownership_collection().update_one(
        {"resource_id": resource_id},
        {
            "$set": {
                "resource_id": resource_id,
                "owner_user_id": owner_user_id,
                "resource_type": resource_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )


def get_owner(resource_id: str) -> Optional[str]:
    item = get_live_session_ownership_collection().find_one({"resource_id": resource_id})
    return item.get("owner_user_id") if item else None


def owns(resource_id: str, user_id: str) -> bool:
    return get_owner(resource_id) == user_id
