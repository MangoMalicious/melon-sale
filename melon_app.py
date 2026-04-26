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

# Auth
if 'ws' not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")

# Wrapping everything in a FORM prevents "Click Off" saving
with st.sidebar.form("sale_form", clear_on_submit=True):
    # 1. Weight Input
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
    
    # 2. Manual Price (Optional)
    manual_p = st.text_input("Discount Price (RM)", placeholder="Optional...")

    # --- LIVE PRICE PREVIEW (No Dropdown) ---
    std_p = float(math.floor(weight * PRICE_PER_KG))
    
    if weight > 0:
        try:
            final_p = float(manual_p) if manual_p else std_p
            # We display the price right here in the form
            st.markdown(f"### Total: RM {final_p:.0f}")
        except:
            st.markdown(f"### Total: RM {std_p:.0f}")
    else:
        st.markdown("### Total: RM 0")

    # 3. SAVE BUTTON
    # This is the ONLY thing that triggers a save
    submitted = st.form_submit_button("Confirm & Save Sale", use_container_width=True)

    if submitted:
        if weight > 0:
            try:
                final_p = float(manual_p) if manual_p else std_p
                date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
                ws.append_row([date_str, weight, PRICE_PER_KG, final_p])
                st.cache_data.clear()
                st.rerun()
            except:
                st.error("Invalid Price")
        else:
            st.error("Enter weight first")

st.sidebar.markdown("---")

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
    rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {rev:,.0f}")
    c2.metric("Total Weight", f"{wgt:,.2f} kg")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
