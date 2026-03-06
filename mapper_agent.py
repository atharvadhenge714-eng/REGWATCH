import chromadb
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize ChromaDB
chroma_client = chromadb.Client()
profile_collection = chroma_client.get_or_create_collection("company_profile")


def index_company_profile(profile):
    """Index a company profile into ChromaDB for comparison."""
    print("📊 Indexing company profile in ChromaDB...")

    # Build documents from profile
    documents = []
    metadatas = []
    ids = []

    # Index services
    for i, service in enumerate(profile.get("services", [])):
        documents.append(f"Company service: {service}")
        metadatas.append({"type": "service", "company": profile["company_name"]})
        ids.append(f"service_{i}")

    # Index regulatory domains
    for i, domain in enumerate(profile.get("regulatory_domains", [])):
        documents.append(f"Regulatory domain: {domain}")
        metadatas.append({"type": "regulatory_domain", "company": profile["company_name"]})
        ids.append(f"domain_{i}")

    # Index risk areas
    for i, risk in enumerate(profile.get("risk_areas", [])):
        documents.append(f"Compliance risk area: {risk}")
        metadatas.append({"type": "risk_area", "company": profile["company_name"]})
        ids.append(f"risk_{i}")

    # Index applicable guidelines
    for i, guideline in enumerate(profile.get("applicable_rbi_guidelines", [])):
        documents.append(f"Applicable RBI guideline: {guideline}")
        metadatas.append({"type": "guideline", "company": profile["company_name"]})
        ids.append(f"guideline_{i}")

    # Index overall profile summary
    documents.append(
        f"Company: {profile['company_name']}. Type: {profile.get('company_type', 'Fintech')}. "
        f"Registration: {profile.get('rbi_registration', 'N/A')}. "
        f"Data handling: {profile.get('data_handling', 'N/A')}. "
        f"Summary: {profile.get('compliance_summary', 'N/A')}"
    )
    metadatas.append({"type": "summary", "company": profile["company_name"]})
    ids.append("summary_0")

    # Clear existing data and add new
    try:
        existing = profile_collection.get()
        if existing["ids"]:
            profile_collection.delete(ids=existing["ids"])
    except:
        pass

    profile_collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Indexed {len(documents)} profile items!")


def compare_regulation_with_profile(regulation_text, company_profile):
    """Use AI to compare an RBI regulation against company profile and find compliance gaps."""
    print("🔍 Comparing regulation with company profile...")

    # Semantic search to find relevant profile items
    results = profile_collection.query(
        query_texts=[regulation_text[:1000]],
        n_results=5
    )

    matched_items = results["documents"][0] if results["documents"] else []
    matched_types = [m["type"] for m in results["metadatas"][0]] if results["metadatas"] else []

    # Use AI for detailed comparison
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""You are an RBI compliance expert. Compare this new RBI regulation with the company's profile and determine the compliance impact.

## New RBI Regulation:
{regulation_text[:3000]}

## Company Profile:
- Company: {company_profile.get('company_name', 'Unknown')}
- Type: {company_profile.get('company_type', 'Fintech')}
- RBI Registration: {company_profile.get('rbi_registration', 'N/A')}
- Services: {', '.join(company_profile.get('services', []))}
- Regulatory Domains: {', '.join(company_profile.get('regulatory_domains', []))}
- Risk Areas: {', '.join(company_profile.get('risk_areas', []))}
- Data Handling: {company_profile.get('data_handling', 'N/A')}

## Matched Profile Items (from semantic search):
{chr(10).join(f'- [{t}] {item}' for item, t in zip(matched_items, matched_types))}

Return ONLY a valid JSON object (no markdown, no extra text):
{{
    "is_applicable": true or false,
    "applicability_reason": "why this regulation applies or doesn't apply to this company",
    "impact_level": "High / Medium / Low / Not Applicable",
    "affected_services": ["list of company services affected"],
    "affected_domains": ["list of regulatory domains affected"],
    "compliance_gaps": [
        {{
            "gap": "description of the compliance gap",
            "current_state": "what the company likely does now",
            "required_state": "what the regulation requires",
            "risk": "High / Medium / Low"
        }}
    ],
    "immediate_actions": ["list of immediate actions needed"],
    "policy_changes_needed": ["list of internal policies that need updating"]
}}"""
        }],
        temperature=0.3
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        comparison = json.loads(result_text)
        print(f"✅ Comparison complete! Impact: {comparison.get('impact_level', 'Unknown')}")
        return comparison
    except json.JSONDecodeError:
        print("⚠️ Could not parse comparison, returning raw analysis")
        return {
            "is_applicable": True,
            "applicability_reason": "Could not determine — manual review needed",
            "impact_level": "Medium",
            "affected_services": company_profile.get("services", [])[:3],
            "affected_domains": company_profile.get("regulatory_domains", [])[:3],
            "compliance_gaps": [{"gap": result_text[:300], "current_state": "Unknown", "required_state": "As per regulation", "risk": "Medium"}],
            "immediate_actions": ["Review the regulation manually"],
            "policy_changes_needed": ["Review all applicable policies"]
        }


# TEST
if __name__ == "__main__":
    test_profile = {
        "company_name": "Paytm",
        "company_type": "Fintech",
        "rbi_registration": "PA License, PPI License",
        "services": ["UPI Payments", "Paytm Wallet", "Paytm Postpaid", "Insurance", "Mutual Funds"],
        "regulatory_domains": ["KYC/AML", "PPI", "UPI", "Digital Lending", "Payment Aggregator"],
        "risk_areas": ["KYC compliance", "PPI regulations", "Data localization"],
        "data_handling": "Handles payment data, KYC data, transaction logs",
        "compliance_summary": "Major fintech with PA and PPI licenses, subject to KYC, AML, PPI, and PA regulations."
    }

    index_company_profile(test_profile)

    test_regulation = "RBI mandates easing of KYC norms for low-risk customers, allowing continued transactions with pending KYC until June 2026."
    result = compare_regulation_with_profile(test_regulation, test_profile)
    print(json.dumps(result, indent=2))