import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_company(company_name):
    """Search for a company and find its website URL."""
    print(f"🔍 Searching for '{company_name}'...")

    # Try common fintech/NBFC website patterns
    search_urls = [
        f"https://www.google.com/search?q={company_name}+fintech+india+site",
    ]

    # For known companies, return direct URLs
    known_companies = {
        "paytm": "https://paytm.com",
        "phonepe": "https://www.phonepe.com",
        "razorpay": "https://razorpay.com",
        "cred": "https://cred.club",
        "groww": "https://groww.in",
        "zerodha": "https://zerodha.com",
        "bajaj finserv": "https://www.bajajfinserv.in",
        "hdfc bank": "https://www.hdfcbank.com",
        "icici bank": "https://www.icicibank.com",
        "sbi": "https://www.sbi.co.in",
        "axis bank": "https://www.axisbank.com",
        "kotak mahindra": "https://www.kotak.com",
        "muthoot finance": "https://www.muthootfinance.com",
        "bajaj finance": "https://www.bajajfinserv.in",
        "mobikwik": "https://www.mobikwik.com",
        "slice": "https://www.sliceit.com",
        "jupiter": "https://jupiter.money",
        "fi money": "https://fi.money",
        "niyo": "https://www.goniyo.com",
        "lendingkart": "https://www.lendingkart.com",
        "zestmoney": "https://www.zestmoney.in",
        "rupeek": "https://www.rupeek.com",
        "navi": "https://navi.com",
        "policybazaar": "https://www.policybazaar.com",
    }

    name_lower = company_name.lower().strip()
    for key, url in known_companies.items():
        if key in name_lower or name_lower in key:
            print(f"✅ Found: {url}")
            return url

    # Try constructing URL from company name
    clean_name = company_name.lower().replace(" ", "").replace(".", "")
    guessed_url = f"https://www.{clean_name}.com"
    print(f"🌐 Trying: {guessed_url}")
    return guessed_url


def scrape_company_website(url):
    """Scrape company website to extract text content."""
    print(f"🌐 Scraping {url}...")

    all_text = ""

    # Pages to scrape
    pages = [
        url,
        url.rstrip("/") + "/about",
        url.rstrip("/") + "/about-us",
        url.rstrip("/") + "/products",
        url.rstrip("/") + "/services",
    ]

    for page_url in pages:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Remove scripts, styles, nav, footer
                for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)

                # Clean up
                lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 10]
                page_text = " ".join(lines)

                if page_text:
                    all_text += f"\n[PAGE: {page_url}]\n{page_text[:3000]}\n"
                    print(f"  ✅ Scraped: {page_url} ({len(page_text)} chars)")
        except Exception as e:
            print(f"  ⚠️ Skipped: {page_url} ({e})")
            continue

    if not all_text:
        print("⚠️ Could not scrape website, will use company name for AI analysis")
        all_text = f"Company: {url}"

    return all_text[:8000]


def build_compliance_profile(company_name, website_text):
    """Use Groq AI to build a structured compliance profile from website content."""
    print("🧠 Building compliance profile with AI...")

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""You are an RBI regulatory compliance expert. Analyze this company's website content and build a compliance profile.

Company Name: {company_name}
Website Content:
{website_text[:6000]}

Return ONLY a valid JSON object (no extra text, no markdown) with this exact structure:
{{
    "company_name": "{company_name}",
    "company_type": "one of: Bank / NBFC / Fintech / Payment Aggregator / Microfinance / Insurance / Broker / Other",
    "rbi_registration": "type of RBI registration likely held (e.g., NBFC-ND-SI, PA License, Banking License, PPI License)",
    "services": ["list", "of", "specific", "services", "offered"],
    "regulatory_domains": ["list of RBI regulatory areas applicable, e.g., KYC/AML, Digital Lending, PPI, UPI, Data Localization, NBFC Regulations"],
    "applicable_rbi_guidelines": ["list of specific RBI Master Directions/Circulars applicable"],
    "risk_areas": ["list of key compliance risk areas"],
    "data_handling": "description of likely data handling practices (payments data, KYC data, etc.)",
    "compliance_summary": "2-3 sentence summary of the company's compliance obligations"
}}

Be specific and practical. Base your analysis on the actual website content. Return ONLY the JSON."""
        }],
        temperature=0.3
    )

    result_text = response.choices[0].message.content.strip()

    # Clean up response — extract JSON
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        profile = json.loads(result_text)
        print("✅ Compliance profile built!")
        return profile
    except json.JSONDecodeError:
        print("⚠️ Parsing AI response, building basic profile...")
        return {
            "company_name": company_name,
            "company_type": "Fintech",
            "rbi_registration": "Unknown",
            "services": ["Digital payments", "Financial services"],
            "regulatory_domains": ["KYC/AML", "Digital Lending", "Data Privacy"],
            "applicable_rbi_guidelines": ["RBI KYC Master Direction 2016"],
            "risk_areas": ["KYC compliance", "Data localization"],
            "data_handling": "Handles customer financial and personal data",
            "compliance_summary": result_text[:300]
        }


def profile_company(company_name):
    """Full pipeline: search → scrape → build profile."""
    print(f"\n{'='*60}")
    print(f"🏢 Building Compliance Profile: {company_name}")
    print(f"{'='*60}")

    # Step 1: Find website
    url = search_company(company_name)

    # Step 2: Scrape website
    website_text = scrape_company_website(url)

    # Step 3: Build profile with AI
    profile = build_compliance_profile(company_name, website_text)
    profile["website_url"] = url

    return profile


# TEST
if __name__ == "__main__":
    profile = profile_company("Paytm")
    print("\n" + "="*60)
    print("📋 COMPLIANCE PROFILE:")
    print("="*60)
    print(json.dumps(profile, indent=2))
