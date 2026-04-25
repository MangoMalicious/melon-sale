import streamlit as st
import pandas as pd
import gspread
from datetime import date

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", page_icon="🍈")
st.title("🍈 Family Melon Sale Dashboard")

# Authenticate with Google
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# Open the sheet
# IMPORTANT: Use the exact name of your Google Sheet file
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing") 
worksheet = sh.get_worksheet(0)

# Load data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")

with st.sidebar.form("sale_form", clear_on_submit=True):
    sale_date = st.date_input("Date", date.today())
    # We remove the step/min_value defaults that might be forcing the reset
    weight_input = st.number_input("Weight (kg)", format="%.2f")
    
    st.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")
    
    submitted = st.form_submit_button("Confirm Sale")
    
    if submitted:
        if weight_input > 0:
            total_price = weight_input * PRICE_PER_KG
            # Append row directly using the input variable
            worksheet.append_row([str(sale_date), weight_input, PRICE_PER_KG, total_price])
            st.sidebar.success(f"Saved {weight_input}kg!")
            # We use st.switch_page or just let the app naturally refresh 
            # instead of a forced rerun which can wipe the temp memory
        else:
            st.sidebar.warning("Please enter a weight greater than 0")

# --- DASHBOARD ---
# This ensures that if the sheet is empty, the app doesn't crash
if not df.empty and "Total" in df.columns:
    col1, col2 = st.columns(2)
    
    # Clean up data to make sure they are numbers
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce')
    
    # Fill any empty cells with 0 to prevent math errors
    df = df.fillna(0)
    
    col1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    col2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
elif df.empty:
    st.info("The sheet is currently empty. Start logging to see your stats!")
