import streamlit as st
import pandas as pd
import gspread
from datetime import date

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale")
st.title("Family Melon Sale Dashboard")

# --- THE ULTIMATE CSS FIX ---
st.markdown(
    """
    <style>
    /* Hides instruction text */
    [data-testid="stWidgetInstructions"], div[data-testid="stNumberInput"] small {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate with Google
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# Open the sheet
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing") 
worksheet = sh.get_worksheet(0)

# --- LOGIC: Runs when input changes ---
def save_data():
    weight = st.session_state.weight_input
    # Get the date from its own session state key
    log_date = st.session_state.date_input
    
    if weight is not None and weight > 0:
        total_price = weight * PRICE_PER_KG
        
        # Save to Google Sheets
        worksheet.append_row([str(log_date), weight, PRICE_PER_KG, total_price])
        
        # Reset the weight input box immediately
        st.session_state.weight_input = None
        st.toast(f"Saved {weight}kg successfully for {log_date}")
    else:
        st.error("Please enter a valid weight")

# Load data for dashboard
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR: Non-Form Version ---
st.sidebar.header("Log New Sale")

# Date input added back here
st.sidebar.date_input("Date", date.today(), key="date_input")

# Weight input with Enter-key trigger
st.sidebar.number_input(
    "Weight (kg)", 
    value=None, 
    placeholder="Type weight here...", 
    format="%.2f",
    key="weight_input",
    on_change=save_data
)

st.sidebar.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")

if st.sidebar.button("Refresh Dashboard"):
    st.rerun()

# --- DASHBOARD ---
if not df.empty and "Total" in df.columns:
    col1, col2 = st.columns(2)
    
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce')
    df = df.fillna(0)
    
    col1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    col2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
elif df.empty:
    st.info("The sheet is currently empty. Start logging to see your stats")
