import streamlit as st
import pandas as pd
import gspread
from datetime import date

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", page_icon="🍈")
st.title("🍈 Family Melon Sale Dashboard")

# --- THE ULTIMATE CSS FIX ---
st.markdown(
    """
    <style>
    /* 1. Target the specific label instruction text */
    [data-testid="stWidgetInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* 2. Target the specific "small" element within the number input */
    div[data-testid="stNumberInput"] small {
        display: none !important;
    }

    /* 3. A catch-all for any "Press Enter" text in forms */
    div[data-testid="stForm"] label + div + div {
        display: none !important;
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

# --- CALLBACK FUNCTION: This runs the moment 'Enter' or 'Confirm' is pressed ---
def handle_sale():
    # Grabs the value directly from the session state key
    weight_val = st.session_state.get("weight_input")
    
    if weight_val is not None and weight_val > 0:
        total_price = weight_val * PRICE_PER_KG
        sale_date = date.today()
        
        # Save to Google Sheets
        worksheet.append_row([str(sale_date), weight_val, PRICE_PER_KG, total_price])
        
        # We don't need a manual rerun here because the form will reset 
        # naturally after the callback finishes.
    else:
        st.toast("⚠️ Please enter a weight first!", icon="❌")

# Load data for the dashboard
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")

# clear_on_submit=True is now safe because the callback grabs data FIRST
with st.sidebar.form("sale_form", clear_on_submit=True):
    sale_date = st.date_input("Date", date.today())
    
    # We use the 'key' parameter to link this input to the callback
    st.number_input(
        "Weight (kg)", 
        value=None, 
        placeholder="Type weight here...", 
        format="%.2f",
        key="weight_input"
    )
    
    st.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")
    
    # on_click ensures the handle_sale function runs with the NEW typed data
    st.form_submit_button("Confirm Sale", on_click=handle_sale)

# --- DASHBOARD ---
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
else:
    st.error("Header mismatch in Google Sheets. Ensure headers are: Date, Weight_kg, Price_per_kg, Total")
