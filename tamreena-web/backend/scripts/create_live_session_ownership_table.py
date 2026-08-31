"""
One-off setup script: creates the `live_session_ownership` DynamoDB table
this service owns for mapping Computer-Vision resource ids (upload ids, cv
session ids) to the user who created them. Run once per AWS
account/environment from the `backend/` directory (so app.config's
dotenv loading finds .env) — safe to re-run, skips if the table already
exists.

Usage: python scripts/create_live_session_ownership_table.py
"""

import boto3
from botocore.exceptions import ClientError

from app.config import AWS_REGION, LIVE_SESSION_OWNERSHIP_TABLE_NAME


def main() -> None:
    client = boto3.client("dynamodb", region_name=AWS_REGION)
    try:
        client.describe_table(TableName=LIVE_SESSION_OWNERSHIP_TABLE_NAME)
        print(f"Table '{LIVE_SESSION_OWNERSHIP_TABLE_NAME}' already exists — nothing to do.")
        return
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    client.create_table(
        TableName=LIVE_SESSION_OWNERSHIP_TABLE_NAME,
        KeySchema=[{"AttributeName": "resource_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "resource_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"Created table '{LIVE_SESSION_OWNERSHIP_TABLE_NAME}'.")


if __name__ == "__main__":
    main()
