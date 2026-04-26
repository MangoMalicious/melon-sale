import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz
import io 
import math 

# CONFIG
PRICE_PER_KG = 20.00
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- INITIALIZE STATE ---
if "v_num" not in st.session_state:
    st.session_state.v_num = 0

# Auth
if 'ws' not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

# --- THE SPEED SAVE FUNCTION ---
def quick_save():
    v = st.session_state.v_num
    w_text = st.session_state.get(f"w_{v}", "")
    p_text = st.session_state.get(f"p_{v}", "")
    
    try:
        w_val = float(w_text) if w_text else 0.0
        # Auto-calc
        std_p = float(math.floor(w_val * PRICE_PER_KG))
        # Use manual price if they typed one, else use auto-calc
        p_val = float(p_text) if p_text else std_p

        if w_val > 0:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
            ws.append_row([date_str, w_val, PRICE_PER_KG, p_val])
            st.toast(f"✅ Saved RM {p_val}")
            st.cache_data.clear()
            # Reset the boxes
            st.session_state.v_num += 1
        else:
            st.error("Enter weight first")
    except:
        st.error("Invalid numbers entered")

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. OPTIONAL: Discount Box (Type this first if needed)
st.sidebar.text_input(
    "Discount Price (Optional)", 
    value="", 
    placeholder="Type final RM if discount...", 
    key=f"p_{v}"
)

# 2. WEIGHT (The Trigger)
# Pressing ENTER here saves the whole thing immediately
st.sidebar.text_input(
    "Weight (kg) + Press ENTER", 
    value="", 
    placeholder="Type weight & hit Enter", 
    key=f"w_{v}",
    on_change=quick_save
)

st.sidebar.info("Just type the weight and hit Enter. The app will calculate RM 20/kg and save it automatically.")

# --- DASHBOARD ---
@st.cache_data(ttl=10)
def load_recent_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    headers = all_values[0]
    recent_rows = all_values[-100:] if len(all_values) > 100 else all_values[1:]
    return pd.DataFrame(recent_rows, columns=headers)

df = load_recent_data()

st.title("BG Melon Sale")
if not df.empty:
    total_rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    total_wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {total_rev:,.0f}")
    c2.metric("Total Weight", f"{total_wgt:,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
