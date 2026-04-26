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

# --- SAVE FUNCTION (Called on Enter) ---
def save_sale_callback():
    v = st.session_state.v_num
    # Get current values from state
    w_text = st.session_state.get(f"w_{v}", "")
    p_text = st.session_state.get(f"p_{v}", "")
    
    try:
        w_val = float(w_text) if w_text else 0.0
    except:
        w_val = 0.0
        
    # Logic: if price is blank, use calculated price
    calc_p = float(math.floor(w_val * PRICE_PER_KG))
    try:
        p_val = float(p_text) if p_text else calc_p
    except:
        p_val = calc_p

    if w_val > 0 and p_val > 0:
        date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
        ws.append_row([date_str, w_val, PRICE_PER_KG, p_val])
        st.toast(f"✅ Saved RM {p_val}")
        st.cache_data.clear()
        # Reset form by changing version
        st.session_state.v_num += 1
    else:
        st.error("Missing Weight or Price")

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. Weight Input
# Pressing Enter here triggers a rerun, which calculates the placeholder
weight_text = st.sidebar.text_input(
    "Weight (kg)", 
    value="", 
    placeholder="Enter weight...", 
    key=f"w_{v}"
)

try:
    weight = float(weight_text) if weight_text else 0.0
except:
    weight = 0.0

# 2. Calculation
calc_price = float(math.floor(weight * PRICE_PER_KG)) if weight > 0 else 0.0
p_placeholder = f"RM {calc_price:.0f} (Enter to save)" if weight > 0 else "Enter price..."

# 3. Price Input (THE TRIGGER)
# 'on_change' runs the save_sale_callback the moment Enter is pressed
st.sidebar.text_input(
    "Final Price (RM)", 
    value="", 
    placeholder=p_placeholder, 
    key=f"p_{v}",
    on_change=save_sale_callback
)

st.sidebar.button("Manual Save", on_click=save_sale_callback)

# --- DASHBOARD & DATA ---
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
    st.subheader("Sales History")
    st.dataframe(df, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.sidebar.download_button("Download Excel", data=buffer.getvalue(), file_name="sales.xlsx")
else:
    st.info("No sales logged yet.")
