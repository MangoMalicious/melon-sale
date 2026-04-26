import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz
import math

# CONFIG
PRICE_PER_KG = 20.0
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing"

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- GOOGLE SHEETS ---
if "ws" not in st.session_state:
    try:
        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_url(SHEET_URL)
        st.session_state.ws = sh.get_worksheet(0)
    except:
        st.error("Check Google Sheet Connection")
        st.stop()

ws = st.session_state.ws

# --- STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "weight" not in st.session_state:
    st.session_state.weight = 0.0
if "final_price" not in st.session_state:
    st.session_state.final_price = 0.0

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")

# STEP 1: INPUT
if st.session_state.step == 1:
    # Adding an on_change here captures the FIRST ENTER
    def move_to_step2():
        if st.session_state.temp_w > 0:
            st.session_state.weight = st.session_state.temp_w
            # Calculate price
            base = st.session_state.weight * PRICE_PER_KG
            disc = st.session_state.get("temp_d", 0.0)
            st.session_state.final_price = math.floor(base * (1 - disc / 100))
            st.session_state.step = 2

    st.sidebar.number_input(
        "Weight (kg)", 
        min_value=0.0, 
        step=0.1, 
        format="%.2f", 
        key="temp_w", 
        on_change=move_to_step2
    )
    
    st.sidebar.number_input(
        "Discount (%)", 
        min_value=0.0, 
        max_value=100.0, 
        step=1.0, 
        key="temp_d"
    )

    if st.sidebar.button("Click for Preview (or hit Enter)"):
        move_to_step2()
        st.rerun()

# STEP 2: CONFIRMATION
elif st.session_state.step == 2:
    st.sidebar.info("✅ PREVIEW LOCKED")
    st.sidebar.write(f"**Weight:** {st.session_state.weight} kg")
    st.sidebar.write(f"**Total Price:** RM {st.session_state.final_price}")
    
    # This button captures the SECOND ENTER
    # In Streamlit, the primary button is triggered by Enter when the page reruns
    if st.sidebar.button("PRESS ENTER TO SAVE", type="primary", use_container_width=True):
        try:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y")
            ws.append_row([
                date_str, 
                st.session_state.weight, 
                PRICE_PER_KG, 
                st.session_state.final_price
            ])
            st.toast("Saved!")
            st.session_state.step = 1
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

    if st.sidebar.button("Cancel / Fix"):
        st.session_state.step = 1
        st.rerun()

# --- DASHBOARD ---
st.title("BG Melon Sale")

@st.cache_data(ttl=10)
def load_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    return pd.DataFrame(all_values[1:], columns=all_values[0])

df = load_data()

if not df.empty:
    df['Total_RM'] = pd.to_numeric(df.iloc[:, 3], errors='coerce')
    st.metric("Total Revenue", f"RM {df['Total_RM'].sum():,.0f}")
    st.dataframe(df.iloc[::-1], use_container_width=True)
