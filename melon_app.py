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

# --- SAVE LOGIC ---
def save_sale_callback():
    v = st.session_state.v_num
    w_text = st.session_state.get(f"w_{v}", "")
    p_text = st.session_state.get(f"p_{v}", "")
    
    try:
        w_val = float(w_text) if w_text else 0.0
        # Calc standard price
        calc_p = float(math.floor(w_val * PRICE_PER_KG))
        # Use manual price if entered, else use calculated
        p_val = float(p_text) if p_text else calc_p

        if w_val > 0:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
            # Columns: Date, Weight, Rate, Final Total
            ws.append_row([date_str, w_val, PRICE_PER_KG, p_val])
            st.toast(f"✅ Saved RM {p_val}")
            st.cache_data.clear()
            st.session_state.v_num += 1
        else:
            st.error("Enter weight first!")
    except Exception as e:
        st.error(f"Error: {e}")

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. WEIGHT (Starts blank)
weight_input = st.sidebar.text_input(
    "Weight (kg)", 
    value="", 
    placeholder="Enter weight...", 
    key=f"w_{v}"
)

# 2. PRICE (Starts blank)
price_input = st.sidebar.text_input(
    "Final Price (RM)", 
    value="", 
    placeholder="Leave blank for auto-calc", 
    key=f"p_{v}"
)

# --- REAL-TIME DISCOUNT CHECK ---
try:
    w_float = float(weight_input) if weight_input else 0.0
    p_float = float(price_input) if price_input else 0.0
    std_price = float(math.floor(w_float * PRICE_PER_KG))
    
    if w_float > 0:
        if p_float > 0 and p_float < std_price:
            diff = std_price - p_float
            pct = (diff / std_price) * 100
            st.sidebar.warning(f"Discount: -RM {diff:.0f} ({pct:.1f}%)")
        elif p_float == 0:
            st.sidebar.info(f"Standard Price: RM {std_price:.0f}")
except:
    pass

# 3. THE TRIGGER
if st.sidebar.button("Save Sale (or hit Enter)"):
    save_sale_callback()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Hit Enter in either box to update the calculation or Save.")

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
    # Use standard pandas conversion for metrics
    total_rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    total_wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {total_rev:,.0f}")
    c2.metric("Total Weight", f"{total_wgt:,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
