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

# --- SAVE CALLBACK ---
def quick_save():
    v = st.session_state.v_num
    # Get weight from the number_input and price from the text_input
    w_val = st.session_state.get(f"w_{v}", 0.0)
    p_text = st.session_state.get(f"p_{v}", "")
    
    std_p = float(math.floor(w_val * PRICE_PER_KG))
    
    try:
        p_val = float(p_text) if p_text else std_p
        if w_val > 0:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
            ws.append_row([date_str, w_val, PRICE_PER_KG, p_val])
            st.cache_data.clear()
            # Increment version to reset inputs to blank/0.0
            st.session_state.v_num += 1
    except:
        pass

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. Manual Price (Optional - Text Input)
manual_price_text = st.sidebar.text_input(
    "Discount Price (Optional)", 
    value="", 
    placeholder="Final RM...", 
    key=f"p_{v}"
)

# 2. Weight (Number Input for LIVE updating)
# We use a number_input here because it updates the state immediately
weight = st.sidebar.number_input(
    "Weight (kg)", 
    min_value=0.0, 
    step=0.1, 
    format="%.2f",
    key=f"w_{v}"
)

# --- THE DROPDOWN PREVIEW ---
if weight > 0:
    std_p = float(math.floor(weight * PRICE_PER_KG))
    
    with st.sidebar.expander("📊 Price Preview", expanded=True):
        if manual_price_text:
            try:
                m_val = float(manual_price_text)
                st.write(f"Weight: **{weight} kg**")
                st.write(f"Manual Price: **RM {m_val:.0f}**")
                st.caption(f"~~Original: RM {std_p:.0f}~~")
            except:
                st.write(f"Weight: **{weight} kg**")
                st.write(f"Auto Total: **RM {std_p:.0f}**")
        else:
            st.write(f"Weight: **{weight} kg**")
            st.write(f"Auto Total: **RM {std_p:.0f}**")
        
        # This button replaces the "Enter" trigger for better reliability
        if st.button("Save This Sale"):
            quick_save()
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
    # Column 3 is Final Total, Column 1 is Weight
    rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {rev:,.0f}")
    c2.metric("Total Weight", f"{wgt:,.2f} kg")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
