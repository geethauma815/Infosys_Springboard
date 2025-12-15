import streamlit as st
import sqlite3
import hashlib
import time

# =================== PAGE CONFIG =====================
st.set_page_config(page_title="Login", layout="centered")

# =================== CSS STYLING =====================
st.markdown("""
<style>
    /* 1. Set the background of the entire app to a light grey */
    .stApp {
        background-color: #F3F4F6;
        color: #333333;
    }

    /* 2. Style the Main Content Block to look like a Card */
    /* This targets the main container where your inputs live */
    div.block-container {
        background-color: #FFFFFF;
        padding: 3rem 2rem !important;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
        max-width: 500px; /* Restrict width for a nice card look */
    }

    /* 3. Typography Styles */
    h1, h2, h3, p, label, div {
        font-family: 'Inter', sans-serif;
        color: #111827;
    }

    /* Project Heading */
    .project-heading {
        font-size: 20px;
        font-weight: 800;
        color: #111827;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 25px;
        line-height: 1.4;
        border-bottom: 2px solid #F3F4F6;
        padding-bottom: 15px;
    }
    .project-sub {
        color: #0056D2;
        font-size: 14px;
        display: block;
        font-weight: 700;
        margin-bottom: 5px;
    }

    /* Login Titles */
    .login-title {
        font-size: 24px;
        font-weight: 700;
        color: #374151;
        text-align: center;
        margin-bottom: 5px;
    }
    .login-subtitle {
        font-size: 14px;
        color: #6B7280;
        text-align: center;
        margin-bottom: 25px;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #F9FAFB;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        color: #111827;
    }
    .stTextInput input:focus {
        border-color: #0056D2;
        box-shadow: 0 0 0 1px #0056D2;
    }

    /* Primary Button */
    button[kind="primary"] {
        background-color: #0056D2 !important;
        color: white !important;
        border: none;
        width: 100%;
        padding: 10px;
        border-radius: 6px;
        font-weight: 600;
        margin-top: 10px;
    }
    button[kind="primary"]:hover {
        background-color: #00449E !important;
    }

    /* Hide standard headers */
    header, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =================== BACKEND LOGIC =====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        hashed = hash_password(password)

        # Fetch ID, Name, Email
        cursor.execute("SELECT id, name, email FROM users WHERE email=? AND password=?", (email, hashed))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None


# =================== UI CONTENT =====================

# 1. Check if already logged in (Auto-Redirect)
if st.session_state.get("logged_in"):
    st.switch_page("Home.py")

# --- NO HTML WRAPPERS NEEDED ---
# The CSS 'div.block-container' handles the card look automatically.

# 1. Project Heading
st.markdown("""
    <div class='project-heading'>
        <span class='project-sub'>AI Powered</span>
        Regulatory Compliance Checker<br>for Contracts
    </div>
""", unsafe_allow_html=True)

# 2. Login Titles
st.markdown("<div class='login-title'> Welcome Back</div>", unsafe_allow_html=True)
st.markdown("<div class='login-subtitle'>Enter your credentials to access the platform</div>", unsafe_allow_html=True)

# 3. Form
email = st.text_input("Email Address", placeholder="name@company.com")
password = st.text_input("Password", type="password", placeholder="••••••••")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Sign In", type="primary"):
    if email and password:
        user = check_login(email, password)

        if user:
            # Clear previous state always
            st.session_state.clear()

            # Store user info in session
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user[0]
            st.session_state["user_name"] = user[1]
            st.session_state["user_email"] = user[2]

            # Show Success Message
            st.success(f"✅ Login Successful! Welcome, {user[1]}.")
            
            # Wait 1 second so user sees the message, then redirect
            time.sleep(1)
            st.switch_page("Home.py")
        else:
            st.error("❌ Invalid Email or Password")
    else:
        st.warning("⚠ Please fill in all fields.")

# 4. Footer Link
st.markdown(
    "<div style='text-align:center; margin-top:15px; font-size:13px; color:#666;'>"
    "Don't have an account? <a href='pages/Register.py' target='_self' style='color:#0056D2; font-weight:600; text-decoration:none;'>Sign Up</a>"
    "</div>", 
    unsafe_allow_html=True
)