# pages/Regulation_Monitor.py
import streamlit as st
import os
import json
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Import backend logic
from config import REGS_FILE, CONTRACT_INDEX, CONTRACTS_DIR
# IMPORTANT: Imported inject_clause_smartly to fix the insertion position
from analyzer import mock_fetch_regulations, match_regulation_to_contract, inject_clause_smartly
from processor import read_contract_text, save_pdf
from utils import read_json, write_json

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Regulation Monitor", layout="wide")

# ================= AUTHENTICATION ENFORCEMENT =================
# 🛑 CRITICAL: Check session state immediately.
if not st.session_state.get("logged_in"):
    st.empty()
    st.switch_page("pages/Login.py")
# ================= END ENFORCEMENT =================


# ================= CSS: HIDE DEFAULT NAV & STYLE =================
st.markdown("""
<style>
    /* 1. Hide Default Navigation */
    [data-testid="stSidebarNav"] { display: none; }

    /* 2. Standard White Styling */
    .stApp { background-color: #FFFFFF !important; color: #333333; }
    [data-testid="stSidebar"] { background-color: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
    
    /* 3. Regulation Card Styling */
    .reg-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .reg-title { font-size: 18px; font-weight: 700; color: #111827; }
    .reg-meta { font-size: 12px; color: #6B7280; margin-top: 5px; }
    
    /* 4. Badges */
    .impact-high { background-color: #FEF2F2; color: #991B1B; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #FECACA; }
    .impact-clean { background-color: #ECFDF5; color: #065F46; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #A7F3D0; }
    
    /* 5. Input Field Styling */
    .stTextInput input { background-color: #FFFFFF !important; border-color: #D1D5DB !important; }
</style>
""", unsafe_allow_html=True)

# ================= CUSTOM SIDEBAR =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
    st.markdown("### AI Powered Regulatory Compliance Checker for Contracts")
    
    # User Status
    st.success(f"👤 **{st.session_state.get('user_name', 'Analyst')}**")

    st.page_link("Home.py", label="Overview", icon="🏠")
    st.page_link("pages/Contract_Analysis.py", label="Contract Analysis", icon="📄")
    st.page_link("pages/Risk_Assessment.py", label="Risk Assessment", icon="📊")
    st.page_link("pages/Regulation_Monitor.py", label="Regulation Monitor", icon="⚖️")
    st.page_link("pages/AI_Chatbot.py", label="AI Chatbot", icon="🤖")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ================= EMAIL HELPER FUNCTION =================

def send_email_with_attachment(to_email, subject, body, file_path):
    """
    Sends an email with the PDF attachment using Gmail SMTP.
    """
    # --- CREDENTIALS ---
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "geetaglory96339@gmail.com" 
    SENDER_PASSWORD = "qwctfmkrjrwiuamg"  
    # -------------------

    if "your-email" in SENDER_EMAIL or not SENDER_EMAIL:
        st.warning("⚠️ Email not configured. Please update SENDER_EMAIL in Regulation_Monitor.py")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}")
        return False

def scan_contracts_for_regulation(reg):
    """Scans contracts for keywords matching the regulation."""
    index = read_json(CONTRACT_INDEX)
    affected_contracts = []
    
    for cid, meta in index.items():
        path = os.path.join(CONTRACTS_DIR, meta["file"])
        text = read_contract_text(path)
        
        if text:
            score, matches = match_regulation_to_contract(reg, text)
            if score > 0:
                affected_contracts.append({
                    "id": cid,
                    "name": meta["original_name"],
                    "version": meta["version"],
                    "text": text,
                    "matches": matches,
                    "file": meta["file"]
                })
    return affected_contracts

# ================= MAIN UI LOGIC =================
st.title("⚖️ Regulatory Compliance Center")
st.markdown("Monitor active regulations and **push updates** directly to affected contracts.")

# --- TOP ACTION BAR ---
col_stats, col_btn = st.columns([4, 1])
regs = read_json(REGS_FILE)

with col_stats:
    if regs:
        st.info(f"📚 Monitoring **{len(regs)}** active regulations across your portfolio.")
    else:
        st.info("📚 Monitoring **0** active regulations.")

with col_btn:
    if st.button("🔄 Fetch New Rules", type="primary", use_container_width=True):
        with st.spinner("Syncing with Global Regulatory API..."):
            new_reg = mock_fetch_regulations()
            if new_reg:
                st.success("New Rule Added!")
                st.rerun()
            else:
                st.toast("System is up to date.")

st.markdown("---")

# --- REGULATION LIST ---
if not regs:
    st.warning("No regulations found.")
else:
    for reg in regs: # If regs is a dict, you might need regs.values() depending on your JSON structure
        # Ensure we are iterating correctly. If regs is a dict {id: {data}}, use .values()
        # If it is a list of dicts, simple iteration works.
        reg_data = reg if isinstance(regs, list) else regs[reg]
        
        # 1. Regulation Card
        with st.container():
            st.markdown(f"""
            <div class="reg-card">
                <div style="display:flex; justify-content:space-between;">
                    <div class="reg-title">{reg_data.get('title', 'Unknown Regulation')}</div>
                    <div style="font-weight:600; color:#4B5563;">{reg_data.get('jurisdiction', 'Global')}</div>
                </div>
                <div style="margin: 10px 0; color:#374151;">{reg_data.get('summary', 'No summary available.')}</div>
                <div class="reg-meta">
                    <b>Keywords:</b> {', '.join(reg_data.get('keywords', []))} • <b>Effective:</b> {reg_data.get('date_published', 'N/A')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. Action Area (Expand to see impacts)
            with st.expander(f"📉 View Impact & Remediation ({reg_data.get('title')})"):
                
                impacted = scan_contracts_for_regulation(reg_data)
                
                if not impacted:
                    st.markdown(f"<span class='impact-clean'>✅ No Violations Detected</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='impact-high'>⚠️ {len(impacted)} Contracts Require Updates</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Loop through impacted contracts
                    for item in impacted:
                        c1, c2 = st.columns([2, 1])
                        
                        with c1:
                            st.write(f"**📄 {item['name']} (v{item['version']})**")
                            st.caption(f"Detected Terms: {', '.join(item['matches'])}")
                            
                            # --- EMAIL INPUT FIELD ---
                            # Use unique keys based on loop indices to avoid conflicts
                            email_key = f"email_{reg_data.get('id', 'r1')}_{item['id']}"
                            recipient = st.text_input("Notify Stakeholder (Email):", key=email_key, placeholder="e.g. client@company.com")

                        with c2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_key = f"fix_{reg_data.get('id', 'r1')}_{item['id']}"
                            
                            # --- FIX & EMAIL BUTTON ---
                            if st.button("🛠 Fix & Email Update", key=btn_key, type="primary"):
                                if not recipient:
                                    st.error("Please enter an email address first.")
                                else:
                                    # 1. GENERATE SMART UPDATE
                                    # Define the new clause explicitly
                                    new_clause = (
                                        f"5. COMPLIANCE & DATA NOTICE (Added: {datetime.now().date()})\n"
                                        f"5.1 Pursuant to the {reg_data.get('title')}, Developer agrees to implement "
                                        f"strict transparency measures regarding '{', '.join(item['matches'])}'.\n"
                                        f"5.2 Immediate written notice shall be provided to Client in the event "
                                        f"of any regulatory inquiry or data breach."
                                    )
                                    
                                    # Use the smart injector to insert BEFORE termination/warranty
                                    new_text = inject_clause_smartly(item["text"], new_clause)
                                    
                                    # 2. Create New PDF Version
                                    index = read_json(CONTRACT_INDEX)
                                    new_ver = item["version"] + 1
                                    new_filename = f"{item['id']}-v{new_ver}.pdf"
                                    new_path = os.path.join(CONTRACTS_DIR, new_filename)
                                    
                                    save_pdf(new_path, new_text)
                                    
                                    # 3. Update Database
                                    # Check if item['id'] exists to avoid errors
                                    if item['id'] in index:
                                        index[item['id']]["version"] = new_ver
                                        index[item['id']]["file"] = new_filename
                                        index[item['id']]["last_updated"] = datetime.now().isoformat()
                                        write_json(CONTRACT_INDEX, index)
                                        
                                        # 4. Send Email with Attachment
                                        email_sub = f"Contract Updated: {item['name']} (v{new_ver})"
                                        email_msg = f"Hello,\n\nThe contract '{item['name']}' has been updated to comply with '{reg_data.get('title')}'.\n\nPlease find the new version attached."
                                        
                                        with st.spinner("Sending Email..."):
                                            success = send_email_with_attachment(recipient, email_sub, email_msg, new_path)
                                        
                                        if success:
                                            st.success(f"Updated & Sent to {recipient}!")
                                            time.sleep(2)
                                            st.rerun()
                                    else:
                                        st.error("Error: Contract ID not found in index.")