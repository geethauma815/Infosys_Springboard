import streamlit as st
import sqlite3
import hashlib
import time

# =================== PAGE CONFIG =====================
st.set_page_config(page_title="Register", layout="centered")

# =================== CSS STYLING =====================
st.markdown("""
<style>
    /* 1. Set the background of the entire app to a light grey */
    .stApp {
        background-color: #F3F4F6;
        color: #333333;
    }

    /* 2. Style the Main Content Block to look like a Card */
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

    /* Form Titles */
    .reg-title {
        font-size: 24px;
        font-weight: 700;
        color: #374151;
        text-align: center;
        margin-bottom: 5px;
    }
    .reg-subtitle {
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

def register_user(name, email, password):
    conn = None
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)
        conn.commit()

        hashed = hash_password(password)
        cursor.execute("INSERT INTO users(name, email, password) VALUES(?,?,?)", (name, email, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("❌ Registration failed: This email address is already registered.")
        return False
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


# =================== UI CONTENT =====================

# Check success state
if st.session_state.get("registration_success"):
    st.success("🎉 Registration successful! Redirecting to login...")
    time.sleep(1)
    st.session_state.pop("registration_success")
    # Redirect to Home.py (or whatever your login entry point is)
    st.switch_page("Home.py")

# 1. Project Heading
st.markdown("""
    <div class='project-heading'>
        <span class='project-sub'>AI Powered</span>
        Regulatory Compliance Checker<br>for Contracts
    </div>
""", unsafe_allow_html=True)

# 2. Page Titles
st.markdown("<div class='reg-title'>🚀 Create Account</div>", unsafe_allow_html=True)
st.markdown("<div class='reg-subtitle'>Start managing your contracts today.</div>", unsafe_allow_html=True)

# 3. Form
with st.form("registration_form"):
    name = st.text_input("Full Name", placeholder="John Doe")
    email = st.text_input("Email Address", placeholder="name@company.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")

    submitted = st.form_submit_button("Register", type="primary")

    if submitted:
        if name and email and password:
            if register_user(name, email, password):
                st.session_state["registration_success"] = True 
                st.rerun()
        else:
            st.error("⚠ Please fill in all fields.")

# 4. Footer Link
st.markdown(
    "<div style='text-align:center; margin-top:15px; font-size:14px;'>"
    "Already have an account? "
    "<a href='Home.py' target='_self' style='color:#0056D2; text-decoration:none; font-weight:600;'>Log In</a>"
    "</div>",
    unsafe_allow_html=True
)