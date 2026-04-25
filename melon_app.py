import streamlit as st
import pandas as pd
import gspread
from datetime import date

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", page_icon="🍈")
st.title("🍈 Family Melon Sale Dashboard")

# Authenticate with Google
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# Open the sheet (Make sure the name matches exactly)
sh = gc.open("Melon Sales Data") 
worksheet = sh.get_worksheet(0)

# Load data for display
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
with st.sidebar.form("sale_form", clear_on_submit=True):
    sale_date = st.date_input("Date", date.today())
    weight = st.number_input("Weight (kg)", min_value=0.1, step=0.1)
    
    total_price = weight * PRICE_PER_KG
    st.info(f"**Total to Charge: RM {total_price:.2f}**")
    
    submitted = st.form_submit_button("Confirm Sale")
    
    if submitted:
        # Append to Google Sheet
        worksheet.append_row([str(sale_date), weight, PRICE_PER_KG, total_price])
        st.success("Saved to Cloud!")
        st.rerun()

# --- DASHBOARD ---
if not df.empty:
    col1, col2 = st.columns(2)
    col1.metric("Total Revenue", f"RM {pd.to_numeric(df['Total']).sum():,.2f}")
    col2.metric("Total Weight", f"{pd.to_numeric(df['Weight_kg']).sum():,.2f} kg")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
