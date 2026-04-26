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

# --- GOOGLE SHEETS CONNECTION ---
if "ws" not in st.session_state:
    try:
        creds = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_url(SHEET_URL)
        st.session_state.ws = sh.get_worksheet(0)
    except Exception as e:
        st.error(f"Sheet connection failed: {e}")
        st.stop()

ws = st.session_state.ws

# --- INITIALIZE STATE ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "weight" not in st.session_state:
    st.session_state.weight = 0.0
if "final_price" not in st.session_state:
    st.session_state.final_price = 0.0

# --- SIDEBAR LOGIC ---
st.sidebar.header("Log New Sale")

# STEP 1: INPUT AND PREVIEW
if st.session_state.step == 1:
    weight = st.sidebar.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
    discount = st.sidebar.number_input("Discount (%)", min_value=0.0, max_value=100.0, step=1.0)

    # Live math (Floored to keep it simple for change-giving)
    base_price = weight * PRICE_PER_KG
    calc_final = math.floor(base_price * (1 - discount / 100))

    if weight > 0:
        st.sidebar.markdown(f"### Total: RM {calc_final}")

    if st.sidebar.button("Enter (Preview)", use_container_width=True):
        if weight <= 0:
            st.sidebar.error("Enter valid weight")
        else:
            st.session_state.weight = weight
            st.session_state.final_price = calc_final
            st.session_state.step = 2
            st.rerun()

# STEP 2: LOCK AND CONFIRM
elif st.session_state.step == 2:
    st.sidebar.warning("⚠️ Review Sale Details")
    st.sidebar.write(f"**Weight:** {st.session_state.weight} kg")
    st.sidebar.write(f"**Price:** RM {st.session_state.final_price}")
    
    col1, col2 = st.sidebar.columns(2)
    
    if col1.button("Confirm Save", type="primary", use_container_width=True):
        try:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y")
            ws.append_row([
                date_str, 
                st.session_state.weight, 
                PRICE_PER_KG, 
                st.session_state.final_price
            ])
            st.toast("Sale logged successfully!")
            st.session_state.step = 1
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Save failed: {e}")

    if col2.button("Cancel", use_container_width=True):
        st.session_state.step = 1
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("BG Melon Sale Dashboard")

@st.cache_data(ttl=10)
def load_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    return pd.DataFrame(all_values[1:], columns=all_values[0])

df = load_data()

if not df.empty:
    # Convert columns for math
    df['Weight_kg'] = pd.to_numeric(df.iloc[:, 1], errors='coerce')
    df['Total_RM'] = pd.to_numeric(df.iloc[:, 3], errors='coerce')
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {df['Total_RM'].sum():,.0f}")
    c2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Recent Sales")
    st.dataframe(df.iloc[::-1], use_container_width=True) # Show newest first
else:
    st.info("No sales data found yet.")
