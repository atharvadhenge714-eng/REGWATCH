import streamlit as st
import json
import os
import tempfile
from company_profiler import profile_company, build_compliance_profile
from fetch_agent import fetch_latest_circulars, fetch_circular_text
from parser_agent import parse_rbi_circular
from mapper_agent import index_company_profile, compare_regulation_with_profile
from action_agent import generate_action_plan, generate_quick_scan
from database import save_report

def generate_pdf_bytes(markdown_text):
    """Convert markdown text to PDF bytes for downloading."""
    try:
        from markdown_pdf import MarkdownPdf, Section
        pdf = MarkdownPdf(toc_level=0)
        pdf.add_section(Section(markdown_text, toc=False))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            
        pdf.save(tmp_path)
            
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
            
        os.unlink(tmp_path)
        return pdf_bytes
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return str(markdown_text).encode("utf-8")

import streamlit.components.v1 as components

# PAGE CONFIG
st.set_page_config(
    page_title="RegWatch — Agentic RBI Compliance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== LOGIN SYSTEM =====================
is_logged_in = st.query_params.get("logged_in") == "true"
current_user = st.query_params.get("user", "User")

if not is_logged_in:
    # Injecting the user's custom CSS directly into Streamlit
    st.markdown("""
    <style>
    .stAppHeader { display: none !important; }
    .stMainBlockContainer { padding: 0 !important; max-width: 100% !important; margin: 0 !important; height: 100vh; overflow: hidden; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    /* BACKGROUNDS */
    .stApp {
        background: url("https://images5.alphacoders.com/128/1280324.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    .planet-mask {
        position: absolute; right: 0; top: 0; width: 40%; height: 100%;
        background: linear-gradient(to right, transparent, rgba(0,0,0,0.95)); z-index: 1; pointer-events: none;
    }

    .stars {
        position: absolute; width: 100%; height: 100%;
        background: url("https://www.transparenttextures.com/patterns/stardust.png");
        animation: moveStars 200s linear infinite; z-index: 2; pointer-events: none;
    }
    @keyframes moveStars{ from{background-position:0 0;} to{background-position:10000px 5000px;} }

    /* CENTER LOGIN BOX OVERRIDE */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 380px; padding: 40px; border-radius: 20px;
        background: rgba(255,255,255,0.08) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 0 40px rgba(0,0,0,0.6);
        z-index: 10;
        text-align: center;
    }
    
    /* WIDGET STYLING */
    h2 { color: white !important; font-size: 28px !important; text-align: center; margin-bottom: 20px !important; }
    div[data-baseweb="input"] {
        background: rgba(255,255,255,0.1) !important;
        border: none !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input { color: white !important; padding: 12px; }
    div[data-baseweb="input"] input::placeholder { color: rgba(255,255,255,0.6); }

    .stButton > button {
        width: 100% !important; padding: 12px !important; margin-top: 15px !important;
        border: none; border-radius: 10px;
        background: linear-gradient(45deg,#4facfe,#00f2fe) !important;
        color: white !important; font-weight: bold !important; transition: 0.3s;
    }
    .stButton > button:hover { transform: scale(1.05); color: white !important; }
    </style>
    
    <div class="planet-mask"></div>
    <div class="stars"></div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2>RegWatch AI</h2>", unsafe_allow_html=True)
        login_user = st.text_input("Username", placeholder="admin", key="user")
        login_pass = st.text_input("Password", placeholder="admin", type="password", key="pass")
        
        if st.button("Login"):
            if login_user == "admin" and login_pass == "admin":
                st.query_params["logged_in"] = "true"
                st.query_params["user"] = login_user
                st.rerun()
            else:
                st.error("Invalid Credentials. Use admin/admin")
        
        st.markdown("<p style='text-align:center; color:#ccc; font-size:14px; margin-top:10px;'>Default credentials: admin / admin</p>", unsafe_allow_html=True)

    st.stop()


# ===================== MAIN APP =====================

# ===================== CSS =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp { background: #080815; font-family: 'Inter', sans-serif; }

    .hero { text-align: center; padding: 25px 0 10px; }
    .hero h1 {
        font-size: 2.6rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; letter-spacing: -0.5px;
    }
    .hero p { color: #475569; font-size: 0.95rem; margin-top: 6px; }

    .gcard {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 14px; padding: 20px;
    }

    .stat {
        background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.04));
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 12px; padding: 18px; text-align: center;
    }
    .stat .val { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
    .stat .lbl { color: #64748b; font-size: 0.8rem; margin-top: 2px; }

    .profile-card {
        background: rgba(99,102,241,0.06);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 14px; padding: 20px; margin: 10px 0;
    }
    .profile-card h3 { color: #c4b5fd; margin: 0 0 12px; font-size: 1.2rem; }
    .profile-item { color: #94a3b8; font-size: 0.9rem; margin: 6px 0; line-height: 1.6; }
    .profile-item strong { color: #e2e8f0; }

    .circ-row {
        background: rgba(15,23,42,0.5);
        border: 1px solid rgba(99,102,241,0.08);
        border-radius: 12px; padding: 14px 18px; margin: 6px 0;
        transition: all 0.2s;
    }
    .circ-row:hover { border-color: rgba(99,102,241,0.25); }
    .circ-title { color: #e2e8f0; font-weight: 600; font-size: 0.9rem; }
    .circ-meta { color: #64748b; font-size: 0.78rem; margin-top: 3px; }

    .badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; }
    .badge-high { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .badge-medium { background: rgba(234,179,8,0.15); color: #facc15; border: 1px solid rgba(234,179,8,0.3); }
    .badge-low { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-na { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
    .badge-cat { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); }

    .impact-high { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.2); border-radius: 14px; padding: 18px; margin: 8px 0; }
    .impact-medium { background: rgba(234,179,8,0.06); border: 1px solid rgba(234,179,8,0.2); border-radius: 14px; padding: 18px; margin: 8px 0; }
    .impact-low { background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.2); border-radius: 14px; padding: 18px; margin: 8px 0; }

    .step {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 16px; background: rgba(99,102,241,0.05);
        border-left: 3px solid #6366f1;
        border-radius: 0 10px 10px 0; margin: 8px 0;
    }
    .step .num {
        background: linear-gradient(135deg, #6366f1, #7c3aed);
        color: white; width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
    }
    .step .txt { color: #94a3b8; font-size: 0.85rem; }
    .step .txt strong { color: #e2e8f0; }

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
        ("2", "AI finds real website"),
        ("3", "AI scrapes & extracts services"),
        ("4", "System builds compliance profile"),
        ("5", "Fetch latest RBI circulars"),
        ("6", "AI scans & filters relevant ones"),
        ("7", "Compare regulation vs profile"),
    ]
    for num, txt in steps:
        st.markdown(f'<div class="step"><div class="num">{num}</div><div class="txt">{txt}</div></div>', unsafe_allow_html=True)

    st.divider()

    if "company_profile" in st.session_state:
        p = st.session_state.company_profile
        st.success(f"🏢 {p['company_name']}", icon="✅")
        st.caption(f"Type: {p.get('company_type', 'N/A')}")
        st.caption(f"URL: {p.get('website_url', 'N/A')}")
        st.caption(f"Services: {len(p.get('services', []))}")
    else:
        st.info("No company profiled yet")

    st.divider()
    st.caption("Team Apex Devs — The Paradox 2025")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.query_params.clear()
        st.rerun()

# ===================== MAIN =====================

# STEP 1: Company Setup (if no profile yet)
if "company_profile" not in st.session_state:
    st.markdown("### Step 1 — Enter Your Company Name")
    st.caption("The AI will find the real website, scrape it, and build a compliance profile automatically.")

    # Use a form so Enter key submits
    with st.form("company_form", clear_on_submit=False):
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Paytm, PhonePe, CRED, Razorpay, HDFC Bank, Bajaj Finance...",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🚀 Build Compliance Profile", type="primary", use_container_width=True)

    # OR upload policy
    st.markdown("")
    with st.expander("📄 Or upload a company policy document"):
        policy_pdf = st.file_uploader("Upload policy (PDF or TXT)", type=["pdf", "txt"], key="policy_up")
        policy_name = st.text_input("Company name", key="policy_name_in")
        if policy_pdf and policy_name and st.button("Build Profile from Document"):
            with st.spinner("Processing..."):
                if policy_pdf.name.endswith(".txt"):
                    doc_text = policy_pdf.read().decode("utf-8")
                else:
                    import pypdf
                    reader = pypdf.PdfReader(policy_pdf)
                    doc_text = " ".join(page.extract_text() for page in reader.pages)
                profile = build_compliance_profile(policy_name, doc_text)
                profile["website_url"] = "Uploaded document"
                index_company_profile(profile)
                st.session_state.company_profile = profile
                st.rerun()

    # Trigger on Enter or button
    if submitted and company_name:
        progress = st.progress(0, text="🔍 Finding company website...")

        with st.status("🤖 Autonomous Company Profiling...", expanded=True) as status:
            st.write(f"🔍 Finding real website for {company_name}...")
            progress.progress(15, text="Finding website via AI...")

            st.write("🌐 Scraping company website...")
            progress.progress(40, text="Scraping real website pages...")

            st.write("🧠 Analyzing with AI (LLaMA 3.3 70B)...")
            progress.progress(65, text="Building compliance profile...")

            profile = profile_company(company_name)

            st.write(f"📊 Found: {profile.get('website_url', 'N/A')}")
            st.write(f"📊 Detected {len(profile.get('services', []))} services")
            st.write("📊 Indexing in ChromaDB...")
            index_company_profile(profile)
            progress.progress(100, text="✅ Profile ready!")

            status.update(label=f"✅ Profile Built — {company_name}", state="complete")

        st.session_state.company_profile = profile
        st.rerun()


# Main app after profile is built
else:
    profile = st.session_state.company_profile

    tab1, tab2, tab3 = st.tabs(["🏢 Company Profile", "🌐 RBI Scan & Alerts", "📄 Upload Circular"])


    # ============= TAB 1: COMPANY PROFILE =============
    with tab1:
        col_p1, col_p2 = st.columns([2, 1])

        with col_p1:
            st.markdown(f"""
            <div class="profile-card">
                <h3>🏢 {profile['company_name']}</h3>
                <div class="profile-item"><strong>Type:</strong> {profile.get('company_type', 'N/A')}</div>
                <div class="profile-item"><strong>Website:</strong> <a href="{profile.get('website_url', '#')}" style="color:#818cf8;">{profile.get('website_url', 'N/A')}</a></div>
                <div class="profile-item"><strong>RBI Registration:</strong> {profile.get('rbi_registration', 'N/A')}</div>
                <div class="profile-item"><strong>Data Handling:</strong> {profile.get('data_handling', 'N/A')}</div>
                <div class="profile-item"><strong>Summary:</strong> {profile.get('compliance_summary', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            for val, lbl in [
                (str(len(profile.get("services", []))), "Services Detected"),
                (str(len(profile.get("regulatory_domains", []))), "Regulatory Domains"),
                (str(len(profile.get("risk_areas", []))), "Risk Areas")
            ]:
                st.markdown(f'<div class="stat"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)
                st.markdown("")

        st.markdown("")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown("**🔧 Services**")
            for s in profile.get("services", []):
                st.markdown(f"- {s}")
        with col_s2:
            st.markdown("**📋 Regulatory Domains**")
            for d in profile.get("regulatory_domains", []):
                st.markdown(f"- {d}")
        with col_s3:
            st.markdown("**⚠️ Risk Areas**")
            for r in profile.get("risk_areas", []):
                st.markdown(f"- {r}")

        with st.expander("📖 Applicable RBI Guidelines"):
            for g in profile.get("applicable_rbi_guidelines", []):
                st.markdown(f"- {g}")

        st.divider()
        if st.button("🔄 Change Company", key="reprofile"):
            for key in ["company_profile", "circulars", "scan_results", "analyzing_circular"]:
                st.session_state.pop(key, None)
            st.rerun()


    # ============= TAB 2: RBI SCAN & ALERTS =============
    with tab2:
        st.markdown(f"#### 🌐 RBI Circulars — Relevance Scan for {profile['company_name']}")

        # Fetch circulars
        if "circulars" not in st.session_state:
            with st.spinner("Fetching latest RBI circulars..."):
                st.session_state.circulars = fetch_latest_circulars()

        circulars = st.session_state.circulars

        # Controls
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            scan_btn = st.button("⚡ Auto-Scan: Find Relevant Circulars", type="primary", use_container_width=True)
        with col_c2:
            show_all = st.checkbox("Show all circulars (including non-relevant)", value=not bool(st.session_state.get("scan_results")))

        # Run auto scan
        if scan_btn:
            with st.status(f"🤖 AI scanning {len(circulars)} circulars for {profile['company_name']}...", expanded=True) as status:
                st.write(f"Comparing against: {', '.join(profile.get('services', [])[:5])}...")
                scan_results = generate_quick_scan(circulars, profile)
                st.session_state.scan_results = scan_results
                relevant_count = sum(1 for r in scan_results if r.get("is_relevant"))
                st.write(f"Found {relevant_count} relevant circulars!")
                status.update(label=f"✅ {relevant_count}/{len(circulars)} circulars relevant", state="complete")

        st.divider()

        scan_results = st.session_state.get("scan_results", None)
        has_scan = scan_results is not None

        # Display circulars
        for i, c in enumerate(circulars):
            scan = scan_results[i] if has_scan and i < len(scan_results) else None

            # Filter: after scan, only show relevant ones (unless show_all is checked)
            if has_scan and not show_all:
                if scan and not scan.get("is_relevant", False):
                    continue

            col_a, col_b = st.columns([5, 1])

            with col_a:
                impact = scan.get("impact_level", "") if scan else ""
                badge_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(impact, "badge-na")

                rel_html = ""
                if scan:
                    if scan.get("is_relevant"):
                        rel_html = f' <span class="badge {badge_class}">{impact} Impact</span>'
                        urgency = scan.get("urgency", "")
                        urg_icon = {"Immediate": "🔴", "This Quarter": "🟡", "Informational": "🟢"}.get(urgency, "")
                        rel_html += f' <span class="badge badge-na">{urg_icon} {urgency}</span>'
                    else:
                        rel_html = ' <span class="badge badge-na">Not Applicable</span>'

                st.markdown(f"""
                <div class="circ-row">
                    <div class="circ-title">{c['title']}{rel_html}</div>
                    <div class="circ-meta">📅 {c.get('date', 'N/A')} &nbsp; <span class="badge badge-cat">{c.get('category', 'RBI')}</span></div>
                </div>
                """, unsafe_allow_html=True)

                if scan and scan.get("is_relevant"):
                    st.caption(f"💡 {scan.get('relevance_reason', '')}")

            with col_b:
                st.markdown("")
                if st.button("Analyze →", key=f"deep_{i}", use_container_width=True):
                    st.session_state.analyzing_circular = c

        # Deep analysis
        if "analyzing_circular" in st.session_state:
            c = st.session_state.analyzing_circular
            st.divider()
            st.markdown(f"### 🔍 Analyzing: {c['title']}")

            progress = st.progress(0, text="Fetching circular...")

            with st.status("📄 Fetching content...", expanded=True) as status:
                content = fetch_circular_text(c["url"])
                progress.progress(20)
                status.update(label="✅ Content Fetched", state="complete")

            st.markdown(f'<div class="gcard"><p style="color:#cbd5e1;font-size:0.85rem;">{content[:800]}...</p></div>', unsafe_allow_html=True)
            st.divider()

            with st.status("🎯 Comparing with company profile...", expanded=True) as status:
                comparison = compare_regulation_with_profile(content, profile)
                progress.progress(50)
                status.update(label="✅ Compared", state="complete")

            impact = comparison.get("impact_level", "Unknown")
            impact_class = {"High": "impact-high", "Medium": "impact-medium"}.get(impact, "impact-low")

            st.markdown(f"""
            <div class="{impact_class}">
                <strong>Impact:</strong> {impact} &nbsp; <strong>Applicable:</strong> {'✅ Yes' if comparison.get('is_applicable') else '❌ No'}<br>
                <span style="color:#94a3b8">{comparison.get('applicability_reason', '')}</span>
            </div>
            """, unsafe_allow_html=True)

            if comparison.get("compliance_gaps"):
                for gap in comparison["compliance_gaps"]:
                    st.warning(f"**{gap.get('gap', '')}** — Risk: {gap.get('risk', 'Medium')}")

            st.divider()

            with st.status("⚡ Generating action plan...", expanded=True) as status:
                affected_text = json.dumps(comparison.get("compliance_gaps", []), indent=2)
                action_plan = generate_action_plan(content[:2000], affected_text)
                progress.progress(100)
                status.update(label="✅ Action Plan Ready", state="complete")

            st.markdown("### 📌 Compliance Action Plan")
            st.markdown(action_plan)

            report_md = f"# Compliance Report — {profile['company_name']}\n\n## Circular: {c['title']}\n\n{action_plan}"
            pdf_data = generate_pdf_bytes(report_md)

            st.download_button(
                "📥 Download PDF Report",
                data=pdf_data,
                file_name=f"compliance_{profile['company_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            try:
                save_report(c["title"], json.dumps(comparison), action_plan)
            except:
                pass

            st.success(f"✅ Analysis complete for {profile['company_name']}")

            if st.button("← Back to Circulars"):
                st.session_state.pop("analyzing_circular", None)
                st.rerun()


    # ============= TAB 3: UPLOAD CIRCULAR =============
    with tab3:
        st.markdown(f"#### 📄 Upload a Custom RBI Circular")
        st.caption(f"Analyze any circular PDF against {profile['company_name']}'s profile")

        uploaded = st.file_uploader("Upload circular PDF", type="pdf", key="custom_pdf")

        if uploaded and st.button("🚀 Analyze", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            progress = st.progress(0)

            with st.status("🔍 Parsing...") as s:
                parsed = parse_rbi_circular(tmp_path)
                progress.progress(30)
                s.update(label="✅ Parsed", state="complete")

            st.markdown(f'<div class="gcard"><p style="color:#cbd5e1;font-size:0.85rem;">{parsed}</p></div>', unsafe_allow_html=True)
            st.divider()

            with st.status("🎯 Comparing...") as s:
                comparison = compare_regulation_with_profile(parsed, profile)
                progress.progress(60)
                s.update(label="✅ Compared", state="complete")

            impact = comparison.get("impact_level", "Unknown")
            st.markdown(f"**Impact:** {impact} | **Applicable:** {'✅' if comparison.get('is_applicable') else '❌'}")
            st.caption(comparison.get("applicability_reason", ""))
            st.divider()

            with st.status("⚡ Generating plan...") as s:
                plan = generate_action_plan(parsed, json.dumps(comparison.get("compliance_gaps", [])))
                progress.progress(100)
                s.update(label="✅ Done", state="complete")

            st.markdown("### 📌 Action Plan")
            st.markdown(plan)

            report_md = f"# Compliance Report — {profile['company_name']}\n\n## Uploaded Circular\n\n{plan}"
            pdf_data = generate_pdf_bytes(report_md)

            st.download_button(
                "📥 Download PDF Report", 
                data=pdf_data, 
                file_name=f"compliance_{profile['company_name'].replace(' ', '_')}.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
            st.success("✅ Complete")
            os.unlink(tmp_path)