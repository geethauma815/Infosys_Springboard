# pages/Risk_Assessment.py
import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

# Backend Utilities
from config import CONTRACT_INDEX, CONTRACTS_DIR
from utils import read_json, write_json
from processor import save_uploaded_contract, read_contract_text

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Risk Assessment", layout="wide")

# ================= AUTHENTICATION ENFORCEMENT =================
# 🛑 CRITICAL: Check session state immediately.
if not st.session_state.get("logged_in"):
    st.empty()
    st.switch_page("pages/Login.py")
# ================= END ENFORCEMENT =================


# ================= CSS STYLING =================
st.markdown("""
<style>
    /* Styling for the page */
    .stApp { background-color: #FFFFFF !important; color: #333333; }
    [data-testid="stSidebar"] { background-color: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebarNav"] { display: none; }
    
    /* Result Cards */
    .risk-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        margin-bottom: 15px;
        background-color: #F9FAFB;
    }
    .high-risk { border-left: 5px solid #EF4444; background-color: #FEF2F2; }
    .med-risk { border-left: 5px solid #F59E0B; background-color: #FFFBEB; }
    .low-risk { border-left: 5px solid #10B981; background-color: #ECFDF5; }
    
    /* Metrics */
    .metric-box { text-align: center; padding: 15px; border: 1px solid #eee; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR NAVIGATION =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
    st.markdown("### AI Powered Regulatory Compliance Checker for Contracts")
    
    # User Status
    st.success(f"👤 **{st.session_state.get('user_name', 'Analyst')}**")

    # Navigation Links
    st.page_link("Home.py", label="Overview", icon="🏠")
    st.page_link("pages/Contract_Analysis.py", label="Contract Analysis", icon="📄")
    st.page_link("pages/Risk_Assessment.py", label="Risk Assessment", icon="📊")
    st.page_link("pages/Regulation_Monitor.py", label="Regulation Monitor", icon="⚖️")
    st.page_link("pages/AI_Chatbot.py", label="AI Chatbot", icon="🤖")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ================= CORE RISK LOGIC =================
def analyze_single_contract(text):
    """
    Analyzes a single text string for specific risk clauses.
    Returns: (score, risk_level, found_issues)
    """
    text = text.lower()
    issues = []
    score_penalty = 0
    
    # --- RISK RULES DEFINITION ---
    rules = {
        "Unlimited Liability": ("liability" in text and "unlimited" in text, 30),
        "Missing Termination Notice": ("terminate" in text and "notice" not in text, 20),
        "Mandatory Arbitration": ("arbitration" in text, 15),
        "Indemnification": ("indemnif" in text, 15),
        "Long-Term / Perpetual": ("perpetual" in text or "indefinite" in text, 10),
        "Force Majeure Missing": ("force majeure" not in text, 10),
    }
    
    for issue_name, (is_present, penalty) in rules.items():
        if is_present:
            issues.append(issue_name)
            score_penalty += penalty
            
    final_score = max(0, 100 - score_penalty)
    
    if final_score < 60: risk_level = "High"
    elif final_score < 85: risk_level = "Medium"
    else: risk_level = "Low"
    
    return final_score, risk_level, issues

@st.cache_data(ttl=60) # Cache for speed, clear every minute to show updates
def get_portfolio_data():
    """Reads all contracts from storage and builds the dataset for graphs."""
    index = read_json(CONTRACT_INDEX)
    data_list = []
    
    for cid, meta in index.items():
        path = os.path.join(CONTRACTS_DIR, meta["file"])
        if os.path.exists(path):
            text = read_contract_text(path)
            s, l, i = analyze_single_contract(text)
            data_list.append({
                "Contract": meta.get("original_name", "Unknown"),
                "Score": s,
                "Risk": l,
                "Issues": i,
                "Issue_Count": len(i)
            })
    
    if not data_list:
        return pd.DataFrame(columns=["Contract", "Score", "Risk", "Issues", "Issue_Count"])
        
    return pd.DataFrame(data_list)

# ================= UI: SECTION 1 - UPLOAD & INSTANT CHECK =================
st.title("🛡️ Risk Assessment Engine")
st.markdown("Upload a contract for instant scoring, or scroll down for portfolio analytics.")

with st.container():
    st.markdown("#### 1. Analyze New Contract")
    uploaded_file = st.file_uploader("Upload PDF/TXT to Assess Risk", type=["pdf", "txt"])

    if uploaded_file:
        # 1. Save File
        cid, path, text = save_uploaded_contract(uploaded_file)
        
        # 2. Run Analysis
        score, risk, issues = analyze_single_contract(text)
        
        # 3. Display Results
        color = "#EF4444" if risk == "High" else "#F59E0B" if risk == "Medium" else "#10B981"
        
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown(f"""
            <div style="background-color:{color}; padding:20px; border-radius:10px; color:white; text-align:center;">
                <div style="font-size:48px; font-weight:bold;">{score}</div>
                <div style="font-size:18px;">/ 100</div>
                <div style="margin-top:10px; font-weight:bold;">{risk.upper()} RISK</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.subheader(f"Risk Report: {uploaded_file.name}")
            if issues:
                st.write("⚠️ **Potential Risks Detected:**")
                for issue in issues:
                    st.markdown(f"- 🔴 **{issue}**")
                st.info("💡 Recommendation: Review these clauses in the 'Contract Analysis' page.")
            else:
                st.success("✅ Clean Contract: No standard high-risk clauses detected.")
                
        # Refresh visuals immediately
        st.cache_data.clear() 

# ================= UI: SECTION 2 - VISUAL ANALYTICS =================
st.markdown("---")
st.markdown("#### 2. Portfolio Analytics")

df = get_portfolio_data()

if df.empty:
    st.info("No contracts in database yet.")
else:
    # --- ROW 1: RISK MATRIX & DISTRIBUTION ---
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.caption("Risk Matrix: Safety Score vs. Issue Count")
        scatter = alt.Chart(df).mark_circle(size=100).encode(
            x=alt.X('Issue_Count:Q', title='Issues Detected'),
            y=alt.Y('Score:Q', title='Safety Score (0-100)', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Risk', scale=alt.Scale(domain=['High', 'Medium', 'Low'], range=['#EF4444', '#F59E0B', '#10B981'])),
            tooltip=['Contract', 'Score', 'Risk', 'Issue_Count']
        ).interactive()
        st.altair_chart(scatter, use_container_width=True)

    with col_b:
        st.caption("Risk Distribution")
        donut = alt.Chart(df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("count()"),
            color=alt.Color("Risk", scale=alt.Scale(domain=['High', 'Medium', 'Low'], range=['#EF4444', '#F59E0B', '#10B981'])),
            tooltip=["Risk", "count()"]
        )
        st.altair_chart(donut, use_container_width=True)

    # --- ROW 2: HOTSPOTS (BAR CHART) ---
    st.caption("🔥 Vulnerability Hotspots (Most Common Risks)")
    
    # Flatten the list of lists for counting
    all_issues = [x for sublist in df['Issues'] for x in sublist]
    if all_issues:
        issue_counts = pd.DataFrame(all_issues, columns=["Issue"]).value_counts().reset_index(name="Count")
        
        bar_chart = alt.Chart(issue_counts).mark_bar().encode(
            x=alt.X('Count:Q', title='Contracts Affected'),
            y=alt.Y('Issue:N', sort='-x', title=None),
            color=alt.Color('Count:Q', legend=None, scale=alt.Scale(scheme='orangered')),
            tooltip=['Issue', 'Count']
        ).properties(height=300)
        
        st.altair_chart(bar_chart, use_container_width=True)
    else:
        st.success("No widespread clause violations found in the portfolio.")