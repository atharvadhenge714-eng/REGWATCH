from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_action_plan(parsed_circular, affected_policies):
    """Generate a comprehensive, structured compliance action plan."""
    print("📋 Generating compliance action plan...")

    # Format affected policies for the AI
    if isinstance(affected_policies, list) and affected_policies:
        if isinstance(affected_policies[0], dict):
            policies_text = "\n".join(
                f"  {i+1}. [{p['policy_name']}] (Dept: {p['department']}) — Regulatory Ref: {p['regulatory_reference']}\n"
                f"     Current Version: v{p['version']} | Last Updated: {p['last_updated']}\n"
                f"     Content: {p['matched_content'][:200]}"
                for i, p in enumerate(affected_policies)
            )
        else:
            policies_text = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(affected_policies))
    else:
        policies_text = str(affected_policies)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""You are the Chief Compliance Officer at an Indian fintech/NBFC company. A new RBI regulation has been issued and you must create an ACTIONABLE compliance response.

## New RBI Regulation:
{parsed_circular}

## Company Policies Affected:
{policies_text}

Generate a COMPREHENSIVE compliance action plan in the following exact format. Be specific, reference actual policy names, and provide realistic deadlines.

---

## 📊 COMPLIANCE GAP ANALYSIS

For each affected policy, identify:
- **Current State**: What the existing policy says
- **Required State**: What the new regulation demands
- **Gap**: Specific differences that need to be addressed
- **Risk Level**: 🔴 High / 🟡 Medium / 🟢 Low

---

## ⚡ IMMEDIATE ACTIONS (Within 7 Days)

| # | Action Item | Owner | Deadline | Priority |
|---|------------|-------|----------|----------|
| 1 | [specific task] | [Engineering/Legal/Compliance/Product/Operations] | [date] | 🔴/🟡/🟢 |

List 4-5 specific, actionable tasks.

---

## 📝 POLICY AMENDMENTS REQUIRED

For each affected policy, draft the specific amendments:
- **Policy Name**: [name]
- **Section to Amend**: [specific section]
- **Current Wording**: [what it says now]
- **Proposed Wording**: [what it should say]

---

## 🎫 AUTO-GENERATED COMPLIANCE TASKS

| Ticket ID | Task Title | Assignee (Team) | Sprint | Story Points | Acceptance Criteria |
|-----------|-----------|-----------------|--------|-------------|---------------------|
| REG-001 | [task] | [team] | Current/Next | [1-8] | [criteria] |

Create 4-5 tickets in this table.

---

## 📧 STAKEHOLDER NOTIFICATIONS

Draft notification emails for affected teams:
- **To**: [Team/Department]
- **Subject**: [Compliance Alert subject line]
- **Key Message**: [2-3 sentence summary of what they need to do]

---

## ⏰ COMPLIANCE TIMELINE

| Phase | Action | Deadline | Status |
|-------|--------|----------|--------|
| Phase 1 | [Immediate Assessment] | [Week 1] | 🔲 Pending |
| Phase 2 | [Policy Drafting] | [Week 2-3] | 🔲 Pending |
| Phase 3 | [Implementation] | [Week 4-8] | 🔲 Pending |
| Phase 4 | [Testing & Audit] | [Week 8-10] | 🔲 Pending |
| Phase 5 | [Go-Live & Reporting] | [by deadline] | 🔲 Pending |

---

## ⚠️ RISK ASSESSMENT

- **Penalty if non-compliant**: [specific RBI penalty]
- **Reputational risk**: [impact assessment]
- **Operational risk**: [business continuity impact]
- **Recommended board escalation**: Yes/No with justification

Be practical, specific to Indian fintech/NBFC operations, and reference real RBI guidelines.
Use markdown formatting throughout."""
        }]
    )

    print("✅ Action Plan Generated!")
    return response.choices[0].message.content


def generate_gap_analysis(regulation_text, policy_text):
    """Generate a focused gap analysis between a regulation and a specific policy."""
    print("🔍 Generating gap analysis...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Compare this new RBI regulation with the existing company policy and identify compliance gaps.

New Regulation: {regulation_text[:2000]}

Existing Policy: {policy_text[:2000]}

List each gap as:
1. **Gap**: [description]
   - **Current**: [what policy says]
   - **Required**: [what regulation requires]
   - **Action**: [what to do]
   - **Risk**: 🔴 High / 🟡 Medium / 🟢 Low

Be specific and practical."""
        }]
    )

    return response.choices[0].message.content


def generate_quick_scan(circulars, company_profile):
    """Quick scan all circulars to identify which ones are relevant to the company."""
    print("🔍 Quick scanning all circulars for relevance...")

    circulars_text = "\n".join(
        f"{i+1}. [{c.get('date', '')}] {c['title']} — {c.get('summary', '')}"
        for i, c in enumerate(circulars)
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""You are an RBI compliance expert. A company needs to know which of these recent RBI circulars are relevant to them.

Company: {company_profile.get('company_name', 'Unknown')}
Type: {company_profile.get('company_type', 'Fintech')}
Services: {', '.join(company_profile.get('services', []))}
Regulatory Domains: {', '.join(company_profile.get('regulatory_domains', []))}

Recent RBI Circulars:
{circulars_text}

Return ONLY a valid JSON array (no markdown, no extra text). For each circular, return:
[
    {{
        "circular_index": 0,
        "title": "circular title",
        "is_relevant": true/false,
        "relevance_reason": "why it matters or doesn't to this company",
        "impact_level": "High / Medium / Low / Not Applicable",
        "urgency": "Immediate / This Quarter / Informational"
    }}
]

Return the JSON array ONLY."""
        }],
        temperature=0.3
    )

    result_text = response.choices[0].message.content.strip()

    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    try:
        scan_results = json.loads(result_text)
        relevant = sum(1 for r in scan_results if r.get("is_relevant", False))
        print(f"✅ Scan complete! {relevant}/{len(scan_results)} circulars relevant to company.")
        return scan_results
    except json.JSONDecodeError:
        print("⚠️ Could not parse scan results")
        return [{"circular_index": i, "title": c["title"], "is_relevant": True,
                 "relevance_reason": "Manual review needed", "impact_level": "Medium",
                 "urgency": "This Quarter"} for i, c in enumerate(circulars)]


# TEST
if __name__ == "__main__":
    plan = generate_action_plan(
        "RBI mandates all NBFCs to complete re-KYC for existing customers within 6 months. "
        "Enhanced due diligence required for high-risk customers with video KYC verification.",
        [
            {
                "policy_id": "POL-KYC-001",
                "policy_name": "KYC & Customer Due Diligence Policy",
                "department": "Compliance & Onboarding",
                "regulatory_reference": "RBI KYC Master Direction 2016",
                "version": "4.2",
                "last_updated": "March 2025",
                "matched_content": "Re-KYC triggered every 2 years for high-risk and 10 years for low-risk customers..."
            },
            {
                "policy_id": "POL-AML-002",
                "policy_name": "AML & CFT Policy",
                "department": "Compliance & Risk",
                "regulatory_reference": "PMLA 2002",
                "version": "3.1",
                "last_updated": "January 2025",
                "matched_content": "Customer screening against UNSC sanctions lists performed at onboarding..."
            }
        ]
    )
    print(plan)