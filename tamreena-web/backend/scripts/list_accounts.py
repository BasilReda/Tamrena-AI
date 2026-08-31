import os
import boto3
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = os.getenv("AWS_REGION", "eu-north-1")
table_name = os.getenv("DYNAMODB_TABLE_NAME", "workout_users")

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region,
)

dynamodb = session.resource("dynamodb")
table = dynamodb.Table(table_name)

try:
    response = table.scan()
    users = response.get("Items", [])
    print(f"\n========================================================")
    print(f"📊 DynamoDB Table: {table_name} ({region})")
    print(f"👥 Total User Accounts Found: {len(users)}")
    print(f"========================================================\n")

    for i, u in enumerate(users, 1):
        user_id = u.get("user_id", "N/A")
        email = u.get("email") or u.get("username") or "N/A"
        name = u.get("name") or u.get("display_name") or u.get("given_name") or "N/A"
        auth_provider = u.get("auth_provider", "local")
        created_at = u.get("created_at", "N/A")

        print(f"[{i}] User ID:       {user_id}")
        print(f"    Email/Username: {email}")
        print(f"    Name:           {name}")
        print(f"    Provider:       {auth_provider}")
        print(f"    Created At:     {created_at}")
        print("-" * 56)

except Exception as e:
    print(f"❌ Error querying DynamoDB: {e}")
