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

@st.cache_data(ttl=10)
def load_recent_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    headers = all_values[0]
    recent_rows = all_values[-100:] if len(all_values) > 100 else all_values[1:]
    return pd.DataFrame(recent_rows, columns=headers)

@st.cache_data(ttl=10)
def get_totals():
    try:
        vals = ws.batch_get(['G1', 'G2'])
        rev = vals[0][0][0] if vals[0] and vals[0][0] else 0
        wgt = vals[1][0][0] if vals[1] and vals[1][0] else 0
        return float(rev), float(wgt)
    except:
        return 0.0, 0.0

# --- SAVE LOGIC ---
def trigger_save(w, p, d):
    if w > 0 and p > 0:
        date_str = d.strftime("%d-%m-%Y") 
        ws.append_row([date_str, w, PRICE_PER_KG, p])
        st.toast(f"Saved: {w}kg for RM {p}")
        st.cache_data.clear()
        st.session_state.v_num += 1
        st.rerun()

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

sale_date = st.sidebar.date_input("Sale Date", value=datetime.now(MY_TZ), key="date_input")

# 1. Weight Input
# Pressing Enter here calculates the price
weight_text = st.sidebar.text_input("Weight (kg)", value="", placeholder="Enter weight...", key=f"w_{v}")

try:
    weight = float(weight_text) if weight_text else 0.0
except ValueError:
    weight = 0.0

# 2. Price Calculation
calc_price = float(math.floor(weight * PRICE_PER_KG)) if weight > 0 else 0.0
price_placeholder = f"RM {calc_price:.0f}" if weight > 0 else "Enter price..."

# 3. Price Input (THE TRIGGER)
# We use the on_change callback so that pressing Enter here saves the sale
price_text = st.sidebar.text_input(
    "Final Price (RM)", 
    value="", 
    placeholder=price_placeholder, 
    key=f"p_{v}"
)

# Determine final price to save
try:
    if not price_text and weight > 0:
        final_price = calc_price
    else:
        final_price = float(price_text) if price_text else 0.0
except ValueError:
    final_price = 0.0

# Manual Save Button (as backup)
if st.sidebar.button("Save Sale") or (st.session_state.get(f"p_{v}") and weight > 0):
    # This logic checks if the price box was "Entered"
    trigger_save(weight, final_price, sale_date)

# --- DASHBOARD & REPORTS ---
df = load_recent_data()
rev_total, wgt_total = get_totals()

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    with st.sidebar.expander("Delete Entry"):
        row_to_del = st.sidebar.text_input("Enter ID", key="del_box")
        if st.sidebar.button("Confirm Delete"):
            try:
                ws.delete_rows(int(row_to_del) + 2)
                st.toast("Deleted")
                st.cache_data.clear()
                st.rerun()
            except:
                st.sidebar.error("Invalid ID")

    st.sidebar.markdown("---")
    st.sidebar.header("Reports")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales')
    st.sidebar.download_button("Download Excel", data=buffer.getvalue(), file_name="sales.xlsx")

st.title("BG Melon Sale")
if not df.empty:
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {rev_total:,.0f}")
    c2.metric("Total Weight", f"{wgt_total:,.2f} kg")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
