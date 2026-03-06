import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def find_company_website(company_name):
    """Use AI to determine the correct website URL for an Indian company."""
    print(f"🔍 Finding real website for '{company_name}'...")

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""What is the official website URL of the Indian company "{company_name}"?

If it is a bank, NBFC, fintech, or financial services company in India, return the exact official website URL.

Return ONLY the URL, nothing else. Example: https://www.paytm.com
If you don't know the exact URL, return your best guess of the official domain.

Company: {company_name}
URL:"""
        }],
        temperature=0.1,
        max_tokens=100
    )

    url = response.choices[0].message.content.strip()

    # Clean up — extract URL from response
    url_match = re.search(r'https?://[^\s<>"\']+', url)
    if url_match:
        url = url_match.group(0).rstrip("/.,;:)")

    # Ensure it starts with https://
    if not url.startswith("http"):
        url = "https://" + url

    print(f"✅ Found: {url}")
    return url


def scrape_company_website(url):
    """Scrape multiple pages of a company website for real content."""
    print(f"🌐 Scraping {url}...")
    all_text = ""

    # Key pages to try
    base = url.rstrip("/")
    pages_to_try = [
        base,
        base + "/about",
        base + "/about-us",
        base + "/about/about-us",
        base + "/products",
        base + "/services",
        base + "/what-we-do",
        base + "/our-products",
        base + "/company",
    ]

    scraped_count = 0
    for page_url in pages_to_try:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=8, allow_redirects=True)
            if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
                soup = BeautifulSoup(response.text, "html.parser")

                # Remove non-content elements
                for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                          "noscript", "iframe", "svg", "form"]):
                    tag.decompose()

                # Get text from meaningful elements
                text_parts = []
                for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "span", "div"]):
                    txt = element.get_text(strip=True)
                    if txt and len(txt) > 15 and not txt.startswith("{") and "cookie" not in txt.lower():
                        text_parts.append(txt)

                page_text = "\n".join(list(dict.fromkeys(text_parts)))  # Remove duplicates

                if page_text and len(page_text) > 100:
                    all_text += f"\n--- PAGE: {page_url} ---\n{page_text[:3000]}\n"
                    scraped_count += 1
                    print(f"  ✅ {page_url} ({len(page_text)} chars)")

                    if scraped_count >= 3:  # Enough pages
                        break
        except Exception:
            continue

    if not all_text or len(all_text) < 200:
        print(f"⚠️ Limited content from website, AI will use company name for analysis")
        all_text = f"Company name: {url}. Could not scrape detailed website content."

    return all_text[:10000]


def build_compliance_profile(company_name, website_text):
    """Use Groq AI to analyze real website content and build a structured compliance profile."""
    print("🧠 Analyzing company with AI...")

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""You are an RBI regulatory compliance expert. Analyze this company's REAL website content and build an accurate compliance profile based on what they ACTUALLY do.

Company Name: {company_name}

Website Content (scraped from their real website):
{website_text[:7000]}

Based on the ACTUAL content from their website, return ONLY a valid JSON object (no extra text, no markdown):
{{
    "company_name": "{company_name}",
    "company_type": "one of: Commercial Bank / Small Finance Bank / NBFC / NBFC-MFI / Fintech / Payment Aggregator / Payment Bank / Insurance / Broker / Wallet Operator / Digital Lender / Other",
    "rbi_registration": "the likely type of RBI registration they hold based on their services",
    "services": ["list every specific product/service you found on their website"],
    "regulatory_domains": ["list ALL RBI regulatory areas applicable based on their actual services"],
    "applicable_rbi_guidelines": ["list specific RBI Master Directions and Circulars that apply to this company based on their services"],
    "risk_areas": ["list specific compliance risk areas for this company"],
    "data_handling": "describe what kind of customer data they likely handle based on their services",
    "compliance_summary": "3-4 sentence summary of this company's regulatory obligations based on what they actually do"
}}

IMPORTANT: Base everything on the ACTUAL website content. Do NOT give generic answers. Each company should have different services, risks, and applicable regulations based on what they really do.

Return ONLY the JSON."""
        }],
        temperature=0.2
    )

    result_text = response.choices[0].message.content.strip()

    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        profile = json.loads(result_text)
        print(f"✅ Profile built for {profile.get('company_name', company_name)}!")
        return profile
    except json.JSONDecodeError:
        print("⚠️ Parsing error, building basic profile")
        return {
            "company_name": company_name,
            "company_type": "Fintech",
            "rbi_registration": "Unknown — manual verification needed",
            "services": ["Financial services"],
            "regulatory_domains": ["KYC/AML", "Data Privacy"],
            "applicable_rbi_guidelines": ["RBI KYC Master Direction 2016"],
            "risk_areas": ["Regulatory compliance"],
            "data_handling": "Handles customer financial data",
            "compliance_summary": result_text[:300]
        }


def profile_company(company_name):
    """Full autonomous pipeline: find website → scrape → build profile."""
    print(f"\n{'='*60}")
    print(f"🏢 Building Compliance Profile: {company_name}")
    print(f"{'='*60}")

    # Step 1: Find real website via AI
    url = find_company_website(company_name)

    # Step 2: Scrape real website content
    website_text = scrape_company_website(url)

    # Step 3: Build profile from real content
    profile = build_compliance_profile(company_name, website_text)
    profile["website_url"] = url

    return profile


# TEST
if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Razorpay"
    profile = profile_company(name)
    print("\n" + "="*60)
    print("📋 COMPLIANCE PROFILE:")
    print("="*60)
    print(json.dumps(profile, indent=2))
