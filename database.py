import mysql.connector
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("gateway01.ap-southeast-1.prod.aws.tidbcloud.com"),
        port=int(os.getenv("4000")),
        user=os.getenv("3dXmRdVBjtwRrfC.root"),
        password=os.getenv("pQFq9s7BwWrJegiK"),
        database=os.getenv("regwatch_db"),
        ssl_ca=os.getenv("D:\Arya\RegWatch\ca.pem"),  # TiDB Cloud needs SSL
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )

def save_report(circular_name, parsed_result, action_plan):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO compliance_reports 
            (id, circular_name, parsed_result, action_plan, date_analyzed)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            str(uuid.uuid4()),
            str(circular_name)[:500],
            str(parsed_result)[:5000],
            str(action_plan),
            datetime.now().strftime("%Y-%m-%d")
        )

        cursor.execute(sql, values)
        conn.commit()
        print("✅ Saved to TiDB!")

    except Exception as e:
        print(f"❌ Save failed: {e}")

    finally:
        cursor.close()
        conn.close()