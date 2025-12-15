import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import altair as alt 

# --- CONFIG & UTILS SIMULATION ---
# NOTE: Replace these placeholder functions with your actual imports (config, utils)
DATA_DIR = "data"
REGS_FILE = os.path.join(DATA_DIR, "regulations.json")
CONTRACTS_DIR = os.path.join(DATA_DIR, "contracts")
CONTRACT_INDEX = os.path.join(DATA_DIR, "contract_index.json")

def ensure_dirs():
    """Simulates checking/creating directories."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    if not os.path.exists(REGS_FILE):
        with open(REGS_FILE, 'w') as f:
            json.dump({"reg_1": {"name": "GDPR"}, "reg_2": {"name": "CCPA"}}, f)
    if not os.path.exists(CONTRACT_INDEX):
        sample_index = {
            "c001": {"original_name": "Sales Agreement Q4", "version": 2, "uploaded_at": "2025-12-08T10:30:00", "status": "Compliant"},
            "c002": {"original_name": "Vendor Contract 2025", "version": 1, "uploaded_at": "2025-12-09T14:45:00", "status": "Pending Review"},
            "c003": {"original_name": "NDA Acme Corp", "version": 3, "uploaded_at": "2025-12-07T09:00:00", "status": "Minor Issues"},
            "c004": {"original_name": "Lease Agreement", "version": 1, "uploaded_at": "2025-12-10T08:15:00", "status": "Pending Review"},
            "c005": {"original_name": "Service Renewal", "version": 2, "uploaded_at": "2025-12-06T11:00:00", "status": "Compliant"},
        }
        with open(CONTRACT_INDEX, 'w') as f:
            json.dump(sample_index, f)

def read_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Initialize directories
ensure_dirs()
# --- END SIMULATION ---


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Contract Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= AUTHENTICATION ENFORCEMENT =================
if not st.session_state.get("logged_in"):
    st.empty() 
    st.switch_page("pages/Login.py")


# ================= CSS STYLING (Standardized) =================
st.markdown("""
<style>
    /* 1. APP BACKGROUND */
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }

    /* 2. HEADER FIX */
    header[data-testid="stHeader"] { background-color: #FFFFFF !important; border-bottom: 1px solid #F0F2F6; }
    header[data-testid="stHeader"] * { color: #333333 !important; }

    /* 3. SIDEBAR STYLING */
    [data-testid="stSidebar"] { background-color: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebar"] span { color: #4B5563 !important; }
    [data-testid="stSidebar"] h1, h2, h3 { color: #111827 !important; }

    /* 4. HIDE DEFAULT STREAMLIT NAV (The Fix!) */
    [data-testid="stSidebarNav"] { display: none; }

    /* 5. METRIC CARDS */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, border-color 0.2s;
        cursor: pointer;
    }
    .metric-card:hover { transform: translateY(-2px); }

    .metric-value { font-size: 36px; font-weight: 800; color: #0056D2; margin-bottom: 5px; }
    .metric-label { font-size: 13px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; }

    /* Conditional Styles for Pending Review */
    .pending-alert { border-color: #EF4444 !important; } 
    .pending-alert:hover { border-color: #B91C1C !important; }
    .pending-value { color: #EF4444 !important; } 

    /* 6. RECENT ACTIVITY CARDS */
    .activity-card {
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #F3F4F6;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tag {
        background: #EFF6FF;
        color: #1D4ED8;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }

    /* 7. TITLES */
    .main-title { font-size: 32px; font-weight: 800; color: #111827; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)


# ================= UNIFIED SIDEBAR =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
    st.markdown("### AI Powered Regulatory Compliance Checker for Contracts")

    # User Status
    st.success(f"👤 **{st.session_state.get('user_name', 'Analyst')}**")

    # Standard Navigation
    st.page_link("Home.py", label="Overview", icon="🏠")
    st.page_link("pages/Contract_Analysis.py", label="Contract Analysis", icon="📄")
    st.page_link("pages/Risk_Assessment.py", label="Risk Assessment", icon="📊")
    st.page_link("pages/Regulation_Monitor.py", label="Regulation Monitor", icon="⚖️")
    st.page_link("pages/AI_Chatbot.py", label="AI Chatbot", icon="🤖")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ================= DASHBOARD CONTENT =================

# 1. Header
st.markdown("<div class='main-title'>Dashboard Overview</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#6B7280; margin-bottom:30px;'>Welcome to your contract intelligence command center.</p>", unsafe_allow_html=True)

# Load data
regs = read_json(REGS_FILE)
index = read_json(CONTRACT_INDEX)

# Calculate key metrics
df_index = pd.DataFrame.from_dict(index, orient='index')
total_contracts = len(index)
total_regs = len(regs)
pending_reviews = sum(1 for c in index.values() if c.get("status") == "Pending Review")

# 2. Key Metrics
col1, col2, col3 = st.columns(3)

# Contract Metric
with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{total_contracts}</div>
        <div class='metric-label'>Active Contracts</div>
    </div>
    """, unsafe_allow_html=True)

# Regulation Metric
with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{total_regs}</div>
        <div class='metric-label'>Regulations Tracked</div>
    </div>
    """, unsafe_allow_html=True)

# Pending Review Metric (Conditional Styling)
pending_class = "pending-alert" if pending_reviews > 0 else ""
pending_value_class = "pending-value" if pending_reviews > 0 else ""

with col3:
    st.markdown(f"""
    <div class='metric-card {pending_class}'>
        <div class='metric-value {pending_value_class}'>{pending_reviews}</div>
        <div class='metric-label'>Pending Review</div>
    </div>
    """, unsafe_allow_html=True)

# 3. Visualization and Activity Split
st.markdown("---")
st.markdown("### 📈 Compliance Trends")

chart_col, activity_col = st.columns([2, 1])

with chart_col:
    # Altair Chart (Corrected from previous steps)
    if not df_index.empty:
        status_counts = df_index['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']

        # Define colors for statuses
        color_map = {
            "Compliant": "#10B981",       # Green
            "Minor Issues": "#FBBF24",    # Yellow
            "Major Gaps": "#EF4444",      # Red
            "Pending Review": "#3B82F6"   # Blue
        }

        # Add color column
        status_counts['Color'] = status_counts['Status'].map(color_map).fillna("#CCCCCC")

        # Create Altair Chart
        chart = alt.Chart(status_counts).mark_bar().encode(
            x=alt.X('Status', sort=None),
            y='Count',
            color=alt.Color('Status', scale=alt.Scale(
                domain=status_counts['Status'].tolist(),
                range=status_counts['Color'].tolist()
            ), title=None),
            tooltip=['Status', 'Count']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
        st.caption("Contract status breakdown (by last automated review)")
    else:
        st.info("Upload a contract to see the compliance trend data here.")


with activity_col:
    st.markdown("### 🕒 Recent Uploads")
    if not index:
        st.info("No contracts found. Upload one to see recent activity.")
    else:
        sorted_contracts = sorted(
            index.items(),
            key=lambda x: datetime.fromisoformat(x[1].get("uploaded_at", "2000-01-01T00:00:00")),
            reverse=True
        )

        for i, (cid, meta) in enumerate(sorted_contracts[:5]):
            st.markdown(f"""
            <div class='activity-card'>
                <div>
                    <div style='font-weight:700; color:#374151;'>{meta.get('original_name', 'Untitled')}</div>
                    <div style='font-size:12px; color:#9CA3AF;'>ID: {cid} • {meta.get('uploaded_at', '').split('T')[0]}</div>
                </div>
                <span class='tag'>{meta.get('status', 'Unknown')}</span>
            </div>
            """, unsafe_allow_html=True)