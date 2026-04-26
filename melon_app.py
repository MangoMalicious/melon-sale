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

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")

# clear_on_submit=True ensures the boxes go blank after saving
with st.sidebar.form("sale_form", clear_on_submit=True):
    sale_date = st.date_input("Sale Date", value=datetime.now(MY_TZ))
    
    # Weight starts blank
    weight_text = st.text_input("Weight (kg)", value="", placeholder="Enter weight...")
    
    try:
        weight = float(weight_text) if weight_text else 0.0
    except ValueError:
        weight = 0.0
    
    # Auto-calculate suggested price
    calc_price = float(math.floor(weight * PRICE_PER_KG)) if weight > 0 else 0.0
    
    # Price also starts blank. If user leaves it blank, we use calc_price.
    price_placeholder = f"Calculated: RM {calc_price:.0f}" if weight > 0 else "Enter price..."
    price_text = st.text_input("Final Price (RM)", value="", placeholder=price_placeholder)
    
    try:
        if not price_text and weight > 0:
            final_price = calc_price
        else:
            final_price = float(price_text) if price_text else 0.0
    except ValueError:
        final_price = 0.0
    
    submitted = st.form_submit_button("Save Sale")
    
    if submitted:
        if weight > 0 and final_price > 0:
            date_str = sale_date.strftime("%d-%m-%Y") 
            ws.append_row([date_str, weight, PRICE_PER_KG, final_price])
            st.toast(f"Saved: {weight}kg for RM {final_price}")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Please enter weight and price")

# --- MANAGE & REPORTS ---
df = load_recent_data()
rev_total, wgt_total = get_totals()

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    with st.sidebar.expander("Delete Entry"):
        row_to_del = st.text_input("Enter ID to Delete", value="")
        if st.button("Confirm Delete"):
            try:
                ws.delete_rows(int(row_to_del) + 2)
                st.toast("Deleted")
                st.cache_data.clear()
                st.rerun()
            except:
                st.error("Invalid ID")

    st.sidebar.markdown("---")
    st.sidebar.header("Reports")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales')
    
    st.sidebar.download_button(
        label="Download Excel Report",
        data=buffer.getvalue(),
        file_name=f"bg_melon_sales.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- MAIN DASHBOARD ---
st.title("BG Melon Sale")

if not df.empty:
    total_col = "Total(RM)" if "Total(RM)" in df.columns else "Total"
    weight_col = "Weight(kg)" if "Weight(kg)" in df.columns else "Weight_kg"
    
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
    df[weight_col] = pd.to_numeric(df[weight_col], errors='coerce').fillna(0)
    
    display_rev = rev_total if rev_total > 0 else df[total_col].sum()
    display_wgt = wgt_total if wgt_total > 0 else df[weight_col].sum()

    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {display_rev:,.0f}")
    c2.metric("Total Weight", f"{display_wgt:,.2f} kg")
    
    st.subheader("Sales History")
    df_display = df.copy()
    df_display.index = range(len(df))
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("No sales logged yet.")
