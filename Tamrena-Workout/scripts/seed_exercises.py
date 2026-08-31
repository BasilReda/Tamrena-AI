"""
Seed the `workout_exercises` collection from the bundled legacy SQLite
catalogue (``data/tamreena.db``).

The DynamoDB era had this table populated once, out of band, by
``scripts/migrate_exercises_to_dynamo.py`` (which uses ``batch_writer`` and a
random per-row ``exercise_id`` — neither works against the MongoDB adapter and
it is never run on startup). A fresh ``docker compose`` environment therefore
came up with an EMPTY exercise catalogue, so ``search_exercise_db`` and
``GET /exercises`` returned nothing and every exercise-recommender sub-agent
stalled with "No exercises found".

This script is:
  * idempotent  — ``exercise_id`` is derived deterministically from the row's
    stable ``external_id`` (falling back to the SQLite rowid), so re-running
    upserts in place instead of duplicating.
  * safe to run on every container start — it is wired into
    ``docker-entrypoint.sh`` and no-ops quickly once the collection is filled
    (pass ``--force`` to re-seed anyway).

Run manually:  python -m scripts.seed_exercises [--force]
"""

import argparse
import sqlite3
import sys

from config import DB_PATH
from tools.dynamo import get_exercises_table, get_mongo_db
from config import EXERCISES_TABLE_NAME


def _row_to_doc(row: sqlite3.Row) -> dict:
    data = {k: row[k] for k in row.keys()}
    rowid = data.pop("id", None)
    external_id = data.get("external_id")
    stable_id = str(external_id) if external_id not in (None, "") else f"row{rowid}"
    doc = {k: v for k, v in data.items() if v is not None}
    doc["exercise_id"] = f"ex-{stable_id}"
    return doc


def seed(force: bool = False) -> int:
    collection = get_mongo_db()[EXERCISES_TABLE_NAME]
    existing = collection.count_documents({})
    if existing and not force:
        print(f"[seed_exercises] '{EXERCISES_TABLE_NAME}' already has {existing} docs — skipping (use --force to re-seed).")
        return 0

    if not DB_PATH.exists():
        print(f"[seed_exercises] ERROR: legacy catalogue not found at {DB_PATH}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM exercises").fetchall()
    conn.close()

    table = get_exercises_table()
    seeded = 0
    for row in rows:
        table.put_item(Item=_row_to_doc(row))
        seeded += 1

    # payload index mirrors the DynamoDB "muscle-index" GSI — keeps the
    # per-muscle/movement_type query the sub-agents run off a collection scan.
    collection.create_index([("primary_muscle", 1), ("movement_type", 1)], name="muscle-index")

    print(f"[seed_exercises] upserted {seeded} exercises into '{EXERCISES_TABLE_NAME}' from {DB_PATH}.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-seed even if the collection is already populated")
    raise SystemExit(seed(force=parser.parse_args().force))
