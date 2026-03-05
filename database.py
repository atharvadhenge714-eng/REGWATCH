from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from dotenv import load_dotenv
import os

load_dotenv()

client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("69a913bf003047e6b17a"))
client.set_key(os.getenv("standard_b37358674baa1eded5cecfd9b41d3b8be648d3ad6d1c7c6ebe0df1b4daf60d35b504fc23f8da45e1271e204a86623e0edb4f0b1ca34670d8d22c467f906fe2c66b425239f00858cd50bad53e9dc19956a280149c8a6688ab4450f46f0013ccf7d7022a6a1b98d18bc4f9cb0acde35fa792a92df9a669137b01bfb5a44c5a36d6"))

databases = Databases(client)

def save_report(circular_name, parsed_result, action_plan):
    try:
        databases.create_document(
            database_id=os.getenv("APPWRITE_DATABASE_ID"),
            collection_id=os.getenv("APPWRITE_TABLE_ID"),
            document_id=ID.unique(),
            data={
                "circular_name": str(circular_name),
                "parsed_result": str(parsed_result),
                "action_plan": str(action_plan),
                "date_analyzed": "2025-03-06"
            }
        )
        print("✅ Saved to Appwrite!")
    except Exception as e:
        print(f"❌ Save failed: {e}")