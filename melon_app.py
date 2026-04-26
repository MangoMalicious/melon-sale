import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz
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

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. Manual Price (Type this first if giving a discount)
manual_p_text = st.sidebar.text_input(
    "Discount Price (Optional)", 
    value="", 
    placeholder="Final RM...", 
    key=f"p_{v}"
)

# 2. Weight Input (Number Input updates LIVE)
weight = st.sidebar.number_input(
    "Weight (kg)", 
    min_value=0.0, 
    step=0.1, 
    format="%.2f",
    key=f"w_{v}"
)

# --- THE LIVE PREVIEW DROPDOWN ---
if weight > 0:
    std_p = float(math.floor(weight * PRICE_PER_KG))
    
    # Logic to determine final price
    try:
        final_p = float(manual_p_text) if manual_p_text else std_p
    except:
        final_p = std_p

    with st.sidebar.expander("📊 Price Preview (Check Before Saving)", expanded=True):
        st.write(f"Weight: **{weight} kg**")
        
        if manual_p_text:
            st.write(f"Original: ~~RM {std_p:.0f}~~")
            st.write(f"**Final Total: RM {final_p:.0f}**")
        else:
            st.write(f"**Auto Total: RM {std_p:.0f}**")
        
        # This is the ONLY way to save. Clicking outside does nothing.
        if st.button("Confirm & Save Sale", use_container_width=True):
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
            ws.append_row([date_str, weight, PRICE_PER_KG, final_p])
            st.cache_data.clear()
            st.session_state.v_num += 1 # Reset form
            st.rerun()

st.sidebar.markdown("---")

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
    rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {rev:,.0f}")
    c2.metric("Total Weight", f"{wgt:,.2f} kg")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
