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

# --- CALLBACK FUNCTION: Captures data and clears the box ---
def handle_sale():
    weight_val = st.session_state.get("weight_input")
    
    if weight_val is not None and weight_val > 0:
        total_price = weight_val * PRICE_PER_KG
        sale_date = date.today()
        
        # Save to Google Sheets
        worksheet.append_row([str(sale_date), weight_val, PRICE_PER_KG, total_price])
        
        # This is the secret fix: Manually clearing the key in session state
        # so the app doesn't get stuck on the old number
        st.session_state["weight_input"] = None
        st.toast(f"Saved {weight_val}kg successfully")
    else:
        st.error("Please enter a valid weight before confirming")
        
# Load data for the dashboard
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")

# We keep clear_on_submit=False but handle the clearing manually in the callback
with st.sidebar.form("sale_form"):
    sale_date = st.date_input("Date", date.today())
    
    st.number_input(
        "Weight (kg)", 
        value=None, 
        placeholder="Type weight here...", 
        format="%.2f",
        key="weight_input"  # This links directly to the session_state clear above
    )
    
    st.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")
    
    # Confirm Sale button
    st.form_submit_button("Confirm Sale", on_click=handle_sale)

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
else:
    st.error("Header mismatch in Google Sheets. Ensure headers are: Date, Weight_kg, Price_per_kg, Total")
