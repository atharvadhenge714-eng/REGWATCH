import streamlit as st
import json
import os
import tempfile
from company_profiler import profile_company
from fetch_agent import fetch_latest_circulars, fetch_circular_text
from parser_agent import parse_rbi_circular
from mapper_agent import index_company_profile, compare_regulation_with_profile
from action_agent import generate_compliance_alert, generate_quick_scan
from database import save_report

# PAGE CONFIG
st.set_page_config(
    page_title="RegWatch — Agentic RBI Compliance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== CSS =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background: #080815;
        font-family: 'Inter', sans-serif;
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 25px 0 10px;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero p {
        color: #475569;
        font-size: 0.95rem;
        margin-top: 6px;
    }

    /* Glass card */
    .gcard {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 14px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }

    /* Stat */
    .stat {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(168, 85, 247, 0.04));
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }
    .stat .val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .stat .lbl {
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 2px;
    }

    /* Profile card */
    .profile-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        padding: 20px;
        margin: 10px 0;
    }
    .profile-card h3 {
        color: #c4b5fd;
        margin: 0 0 12px;
        font-size: 1.2rem;
    }
    .profile-item {
        color: #94a3b8;
        font-size: 0.9rem;
        margin: 6px 0;
        line-height: 1.6;
    }
    .profile-item strong {
        color: #e2e8f0;
    }

    /* Circular row */
    .circ-row {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 6px 0;
        transition: all 0.2s;
    }
    .circ-row:hover {
        border-color: rgba(99, 102, 241, 0.25);
    }
    .circ-title {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .circ-meta {
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 3px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .badge-high { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .badge-medium { background: rgba(234,179,8,0.15); color: #facc15; border: 1px solid rgba(234,179,8,0.3); }
    .badge-low { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-na { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
    .badge-cat { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); }

    /* Impact card */
    .impact-high {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 14px;
        padding: 18px;
        margin: 8px 0;
    }
    .impact-medium {
        background: rgba(234, 179, 8, 0.06);
        border: 1px solid rgba(234, 179, 8, 0.2);
        border-radius: 14px;
        padding: 18px;
        margin: 8px 0;
    }
    .impact-low {
        background: rgba(34, 197, 94, 0.06);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 14px;
        padding: 18px;
        margin: 8px 0;
    }

    /* Step indicator */
    .step {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(99, 102, 241, 0.05);
        border-left: 3px solid #6366f1;
        border-radius: 0 10px 10px 0;
        margin: 8px 0;
    }
    .step .num {
        background: linear-gradient(135deg, #6366f1, #7c3aed);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step .txt {
        color: #94a3b8;
        font-size: 0.85rem;
    }
    .step .txt strong {
        color: #e2e8f0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #0a0a1d; border-right: 1px solid rgba(99,102,241,0.08); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ===================== HEADER =====================
st.markdown("""
<div class="hero">
    <h1>🛡️ RegWatch</h1>
    <p>Agentic AI for RBI Compliance & Policy Adaptation</p>
</div>
""", unsafe_allow_html=True)


# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### 🛡️ RegWatch")
    st.caption("Fully Autonomous Compliance Intelligence")
    st.divider()

    st.markdown("**Autonomous Pipeline**")
    steps = [
        ("1", "Enter company name"),
        ("2", "AI scrapes company website"),
        ("3", "AI extracts services & builds profile"),
        ("4", "System fetches latest RBI circulars"),
        ("5", "AI scans circulars for relevance"),
        ("6", "AI compares regulation vs profile"),
        ("7", "Compliance alert auto-generated"),
    ]
    for num, txt in steps:
        st.markdown(f"""
        <div class="step">
            <div class="num">{num}</div>
            <div class="txt">{txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if "company_profile" in st.session_state:
        p = st.session_state.company_profile
        st.success(f"🏢 {p['company_name']}", icon="✅")
        st.caption(f"Type: {p.get('company_type', 'N/A')}")
        st.caption(f"Services: {len(p.get('services', []))}")
    else:
        st.info("No company profiled yet")

    st.divider()
    st.caption("Team Apex Devs — The Paradox 2025")


# ===================== MAIN =====================

# STEP 1: Company Setup
if "company_profile" not in st.session_state:
    st.markdown("### Step 1 — Enter Your Company Name")
    st.caption("The AI will search the web, scrape the website, and build a compliance profile automatically.")

    col_in1, col_in2 = st.columns([3, 1])
    with col_in1:
        company_name = st.text_input("Company Name", placeholder="e.g., Paytm, PhonePe, CRED, Razorpay, HDFC Bank...", label_visibility="collapsed")
    with col_in2:
        go_btn = st.button("🚀 Build Profile", type="primary", use_container_width=True)

    # OR upload PDF
    st.markdown("")
    with st.expander("📄 Or upload a company policy document instead"):
        policy_pdf = st.file_uploader("Upload company policy PDF", type=["pdf", "txt"], key="policy_up")
        policy_name = st.text_input("Company/Policy name", key="policy_name_in")
        if policy_pdf and policy_name and st.button("Build Profile from Document"):
            with st.spinner("Processing document..."):
                if policy_pdf.name.endswith(".txt"):
                    doc_text = policy_pdf.read().decode("utf-8")
                else:
                    import pypdf
                    reader = pypdf.PdfReader(policy_pdf)
                    doc_text = " ".join(page.extract_text() for page in reader.pages)

                from company_profiler import build_compliance_profile
                profile = build_compliance_profile(policy_name, doc_text)
                profile["website_url"] = "Uploaded document"
                index_company_profile(profile)
                st.session_state.company_profile = profile
                st.rerun()

    if go_btn and company_name:
        progress = st.progress(0, text="🔍 Searching for company...")

        with st.status("🤖 Autonomous Company Profiling...", expanded=True) as status:
            st.write(f"🔍 Searching for {company_name}...")
            progress.progress(15, text="Searching company website...")

            st.write("🌐 Scraping company website...")
            progress.progress(40, text="Scraping website pages...")

            st.write("🧠 Analyzing with AI (LLaMA 3.3 70B)...")
            progress.progress(65, text="Building compliance profile...")

            profile = profile_company(company_name)

            st.write("📊 Indexing profile in ChromaDB...")
            index_company_profile(profile)
            progress.progress(100, text="✅ Profile ready!")

            status.update(label=f"✅ Profile Built — {company_name}", state="complete")

        st.session_state.company_profile = profile
        st.rerun()

# Main app after profile is built
else:
    profile = st.session_state.company_profile

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏢 Company Profile", "🌐 RBI Circulars & Scan", "📄 Upload Circular"])

    # ============= TAB 1: COMPANY PROFILE =============
    with tab1:
        col_p1, col_p2 = st.columns([2, 1])

        with col_p1:
            st.markdown(f"""
            <div class="profile-card">
                <h3>🏢 {profile['company_name']}</h3>
                <div class="profile-item"><strong>Company Type:</strong> {profile.get('company_type', 'N/A')}</div>
                <div class="profile-item"><strong>RBI Registration:</strong> {profile.get('rbi_registration', 'N/A')}</div>
                <div class="profile-item"><strong>Website:</strong> {profile.get('website_url', 'N/A')}</div>
                <div class="profile-item"><strong>Data Handling:</strong> {profile.get('data_handling', 'N/A')}</div>
                <div class="profile-item"><strong>Compliance Summary:</strong> {profile.get('compliance_summary', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            services = profile.get("services", [])
            st.markdown(f"""
            <div class="stat"><div class="val">{len(services)}</div><div class="lbl">Services Detected</div></div>
            """, unsafe_allow_html=True)
            st.markdown("")
            domains = profile.get("regulatory_domains", [])
            st.markdown(f"""
            <div class="stat"><div class="val">{len(domains)}</div><div class="lbl">Regulatory Domains</div></div>
            """, unsafe_allow_html=True)
            st.markdown("")
            risks = profile.get("risk_areas", [])
            st.markdown(f"""
            <div class="stat"><div class="val">{len(risks)}</div><div class="lbl">Risk Areas</div></div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Services, Domains, Risks
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown("**🔧 Services**")
            for s in services:
                st.markdown(f"- {s}")
        with col_s2:
            st.markdown("**📋 Regulatory Domains**")
            for d in domains:
                st.markdown(f"- {d}")
        with col_s3:
            st.markdown("**⚠️ Risk Areas**")
            for r in risks:
                st.markdown(f"- {r}")

        # Applicable guidelines
        st.markdown("")
        with st.expander("📖 Applicable RBI Guidelines"):
            for g in profile.get("applicable_rbi_guidelines", []):
                st.markdown(f"- {g}")

        st.divider()
        if st.button("🔄 Re-profile Company", key="reprofile"):
            st.session_state.pop("company_profile", None)
            st.session_state.pop("circulars", None)
            st.session_state.pop("scan_results", None)
            st.rerun()


    # ============= TAB 2: RBI CIRCULARS & AUTO SCAN =============
    with tab2:
        st.markdown("#### 🌐 Latest RBI Circulars — Autonomous Relevance Scan")

        # Fetch circulars
        if "circulars" not in st.session_state:
            with st.spinner("Fetching latest RBI circulars..."):
                st.session_state.circulars = fetch_latest_circulars()

        circulars = st.session_state.circulars

        # Auto scan button
        col_scan1, col_scan2 = st.columns([1, 1])
        with col_scan1:
            scan_btn = st.button("⚡ Auto-Scan All Circulars for Relevance", type="primary", use_container_width=True)
        with col_scan2:
            if st.button("🔄 Refresh Circulars", use_container_width=True):
                st.session_state.pop("circulars", None)
                st.session_state.pop("scan_results", None)
                st.rerun()

        # Run auto scan
        if scan_btn:
            with st.status("🤖 AI scanning all circulars against your company profile...", expanded=True) as status:
                st.write(f"Analyzing {len(circulars)} circulars for relevance to {profile['company_name']}...")
                scan_results = generate_quick_scan(circulars, profile)
                st.session_state.scan_results = scan_results
                status.update(label="✅ Scan Complete", state="complete")

        st.divider()

        # Display circulars with scan results
        scan_results = st.session_state.get("scan_results", None)
        has_scan = scan_results is not None

        for i, c in enumerate(circulars):
            # Get scan result for this circular
            scan = None
            if has_scan and i < len(scan_results):
                scan = scan_results[i]

            col_c1, col_c2, col_c3 = st.columns([5, 1, 1])

            with col_c1:
                # Title and metadata
                impact = scan.get("impact_level", "") if scan else ""
                badge_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(impact, "badge-na")

                relevance_html = ""
                if scan:
                    is_rel = scan.get("is_relevant", False)
                    if is_rel:
                        relevance_html = f' <span class="badge {badge_class}">{impact} Impact</span>'
                    else:
                        relevance_html = ' <span class="badge badge-na">Not Applicable</span>'

                st.markdown(f"""
                <div class="circ-row">
                    <div class="circ-title">{c['title']}{relevance_html}</div>
                    <div class="circ-meta">📅 {c.get('date', 'N/A')} &nbsp; <span class="badge badge-cat">{c.get('category', 'RBI')}</span></div>
                </div>
                """, unsafe_allow_html=True)

                if scan and scan.get("is_relevant"):
                    st.caption(f"💡 {scan.get('relevance_reason', '')}")

            with col_c2:
                if scan and scan.get("is_relevant"):
                    urgency = scan.get("urgency", "")
                    urg_icon = {"Immediate": "🔴", "This Quarter": "🟡", "Informational": "🟢"}.get(urgency, "⚪")
                    st.caption(f"{urg_icon} {urgency}")

            with col_c3:
                if st.button("Analyze →", key=f"deep_{i}", use_container_width=True):
                    st.session_state.analyzing_circular = c
                    st.session_state.analyzing_index = i

        # Deep analysis of selected circular
        if "analyzing_circular" in st.session_state:
            c = st.session_state.analyzing_circular
            st.divider()
            st.markdown(f"### 🔍 Deep Analysis: {c['title']}")

            progress = st.progress(0, text="Starting analysis...")

            # Step 1: Fetch content
            with st.status("📄 Fetching circular content...", expanded=True) as status:
                content = fetch_circular_text(c["url"])
                progress.progress(25, text="Content fetched")
                status.update(label="✅ Content Fetched", state="complete")

            # Step 2: Compare with profile
            with st.status("🎯 Comparing with company profile...", expanded=True) as status:
                st.write(f"Comparing regulation against {profile['company_name']}'s profile...")
                comparison = compare_regulation_with_profile(content, profile)
                progress.progress(50, text="Comparison complete")
                status.update(label="✅ Comparison Complete", state="complete")

            # Show comparison results
            impact = comparison.get("impact_level", "Unknown")
            impact_class = {"High": "impact-high", "Medium": "impact-medium", "Low": "impact-low"}.get(impact, "impact-low")

            st.markdown(f"""
            <div class="{impact_class}">
                <strong>Impact Level:</strong> {impact} &nbsp;&nbsp;
                <strong>Applicable:</strong> {'✅ Yes' if comparison.get('is_applicable') else '❌ No'}<br>
                <span style="color:#94a3b8; font-size:0.9rem;">{comparison.get('applicability_reason', '')}</span>
            </div>
            """, unsafe_allow_html=True)

            if comparison.get("compliance_gaps"):
                st.markdown("**Compliance Gaps Found:**")
                for gap in comparison["compliance_gaps"]:
                    st.warning(f"**{gap.get('gap', '')}** — Risk: {gap.get('risk', 'Medium')}")
                    st.caption(f"Current: {gap.get('current_state', '')} → Required: {gap.get('required_state', '')}")

            st.divider()

            # Step 3: Generate alert
            with st.status("⚡ Generating autonomous compliance alert...", expanded=True) as status:
                st.write("Creating gap analysis...")
                st.write("Drafting policy amendments...")
                st.write("Generating JIRA tickets & notifications...")
                circular_info = {"title": c["title"], "date": c.get("date", ""), "content": content}
                alert = generate_compliance_alert(circular_info, comparison, profile)
                progress.progress(100, text="✅ Alert generated")
                status.update(label="✅ Compliance Alert Ready", state="complete")

            st.markdown("### 🚨 Compliance Alert")
            st.markdown(alert)

            # Download
            st.download_button(
                "📥 Download Compliance Report",
                data=f"# Compliance Alert — {profile['company_name']}\n## Circular: {c['title']}\n\n{alert}",
                file_name=f"compliance_alert_{profile['company_name'].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )

            try:
                save_report(c["title"], json.dumps(comparison), alert)
                st.success("💾 Saved to database")
            except Exception as e:
                st.info(f"DB: {e}")

            st.success(f"✅ Autonomous analysis complete for {profile['company_name']}")

            if st.button("← Back to Circulars"):
                st.session_state.pop("analyzing_circular", None)
                st.rerun()


    # ============= TAB 3: UPLOAD CIRCULAR =============
    with tab3:
        st.markdown("#### 📄 Upload a Custom RBI Circular")
        st.caption(f"Upload any circular PDF — it will be analyzed against {profile['company_name']}'s profile")

        uploaded = st.file_uploader("Upload PDF", type="pdf", key="custom_pdf")

        if uploaded and st.button("🚀 Analyze Against Company Profile", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            progress = st.progress(0, text="Processing...")

            with st.status("🔍 Parsing circular...", expanded=True) as status:
                parsed = parse_rbi_circular(tmp_path)
                progress.progress(30)
                status.update(label="✅ Parsed", state="complete")

            st.markdown("**Extracted Regulation:**")
            st.markdown(f"""<div class="gcard"><p style="color:#cbd5e1; font-size:0.9rem;">{parsed}</p></div>""", unsafe_allow_html=True)
            st.divider()

            with st.status("🎯 Comparing with profile...", expanded=True) as status:
                comparison = compare_regulation_with_profile(parsed, profile)
                progress.progress(60)
                status.update(label="✅ Compared", state="complete")

            impact = comparison.get("impact_level", "Unknown")
            impact_class = {"High": "impact-high", "Medium": "impact-medium", "Low": "impact-low"}.get(impact, "impact-low")
            st.markdown(f"""
            <div class="{impact_class}">
                <strong>Impact:</strong> {impact} | <strong>Applicable:</strong> {'✅ Yes' if comparison.get('is_applicable') else '❌ No'}<br>
                <span style="color:#94a3b8">{comparison.get('applicability_reason', '')}</span>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            with st.status("⚡ Generating alert...", expanded=True) as status:
                circ_info = {"title": uploaded.name, "content": parsed}
                alert = generate_compliance_alert(circ_info, comparison, profile)
                progress.progress(100)
                status.update(label="✅ Complete", state="complete")

            st.markdown("### 🚨 Compliance Alert")
            st.markdown(alert)

            st.download_button(
                "📥 Download Report",
                data=alert,
                file_name="compliance_report.md",
                mime="text/markdown",
                use_container_width=True
            )

            st.success("✅ Analysis complete")
            os.unlink(tmp_path)