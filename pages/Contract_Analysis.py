# pages/Contract_Analysis.py
import streamlit as st
import os
import re
from datetime import datetime

# Import custom modules
from config import CONTRACTS_DIR, REGS_FILE, CONTRACT_INDEX
from utils import read_json, write_json
from processor import save_uploaded_contract, save_pdf, read_contract_text
from analyzer import split_into_sections, match_regulation_to_contract

try:
    from emailer import send_email
except ImportError:
    def send_email(to, s, b): return True # Fallback

# ================= AUTHENTICATION ENFORCEMENT =================
# 🛑 CRITICAL: This checks the session state. If not logged in,
# it immediately redirects the user to the Login page.
if not st.session_state.get("logged_in"):
    st.empty() 
    st.switch_page("pages/Login.py") 
# ================= END ENFORCEMENT =================


# ================= PAGE SETUP =================
st.set_page_config(page_title="Contract Analysis", layout="wide")

# ================= UNIFIED UI CSS =================
st.markdown("""
<style>
    /* 1. APP BACKGROUND */
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }

    /* 2. HEADER FIX */
    header[data-testid="stHeader"] { background-color: #FFFFFF !important; border-bottom: 1px solid #F3F4F6; }
    header[data-testid="stHeader"] * { color: #555555 !important; }

    /* 3. SIDEBAR */
    [data-testid="stSidebar"] { background-color: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
    
    /* 4. HIDE DEFAULT STREAMLIT NAV (The Fix!) */
    [data-testid="stSidebarNav"] { display: none; }
    
    /* 5. CARDS */
    .card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); 
        margin-bottom: 20px;
        transition: all 0.2s ease;
    }
    .card:hover { border-color: #0056D2; transform: translateY(-2px); }

    /* 6. CONTROL PANEL */
    .control-panel {
        background: linear-gradient(to right, #F9FAFB, #FFFFFF);
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        margin-bottom: 35px;
    }

    /* 7. TYPOGRAPHY */
    .main-title { font-family: 'Inter', sans-serif; font-size: 36px; font-weight: 800; color: #111827; margin-top: -20px; }
    .sub-title { color: #6B7280; font-size: 16px; margin-bottom: 25px; }
    .badge-blue { background-color: #EFF6FF; color: #1D4ED8; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    
    /* 8. TABS */
    .stTabs [aria-selected="true"] { color: #0056D2 !important; background-color: #EFF6FF !important; }
</style>
""", unsafe_allow_html=True)

# ================= UNIFIED SIDEBAR NAVIGATION =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
    st.markdown("### AI Powered Regulatory Compliance Checker for Contracts")
    
    # User Info Display
    st.success(f"👤 **{st.session_state.get('user_name', 'Analyst')}**")
    
    # Standard Navigation Links (Using st.page_link)
    st.page_link("Home.py", label="Overview", icon="🏠")
    st.page_link("pages/Contract_Analysis.py", label="Contract Analysis", icon="📄")
    st.page_link("pages/Risk_Assessment.py", label="Risk Assessment", icon="📊")
    st.page_link("pages/Regulation_Monitor.py", label="Regulation Monitor", icon="⚖️")
    st.page_link("pages/AI_Chatbot.py", label="AI Chatbot", icon="🤖")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ================= HELPER FOR CLEAN DISPLAY =================
def format_content_as_points(text):
    """
    Detects numbered clauses (1. Title: ...) inside a blob of text 
    and formats them as distinct HTML blocks for readability.
    """
    # 1. Replace newlines with HTML breaks first
    text = text.replace("\n", "<br>")
    
    # 2. Regex to find "1. WORD:" or "2. Word:" patterns
    # We replace them with a double line break and bold text
    pattern = r'(\d+\.\s+[A-Z\s\-]+:?)' 
    formatted_text = re.sub(pattern, r'<br><br><strong style="color:#0056D2;">\1</strong>', text)
    
    # Remove any leading <br> if it was added at the very start
    if formatted_text.startswith("<br><br>"):
        formatted_text = formatted_text[8:]
        
    return formatted_text

# ================= MAIN LOGIC =================

st.markdown("<div class='main-title'>Contract Analysis</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Deep dive analysis: Extract clauses and audit specific contracts.</div>", unsafe_allow_html=True)

# --- STEP 1: CONTROL PANEL ---
st.markdown("<div class='control-panel'>", unsafe_allow_html=True)
col_head, col_action = st.columns([2, 1])
with col_head:
    st.markdown("#### 📂 Document Source")
    st.markdown("Select a contract or upload a new one for analysis.")

with col_action:
     mode = st.radio("Mode:", ["Analyze New", "Audit Existing"], horizontal=True, label_visibility="collapsed")

st.markdown("---")

cid, current_path, current_text, current_meta = None, None, None, None

if mode == "Analyze New":
    uploaded = st.file_uploader("Upload PDF/TXT", type=["pdf", "txt"])
    if uploaded:
        cid, current_path, current_text = save_uploaded_contract(uploaded)
        current_meta = {"original_name": uploaded.name, "version": 1}
        st.success(f"✔ Ready: {uploaded.name}")

else: # Audit Existing
    index = read_json(CONTRACT_INDEX)
    if index:
        options = list(index.keys())
        def format_func(x):
            return f"{index[x]['original_name']} (v{index[x]['version']})"
            
        selected_id = st.selectbox("Select Contract:", options, format_func=format_func)
        
        if selected_id:
            cid = selected_id
            current_meta = index[cid]
            current_path = os.path.join(CONTRACTS_DIR, current_meta["file"])
            current_text = read_contract_text(current_path)
    else:
        st.info("No contracts found.")
st.markdown("</div>", unsafe_allow_html=True)

# --- STEP 2: CONTENT AREA ---
if current_text:
    
    tab_extract, tab_compliance = st.tabs(["🔍 Clause Extraction", "⚖️ Compliance Audit"])

    # === TAB 1: EXTRACTION ===
    with tab_extract:
        st.markdown("<br>", unsafe_allow_html=True)
        sections = split_into_sections(current_text)
        
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            if not sections:
                st.warning("No clear sections detected. Showing raw text.")
                st.text(current_text[:2000] + "...")
            
            for head, content in sections:
                if len(content.strip()) > 5:
                    # Apply the formatting helper here
                    formatted_content = format_content_as_points(content)
                    
                    st.markdown(f"""
                    <div class='card'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:10px;'>
                            <span style='font-weight:700; color:#111827; font-size:16px;'>{head}</span>
                            <span class='badge-blue'>Clause</span>
                        </div>
                        <div style='color:#4B5563; font-size:14px; line-height:1.7;'>
                            {formatted_content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col_c2:
            st.markdown(f"""
            <div class='card' style='padding:20px;'>
                <h4 style='margin-top:0;'>Document Metadata</h4>
                <p><b>File:</b> {current_meta.get('original_name')}</p>
                <p><b>Version:</b> v{current_meta.get('version')}</p>
                <p><b>Sections:</b> {len(sections)}</p>
                <hr>
                <div style='color:#0056D2; font-weight:bold;'>Status: Analyzed</div>
            </div>
            """, unsafe_allow_html=True)

    # === TAB 2: COMPLIANCE AUDIT ===
    with tab_compliance:
        st.markdown("<br>", unsafe_allow_html=True)
        
        regs = read_json(REGS_FILE)
        violations = []
        
        # --- FIX: ROBUST LOOP FOR LIST OR DICT ---
        # The error happened because 'regs' is a list, but we used .items().
        # This fixes it by normalizing the data into a list iterator.
        
        if isinstance(regs, dict):
            iterator = regs.values()
        elif isinstance(regs, list):
            iterator = regs
        else:
            iterator = []
            
        for r_data in iterator:
            score, matches = match_regulation_to_contract(r_data, current_text)
            if score > 0:
                violations.append((r_data, matches))
        # ----------------------------------------

        if violations:
            st.warning(f"⚠️ Found {len(violations)} potential compliance issues.")
            for v_reg, v_matches in violations:
                 st.markdown(f"""
                <div class='card' style='border-left: 5px solid #EF4444;'>
                    <h4 style='color:#991B1B; margin-top:0;'>Non-Compliant: {v_reg.get('title', 'Unknown Regulation')}</h4>
                    <p style='color:#374151; font-size:14px;'>
                        <b>Jurisdiction:</b> {v_reg.get('jurisdiction', 'Global')}<br>
                        <b>Detected Keywords:</b> {', '.join(v_matches)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Button to fix locally if desired
            if st.button("🛠 Fix Issues Locally (Create v+1)", type="primary"):
                updates = "\n\n".join([f"AMENDMENT: Compliant with {v[0].get('title')}" for v in violations])
                new_text = current_text + "\n\n--- REGULATORY UPDATES ---\n" + updates
                
                new_ver = current_meta["version"] + 1
                new_file = f"{cid}-v{new_ver}.pdf"
                new_path = os.path.join(CONTRACTS_DIR, new_file)
                
                save_pdf(new_path, new_text) 
                
                # Update Index
                index = read_json(CONTRACT_INDEX)
                # Ensure we have the record to update
                if cid in index:
                    index[cid]["version"] = new_ver
                    index[cid]["file"] = new_file
                    index[cid]["last_updated"] = datetime.now().isoformat()
                    write_json(CONTRACT_INDEX, index)
                    
                    st.success(f"✅ Contract updated to Version {new_ver}!")
                    st.rerun()
                else:
                    st.error("Could not find contract in index to update.")

        else:
            st.markdown("""
            <div class='card' style='border-left: 5px solid #10B981; text-align:center;'>
                <h3 style='color:#065F46;'>✅ Fully Compliant</h3>
                <p style='color:#6B7280;'>No violations found against active regulations.</p>
            </div>
            """, unsafe_allow_html=True)