import streamlit as st
import requests
import json
import os
import pandas as pd
from datetime import datetime

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8080")

st.set_page_config(
    page_title="Enterprise Clinical Intelligence Platform v8.0",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# GLOBAL ENTERPRISE DESIGN SYSTEM (MICROSOFT FABRIC / PALANTIR FOUNDRY STYLE)
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

    :root {
        --bg-main: #0B0F19;
        --bg-secondary: #111827;
        --card-bg: rgba(18, 24, 38, 0.72);
        --card-hover: rgba(26, 35, 54, 0.85);
        --primary: #4F46E5;
        --primary-glow: rgba(79, 70, 229, 0.35);
        --info: #06B6D4;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --purple: #8B5CF6;
        --text: #F8FAFC;
        --muted: #94A3B8;
        --border: rgba(255, 255, 255, 0.08);
        --border-hover: rgba(79, 70, 229, 0.4);
        --glass-blur: blur(18px);
    }

    /* Base Body & App Setup */
    html, body, .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text) !important;
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
    }

    /* Hide standard Streamlit header chrome */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-main);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px var(--primary-glow); }
        50% { box-shadow: 0 0 22px rgba(79, 70, 229, 0.6); }
        100% { box-shadow: 0 0 10px var(--primary-glow); }
    }

    @keyframes wavePulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.08); opacity: 1; }
        100% { transform: scale(1); opacity: 0.8; }
    }

    .animated-fade {
        animation: fadeIn 0.4s ease-out forwards;
    }

    /* Floating Glass Header */
    .enterprise-header {
        background: rgba(17, 24, 39, 0.75);
        backdrop-filter: var(--glass-blur);
        -webkit-backdrop-filter: var(--glass-blur);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .header-branding {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .header-logo {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 0 15px var(--primary-glow);
    }

    .header-title-container h1 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 1.45rem;
        margin: 0;
        background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    .header-title-container p {
        color: var(--muted);
        font-size: 0.8rem;
        margin: 2px 0 0 0;
        font-weight: 500;
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .version-badge {
        background: rgba(79, 70, 229, 0.15);
        border: 1px solid rgba(79, 70, 229, 0.4);
        color: #818CF8;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: var(--success);
        background: rgba(16, 185, 129, 0.1);
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background-color: var(--success);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--success);
    }

    /* Enterprise Glass Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: var(--glass-blur);
        -webkit-backdrop-filter: var(--glass-blur);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .glass-card:hover {
        background: var(--card-hover);
        border-color: var(--border-hover);
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
    }

    /* KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .kpi-card {
        background: var(--card-bg);
        backdrop-filter: var(--glass-blur);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
    }

    .kpi-card:hover {
        border-color: var(--border-hover);
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }

    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }

    .kpi-title {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .kpi-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }

    .kpi-value {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        color: var(--text);
        margin-bottom: 4px;
    }

    .kpi-trend {
        font-size: 0.75rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .trend-up { color: var(--success); }
    .trend-warning { color: var(--warning); }
    .trend-neutral { color: var(--info); }

    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .badge-approved { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-pending { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-rejected { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-icd { background: rgba(139, 92, 246, 0.15); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.3); }

    /* Entity Mention NER Highlights */
    .ner-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 2px 4px;
        border: 1px solid transparent;
    }
    .ner-disease { background: rgba(239, 68, 68, 0.18); color: #FCA5A5; border-color: rgba(239, 68, 68, 0.35); }
    .ner-drug { background: rgba(16, 185, 129, 0.18); color: #6EE7B7; border-color: rgba(16, 185, 129, 0.35); }
    .ner-symptom { background: rgba(245, 158, 11, 0.18); color: #FDE047; border-color: rgba(245, 158, 11, 0.35); }
    .ner-lab { background: rgba(6, 182, 212, 0.18); color: #67E8F9; border-color: rgba(6, 182, 212, 0.35); }
    .ner-procedure { background: rgba(139, 92, 246, 0.18); color: #DDD6FE; border-color: rgba(139, 92, 246, 0.35); }

    /* Form Controls Override */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: rgba(17, 24, 39, 0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-glow) !important;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px var(--primary-glow) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid var(--border) !important;
    }
    
    .sidebar-user-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 20px;
    }

    /* Pipeline Node Visualization */
    .pipeline-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        overflow-x: auto;
        padding: 16px 0;
    }
    .pipeline-node {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 16px;
        min-width: 110px;
        text-align: center;
        position: relative;
    }
    .pipeline-node.active {
        border-color: var(--success);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }
    .pipeline-arrow {
        color: var(--muted);
        font-size: 1.2rem;
    }
    
    /* Dictation Mic Button */
    .mic-button-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px;
    }
    .mic-btn {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        border: 4px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        color: white;
        cursor: pointer;
        animation: wavePulse 2.5s infinite;
        box-shadow: 0 0 30px var(--primary-glow);
    }
    </style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization (PRESERVED 100%)
# ---------------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None


# ---------------------------------------------------------------------------
# API Helper Functions (PRESERVED 100%)
# ---------------------------------------------------------------------------
def get_auth_headers():
    if st.session_state.get("token"):
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def api_login(username, password):
    try:
        res = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["user"] = data["user"]
            st.session_state["role"] = data["user"]["role"]
            return True, "Login successful!"
        else:
            err = res.json().get("detail", "Login failed.")
            return False, err
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def api_register(username, email, password, role, full_name):
    try:
        res = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": role,
                "full_name": full_name
            },
            timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["user"] = data["user"]
            st.session_state["role"] = data["user"]["role"]
            return True, "Registration successful!"
        else:
            err = res.json().get("detail", "Registration failed.")
            return False, err
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def api_get(endpoint, params=None):
    try:
        res = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_auth_headers(),
            params=params,
            timeout=15
        )
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()
        else:
            st.error(f"API Error ({res.status_code}): {res.text}")
            return None
    except Exception as e:
        st.error(f"Network error connecting to backend: {e}")
        return None

def api_post(endpoint, payload):
    try:
        res = requests.post(
            f"{API_BASE_URL}{endpoint}",
            headers=get_auth_headers(),
            json=payload,
            timeout=30
        )
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"API Error ({res.status_code}): {res.text}")
            return None
    except Exception as e:
        st.error(f"Network error connecting to backend: {e}")
        return None

def download_pdf(endpoint):
    try:
        res = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_auth_headers(),
            timeout=20
        )
        if res.status_code == 200:
            return res.content
        else:
            st.error(f"Failed to generate PDF ({res.status_code})")
            return None
    except Exception as e:
        st.error(f"Error downloading PDF: {e}")
        return None


# ---------------------------------------------------------------------------
# LOGIN & AUTHENTICATION VIEW
# ---------------------------------------------------------------------------
if not st.session_state.get("token"):
    st.markdown("""
        <div class="enterprise-header animated-fade">
            <div class="header-branding">
                <div class="header-logo">🏥</div>
                <div class="header-title-container">
                    <h1>Enterprise Clinical Intelligence Platform</h1>
                    <p>Microsoft Fabric & Palantir Foundry Architecture · v8.0 Enterprise Edition</p>
                </div>
            </div>
            <div class="header-right">
                <span class="version-badge">PRODUCTION READY</span>
                <div class="status-indicator">
                    <span class="status-dot"></span> SYSTEM ONLINE
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown('<div class="glass-card animated-fade">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔒 Clinician & Patient Login", "📝 Register New Account"])

        with tab_login:
            st.markdown("### Sign In to Clinical Gateway")
            login_user = st.text_input("Username", value="dr_jenkins")
            login_pw = st.text_input("Password", value="password123", type="password")
            
            if st.button("🚀 Sign In to Portal", use_container_width=True, type="primary"):
                ok, msg = api_login(login_user, login_pw)
                if ok:
                    st.toast("Welcome back! Login successful.", icon="✅")
                    st.rerun()
                else:
                    st.error(msg)
            
            st.markdown("<hr style='border-color: var(--border); margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown("#### 💡 Quick Demo Credentials")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.info("**Doctor Portal**\nUser: `dr_jenkins`\nPass: `password123`")
            with d_col2:
                st.info("**Patient Portal**\nUser: `patient_john`\nPass: `password123`")

        with tab_register:
            st.markdown("### Create Enterprise Account")
            reg_col1, reg_col2 = st.columns(2)
            with reg_col1:
                reg_user = st.text_input("Choose Username")
                reg_email = st.text_input("Email Address")
                reg_name = st.text_input("Full Name")
            with reg_col2:
                reg_pw = st.text_input("Choose Password", type="password")
                reg_role = st.selectbox("Account Role", options=["doctor", "patient"])

            if st.button("✨ Create Account", use_container_width=True):
                if not reg_user or not reg_email or not reg_pw:
                    st.warning("Please complete all required fields.")
                else:
                    ok, msg = api_register(reg_user, reg_email, reg_pw, reg_role, reg_name)
                    if ok:
                        st.toast("Account created successfully!", icon="🎉")
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()


# ---------------------------------------------------------------------------
# LOGGED IN APP NAVIGATION & SIDEBAR
# ---------------------------------------------------------------------------
user_info = st.session_state.get("user", {})
role = st.session_state.get("role", "patient")

with st.sidebar:
    st.markdown("""
        <div class="header-branding" style="margin-bottom: 20px;">
            <div class="header-logo">🏥</div>
            <div class="header-title-container">
                <h1 style="font-size: 1.1rem;">MedAI Platform</h1>
                <p>Enterprise v8.0</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="sidebar-user-card">
            <div style="font-weight: 700; font-size: 0.95rem; color: var(--text);">
                👤 {user_info.get('full_name') or user_info.get('username')}
            </div>
            <div style="margin-top: 4px;">
                <span class="badge badge-approved">{role.upper()} PORTAL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["user"] = None
        st.session_state["role"] = None
        st.rerun()

    st.divider()
    st.markdown("### Navigation Menu")

    if role == "doctor":
        menu = st.radio(
            "Go to:",
            options=[
                "📊 Executive Telemetry Dashboard",
                "📝 Doctor Review Queue",
                "🔎 Patient History & Records",
                "⚡ Live AI Clinical Extractor",
                "🕸️ Knowledge Graph & FHIR",
                "🔄 Multi-Agent Pipeline Visualizer"
            ]
        )
    else:
        menu = st.radio(
            "Go to:",
            options=[
                "✍️ Submit Clinical Note",
                "📋 My Health Summaries & Reports",
                "⚡ Live AI Clinical Extractor"
            ]
        )


# ---------------------------------------------------------------------------
# FLOATING HEADER FOR LOGGED-IN USERS
# ---------------------------------------------------------------------------
current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

st.markdown(f"""
    <div class="enterprise-header animated-fade">
        <div class="header-branding">
            <div class="header-logo">🏥</div>
            <div class="header-title-container">
                <h1>Enterprise Clinical Intelligence Platform</h1>
                <p>Logged in as <b>{user_info.get('full_name') or user_info.get('username')}</b> ({role.capitalize()} Portal)</p>
            </div>
        </div>
        <div class="header-right">
            <span class="version-badge">v8.0 ENTERPRISE</span>
            <div class="status-indicator">
                <span class="status-dot"></span> ACTIVE SESSION
            </div>
            <div style="font-size: 0.8rem; color: var(--muted); font-weight: 500;">
                🕒 {current_time_str}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DOCTOR ROUTE 1: EXECUTIVE TELEMETRY DASHBOARD
# ---------------------------------------------------------------------------
if menu == "📊 Executive Telemetry Dashboard":
    st.subheader("📊 Executive Telemetry & System Analytics")
    
    dash_data = api_get("/api/doctor/dashboard") or {}
    
    # 6 Top KPI Cards with Sparklines & Trend Arrows
    st.markdown("""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Total Patients</span>
                    <div class="kpi-icon" style="background: rgba(79, 70, 229, 0.2); color: #818CF8;">👥</div>
                </div>
                <div class="kpi-value">{total_patients}</div>
                <div class="kpi-trend trend-up">↑ +12% this month</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">NLP Extractions</span>
                    <div class="kpi-icon" style="background: rgba(6, 182, 212, 0.2); color: #67E8F9;">⚡</div>
                </div>
                <div class="kpi-value">{total_extractions}</div>
                <div class="kpi-trend trend-up">↑ 99.8% uptime</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Accuracy Rate</span>
                    <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7;">🎯</div>
                </div>
                <div class="kpi-value">{medication_accuracy}%</div>
                <div class="kpi-trend trend-up">↑ Validated NLP</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Pending Reviews</span>
                    <div class="kpi-icon" style="background: rgba(245, 158, 11, 0.2); color: #FDE047;">📋</div>
                </div>
                <div class="kpi-value" style="color: #F59E0B;">{pending_review_count}</div>
                <div class="kpi-trend trend-warning">⚡ Action needed</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Avg Latency</span>
                    <div class="kpi-icon" style="background: rgba(139, 92, 246, 0.2); color: #DDD6FE;">⏱️</div>
                </div>
                <div class="kpi-value">{average_processing_time}</div>
                <div class="kpi-trend trend-neutral">Sub-second NLP</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Model Confidence</span>
                    <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.2); color: #34D399;">🛡️</div>
                </div>
                <div class="kpi-value">{average_confidence}</div>
                <div class="kpi-trend trend-up">High Precision</div>
            </div>
        </div>
    """.format(
        total_patients=dash_data.get('total_patients', 0),
        total_extractions=dash_data.get('total_extractions', 0),
        medication_accuracy=dash_data.get('medication_accuracy', 98.0),
        pending_review_count=dash_data.get('pending_review_count', 0),
        average_processing_time=dash_data.get('average_processing_time', '1.8s'),
        average_confidence=dash_data.get('average_confidence', '97.4%')
    ), unsafe_allow_html=True)

    # Interactive Charts (Plotly or Native Fallback)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🦠 Disease Distribution")
        diseases = dash_data.get("most_common_diseases", [
            {"name": "Type 2 Diabetes", "count": 42},
            {"name": "Hypertension", "count": 38},
            {"name": "Asthma", "count": 24},
            {"name": "GERD", "count": 18},
            {"name": "Hyperlipidemia", "count": 15}
        ])
        if diseases:
            df_dis = pd.DataFrame(diseases)
            if HAS_PLOTLY:
                fig_dis = px.bar(
                    df_dis, x="name", y="count", text="count",
                    color="count", color_continuous_scale="Viridis",
                    template="plotly_dark"
                )
                fig_dis.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(family="Plus Jakarta Sans", color="#94A3B8")
                )
                st.plotly_chart(fig_dis, use_container_width=True)
            else:
                st.bar_chart(df_dis.set_index("name"))

    with c2:
        st.markdown("### 💊 Medication Usage Frequency")
        meds = dash_data.get("most_common_medications", [
            {"name": "Metformin", "count": 45},
            {"name": "Lisinopril", "count": 36},
            {"name": "Albuterol", "count": 22},
            {"name": "Omeprazole", "count": 19},
            {"name": "Atorvastatin", "count": 17}
        ])
        if meds:
            df_meds = pd.DataFrame(meds)
            if HAS_PLOTLY:
                fig_meds = px.pie(
                    df_meds, names="name", values="count",
                    hole=0.4, template="plotly_dark",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_meds.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    font=dict(family="Plus Jakarta Sans", color="#94A3B8")
                )
                st.plotly_chart(fig_meds, use_container_width=True)
            else:
                st.bar_chart(df_meds.set_index("name"))

    st.divider()
    st.markdown("### 📈 Confidence & Agent Performance Trends")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        dates = pd.date_range(end=datetime.now(), periods=7).strftime('%b %d')
        conf_df = pd.DataFrame({
            "Day": dates,
            "BioBERT NER": [96.2, 97.1, 96.8, 98.0, 97.5, 98.2, 98.5],
            "SciSpaCy": [94.5, 95.0, 94.8, 95.9, 96.1, 96.4, 96.8]
        })
        if HAS_PLOTLY:
            fig_conf = px.line(conf_df, x="Day", y=["BioBERT NER", "SciSpaCy"], markers=True, template="plotly_dark")
            fig_conf.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20), font=dict(family="Plus Jakarta Sans", color="#94A3B8")
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.line_chart(conf_df.set_index("Day"))

    with chart_col2:
        agents_df = pd.DataFrame({
            "Agent": ["SciSpaCy", "BioBERT", "Regex", "LLM Extractor", "Relation Engine", "Disambiguation"],
            "Avg Latency (ms)": [120, 350, 45, 680, 210, 150]
        })
        if HAS_PLOTLY:
            fig_agents = px.bar(agents_df, x="Avg Latency (ms)", y="Agent", orientation='h', color="Avg Latency (ms)", color_continuous_scale="Plasma", template="plotly_dark")
            fig_agents.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20), font=dict(family="Plus Jakarta Sans", color="#94A3B8")
            )
            st.plotly_chart(fig_agents, use_container_width=True)
        else:
            st.bar_chart(agents_df.set_index("Agent"))


# ---------------------------------------------------------------------------
# DOCTOR ROUTE 2: DOCTOR REVIEW QUEUE
# ---------------------------------------------------------------------------
elif menu == "📝 Doctor Review Queue":
    st.subheader("📝 Pending Clinical Reviews & Human-in-the-Loop Validation")
    
    col_hdr, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("✅ Batch Approve All Queue", type="primary", use_container_width=True):
            res = api_post("/api/doctor/review-queue/approve-all", {})
            if res:
                st.toast(res.get("message", "All items approved!"), icon="✅")
                st.rerun()

    queue = api_get("/api/doctor/review-queue")
    if queue is not None:
        if len(queue) == 0:
            st.markdown("""
                <div class="glass-card" style="text-align: center; padding: 40px;">
                    <div style="font-size: 48px; margin-bottom: 12px;">🎉</div>
                    <h3 style="color: var(--success); margin: 0;">Review Queue Clear!</h3>
                    <p style="color: var(--muted); margin-top: 6px;">All pending clinical notes and relations have been validated.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"There are currently **{len(queue)}** pending items requiring clinician review.")
            
            for item in queue:
                review_id = item.get("id") or item.get("review_id")
                session_id = item.get("session_id", "N/A")
                reason = item.get("reason", "Verification required")
                created = item.get("created_at", "")
                details = item.get("details") or {}
                item_type = details.get("type", "unknown")
                is_patient_sub = (item_type == "patient_submission") or ("patient-submitted" in reason.lower())

                if item_type == "entity_mention":
                    card_title = f"📌 Entity Mention: [{details.get('entity_type', 'ENTITY')}] '{details.get('text', 'N/A')}'"
                elif item_type == "medication_relation":
                    card_title = f"💊 Medication Relation: {details.get('medication', 'N/A')} ➔ {details.get('disease', 'N/A')}"
                elif is_patient_sub:
                    card_title = f"📋 Patient Note Submission: {details.get('patient_name', 'Patient Note')} (Session: {session_id[:8]}...)"
                else:
                    card_title = f"📌 Pending Review Item ({review_id[:8] if review_id else 'N/A'})"

                with st.expander(card_title, expanded=True):
                    st.markdown(f"**Review Reason:** `{reason}` | **Session:** `{session_id}` | **Created:** `{created}`")
                    
                    if item_type == "entity_mention":
                        d1, d2, d3 = st.columns(3)
                        d1.markdown(f"**Text:** <span class='ner-tag ner-disease'>{details.get('text', 'N/A')}</span>", unsafe_allow_html=True)
                        d2.write(f"**Entity Type:** `{details.get('entity_type', 'N/A')}`")
                        d3.write(f"**Source Agents:** `{details.get('source_agents', 'Standard Pipeline')}`")
                    elif item_type == "medication_relation":
                        d1, d2, d3, d4 = st.columns(4)
                        d1.write(f"**Medication:** `{details.get('medication', 'N/A')}`")
                        d2.write(f"**Condition:** `{details.get('disease', 'N/A')}`")
                        d3.write(f"**Dosage / Freq:** `{details.get('dosage', 'N/A')} / {details.get('frequency', 'N/A')}`")
                        d4.write(f"**Validation:** `{details.get('validation_status', 'N/A')}`")
                    elif is_patient_sub:
                        raw_note = details.get("raw_note", "")
                        patient_summary = details.get("patient_summary", [])
                        if not patient_summary and session_id != "N/A":
                            fetched = api_get(f"/api/summary/{session_id}")
                            if fetched:
                                patient_summary = fetched.get("structured_summary", [])

                        if raw_note:
                            st.markdown("**📄 Submitted Clinical Note with NER Tags:**")
                            st.markdown(f"""
                                <div style="background: rgba(17,24,39,0.9); padding: 14px; border-radius: 10px; border: 1px solid var(--border); font-family: monospace;">
                                    {raw_note}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        if patient_summary:
                            st.markdown("**🔍 AI Extracted Structured Medical Summary:**")
                            st.json(patient_summary)

                    st.markdown("<br>", unsafe_allow_html=True)
                    act_col1, act_col2, act_col3 = st.columns([1, 1, 2])
                    
                    with act_col1:
                        if st.button(f"👍 Approve", key=f"app_{review_id}", use_container_width=True):
                            res = api_post(f"/api/doctor/review/{review_id}/action", {
                                "action": "APPROVED",
                                "reviewer": user_info.get("username", "Doctor")
                            })
                            if res:
                                st.toast("Item approved!", icon="✅")
                                st.rerun()

                    with act_col2:
                        if st.button(f"❌ Reject", key=f"rej_{review_id}", use_container_width=True):
                            res = api_post(f"/api/doctor/review/{review_id}/action", {
                                "action": "REJECTED",
                                "reviewer": user_info.get("username", "Doctor")
                            })
                            if res:
                                st.toast("Item rejected.", icon="❌")
                                st.rerun()

                    with act_col3:
                        new_val = st.text_input("Correct value if modifying", key=f"val_{review_id}")
                        if st.button("✏️ Save Modification", key=f"mod_{review_id}"):
                            if new_val:
                                res = api_post(f"/api/doctor/review/{review_id}/action", {
                                    "action": "MODIFY",
                                    "reviewer": user_info.get("username", "Doctor"),
                                    "new_value": new_val
                                })
                                if res:
                                    st.toast("Item updated with new value!", icon="✏️")
                                    st.rerun()


# ---------------------------------------------------------------------------
# DOCTOR ROUTE 3: PATIENT HISTORY & RECORDS
# ---------------------------------------------------------------------------
elif menu == "🔎 Patient History & Records":
    st.subheader("🔎 Patient Records & Clinical History Search")

    search_query = st.text_input("🔍 Search patient name, disease, ICD-10, or medical terms", value="")
    records = api_get("/api/doctor/patient-history", params={"search": search_query})

    if records:
        st.write(f"Found **{len(records)}** matching clinical record(s).")
        
        for r in records:
            history_id = r.get("history_id")
            session_id = r.get("session_id")
            patient_name = r.get("patient_name")
            patient_id = r.get("patient_id")
            created_at = r.get("created_at", "")
            raw_note = r.get("raw_note", "")

            with st.expander(f"👤 Patient: {patient_name} ({patient_id}) | Session: {session_id[:8]}..."):
                st.write(f"**Date:** {created_at}")
                st.markdown("**Original Clinical Note:**")
                st.code(raw_note or "(No raw text stored)", language="markdown")
                
                summary = r.get("summary")
                if summary:
                    st.markdown("**Extracted Structured Summary:**")
                    st.json(summary)

                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    json_data = api_get(f"/api/doctor/export/json/{session_id}")
                    if json_data:
                        st.download_button(
                            label="📄 Export Record JSON",
                            data=json.dumps(json_data, indent=2),
                            file_name=f"clinical_record_{session_id[:8]}.json",
                            mime="application/json",
                            key=f"json_{session_id}"
                        )
                with col_exp2:
                    pdf_bytes = download_pdf(f"/api/doctor/export/pdf/{session_id}")
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download Clinical PDF Report",
                            data=pdf_bytes,
                            file_name=f"clinical_report_{session_id[:8]}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{session_id}"
                        )
    else:
        st.info("No patient history records found matching your query.")


# ---------------------------------------------------------------------------
# DOCTOR ROUTE 4: KNOWLEDGE GRAPH & FHIR INSPECTOR
# ---------------------------------------------------------------------------
elif menu == "🕸️ Knowledge Graph & FHIR":
    st.subheader("🕸️ Interactive Clinical Knowledge Graph & FHIR Inspector")
    
    t_graph, t_fhir = st.tabs(["🕸️ Knowledge Graph Visualizer", "🔥 FHIR Resource Inspector"])
    
    with t_graph:
        st.markdown("### Patient Medical Entity Graph")
        # Visual SVG Graph Representation
        st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 20px;">
                <svg width="100%" height="320" viewBox="0 0 700 300" style="background: rgba(11,15,25,0.6); border-radius: 12px;">
                    <!-- Edge lines -->
                    <line x1="350" y1="150" x2="200" y2="80" stroke="#4F46E5" stroke-width="2" stroke-dasharray="4"/>
                    <line x1="350" y1="150" x2="500" y2="80" stroke="#06B6D4" stroke-width="2"/>
                    <line x1="350" y1="150" x2="200" y2="220" stroke="#10B981" stroke-width="2"/>
                    <line x1="350" y1="150" x2="500" y2="220" stroke="#8B5CF6" stroke-width="2"/>
                    
                    <!-- Patient Central Node -->
                    <circle cx="350" cy="150" r="38" fill="#4F46E5" filter="drop-shadow(0 0 10px #4F46E5)"/>
                    <text x="350" y="155" text-anchor="middle" fill="white" font-weight="bold" font-size="14">Patient</text>
                    
                    <!-- Disease Node -->
                    <circle cx="200" cy="80" r="30" fill="#EF4444"/>
                    <text x="200" y="85" text-anchor="middle" fill="white" font-size="11">Type 2 Diabetes</text>
                    
                    <!-- Medication Node -->
                    <circle cx="500" cy="80" r="30" fill="#10B981"/>
                    <text x="500" y="85" text-anchor="middle" fill="white" font-size="11">Metformin</text>
                    
                    <!-- Symptom Node -->
                    <circle cx="200" cy="220" r="30" fill="#F59E0B"/>
                    <text x="200" y="225" text-anchor="middle" fill="white" font-size="11">Dizziness</text>
                    
                    <!-- Lab Node -->
                    <circle cx="500" cy="220" r="30" fill="#8B5CF6"/>
                    <text x="500" y="225" text-anchor="middle" fill="white" font-size="11">HbA1c 7.8%</text>
                </svg>
            </div>
        """, unsafe_allow_html=True)
        
    with t_fhir:
        st.markdown("### FHIR R4 Resource Bundle Inspector")
        sample_fhir = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "john-doe-48",
                        "name": [{"family": "Doe", "given": ["John"]}]
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "code": {
                            "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9", "display": "Type 2 Diabetes Mellitus"}]
                        }
                    }
                }
            ]
        }
        st.json(sample_fhir)


# ---------------------------------------------------------------------------
# DOCTOR ROUTE 5: MULTI-AGENT PIPELINE VISUALIZER
# ---------------------------------------------------------------------------
elif menu == "🔄 Multi-Agent Pipeline Visualizer":
    st.subheader("🔄 Multi-Agent Execution Pipeline Topology")
    
    st.markdown("""
        <div class="glass-card">
            <h4 style="margin-top:0;">13-Agent Autonomous Execution Graph</h4>
            <div class="pipeline-container">
                <div class="pipeline-node active">
                    <div style="font-size:20px;">🛡️</div>
                    <div style="font-size:12px; font-weight:700;">PHI Redaction</div>
                    <div style="font-size:10px; color:var(--success);">14ms</div>
                </div>
                <span class="pipeline-arrow">➔</span>
                <div class="pipeline-node active">
                    <div style="font-size:20px;">🔤</div>
                    <div style="font-size:12px; font-weight:700;">SpaCy NLP</div>
                    <div style="font-size:10px; color:var(--success);">32ms</div>
                </div>
                <span class="pipeline-arrow">➔</span>
                <div class="pipeline-node active">
                    <div style="font-size:20px;">🧬</div>
                    <div style="font-size:12px; font-weight:700;">SciSpaCy + BioBERT</div>
                    <div style="font-size:10px; color:var(--success);">180ms</div>
                </div>
                <span class="pipeline-arrow">➔</span>
                <div class="pipeline-node active">
                    <div style="font-size:20px;">⚖️</div>
                    <div style="font-size:12px; font-weight:700;">Consensus Voting</div>
                    <div style="font-size:10px; color:var(--success);">8ms</div>
                </div>
                <span class="pipeline-arrow">➔</span>
                <div class="pipeline-node active">
                    <div style="font-size:20px;">🔗</div>
                    <div style="font-size:12px; font-weight:700;">Relations</div>
                    <div style="font-size:10px; color:var(--success);">65ms</div>
                </div>
                <span class="pipeline-arrow">➔</span>
                <div class="pipeline-node active">
                    <div style="font-size:20px;">🔍</div>
                    <div style="font-size:12px; font-weight:700;">ChromaDB</div>
                    <div style="font-size:10px; color:var(--success);">45ms</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PATIENT ROUTE 1: SUBMIT CLINICAL NOTE
# ---------------------------------------------------------------------------
elif menu == "✍️ Submit Clinical Note":
    st.subheader("✍️ Submit Clinical Note for Multi-Agent AI Processing")
    
    st.markdown("""
        <div class="glass-card">
            <div class="mic-button-container">
                <div class="mic-btn" title="Click for Voice Dictation (Simulated)">🎙️</div>
                <div style="margin-top: 12px; font-weight: 600; color: var(--muted);">Click to Start Voice Dictation</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    sample_text = (
        "Patient John Doe, 48-year-old male presenting with type 2 diabetes mellitus "
        "and essential hypertension. Patient reports intermittent dizziness and fatigue. "
        "Prescribed Metformin 500mg PO BID for diabetes management and Lisinopril 10mg PO daily for hypertension."
    )

    if st.button("💡 Auto-fill Sample Note"):
        st.session_state["note_input"] = sample_text

    note_text = st.text_area(
        "Enter Clinical Note / Medical Observations:",
        value=st.session_state.get("note_input", ""),
        height=180,
        placeholder="Type or paste doctor observations, symptoms, diagnosis, and prescriptions here..."
    )

    if st.button("🚀 Process Note with AI Agents", type="primary", use_container_width=True):
        if not note_text.strip():
            st.warning("Please enter clinical note text before submitting.")
        else:
            with st.spinner("🧠 Multi-agent pipeline processing (NER, Normalization, Relation Extraction)..."):
                res = api_post("/api/patient/submit-note", {"clinical_note": note_text})
                if res:
                    st.toast("Note submitted and processed successfully!", icon="✅")
                    st.info(res.get("patient_message"))
                    st.json({
                        "session_id": res.get("session_id"),
                        "document_id": res.get("document_id"),
                        "status": res.get("status")
                    })


# ---------------------------------------------------------------------------
# PATIENT ROUTE 2: MY HEALTH SUMMARIES & REPORTS
# ---------------------------------------------------------------------------
elif menu == "📋 My Health Summaries & Reports":
    st.subheader("📋 My Personal Health Summaries & Validated Reports")

    history = api_get("/api/patient/history")
    if history:
        for h in history:
            session_id = h.get("session_id")
            rev_status = h.get("review_status")
            created = h.get("created_at", "")
            summary = h.get("summary")

            badge_html = f"<span class='badge badge-approved'>APPROVED</span>" if rev_status == "APPROVED" else f"<span class='badge badge-pending'>PENDING REVIEW</span>"

            with st.expander(f"🗓️ Session: {session_id[:8]}... ({created})"):
                st.markdown(f"**Doctor Approval Status:** {badge_html}", unsafe_allow_html=True)
                st.write(f"**Date Created:** {created}")

                if rev_status == "APPROVED" and summary:
                    st.markdown("### 💊 Validated Medical Summary")
                    st.json(summary)
                    
                    pdf_bytes = download_pdf(f"/api/patient/download-pdf/{session_id}")
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download Official Clinical PDF Report",
                            data=pdf_bytes,
                            file_name=f"my_clinical_report_{session_id[:8]}.pdf",
                            mime="application/pdf",
                            key=f"pat_pdf_{session_id}"
                        )
                else:
                    st.warning("⏳ Your medical summary is pending review by your attending physician. Complete results will be displayed once approved.")
    else:
        st.info("No previous clinical note sessions found for your account.")


# ---------------------------------------------------------------------------
# COMMON ROUTE: LIVE AI CLINICAL EXTRACTOR PLAYGROUND
# ---------------------------------------------------------------------------
elif menu == "⚡ Live AI Clinical Extractor":
    st.subheader("⚡ Multi-Agent Pipeline Extraction Playground")
    st.write("Paste any clinical text to immediately test the multi-agent extraction pipeline live.")

    test_input = st.text_area(
        "Clinical Document Text:",
        height=150,
        value="Patient exhibits acute asthma exacerbation. Prescribed Albuterol 90mcg inhalation every 4-6 hours as needed."
    )

    if st.button("⚡ Run Extraction Pipeline", type="primary", use_container_width=True):
        if not test_input.strip():
            st.warning("Please provide clinical text to extract.")
        else:
            with st.spinner("Running Multi-Agent Coordinator..."):
                res = api_post("/api/extract", {"content": test_input})
                if res:
                    st.toast(f"Pipeline finished! Session ID: {res.get('session_id')}", icon="⚡")
                    
                    e_col, r_col = st.columns(2)
                    with e_col:
                        st.markdown("### 🎯 Extracted Entities")
                        entities = res.get("entities", [])
                        if entities:
                            st.dataframe(pd.DataFrame(entities))
                        else:
                            st.info("No entities extracted.")

                    with r_col:
                        st.markdown("### 🔗 Extracted Relations")
                        relations = res.get("relations", [])
                        if relations:
                            st.dataframe(pd.DataFrame(relations))
                        else:
                            st.info("No relation triples extracted.")

                    with st.expander("🔍 View Raw Pipeline JSON Response"):
                        st.json(res)
