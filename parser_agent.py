from groq import Groq
import pypdf
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_rbi_circular(pdf_path):
    print("📄 Reading PDF...")
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    print("🤖 Sending to Groq AI...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""You are an RBI regulatory compliance expert.

Analyze this RBI circular and return ONLY a JSON object:
{{
    "title": "title of the circular",
    "main_change": "what regulation changed in simple words",
    "deadline": "compliance deadline or Not specified",
    "affected_domains": ["list", "of", "affected", "areas"],
    "severity": "High or Medium or Low",
    "action_required": "one sentence on what companies must do"
}}

Return ONLY the JSON. No extra text.

Circular:
{text[:4000]}"""
        }]
    )

    print("✅ PDF Parsed!")
    return response.choices[0].message.content


# TEST
if __name__ == "__main__":
    print(parse_rbi_circular("rbi_circular.pdf"))