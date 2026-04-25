import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale")
st.title("Family Melon Sale Dashboard")

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    [data-testid="stWidgetInstructions"], div[data-testid="stNumberInput"] small {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    .big-success {
        padding: 20px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate with Google
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing") 
worksheet = sh.get_worksheet(0)

# --- TIMEZONE LOGIC ---
def get_malaysia_date():
    # Streamlit Cloud is UTC. Malaysia is UTC+8.
    msia_now = datetime.utcnow() + timedelta(hours=8)
    return msia_now.strftime("%Y-%m-%d")

# --- LOGIC FUNCTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight is not None and weight > 0:
        total_price = weight * PRICE_PER_KG
        date_str = get_malaysia_date()
        
        # COLUMN ORDER: Date, Weight_kg, Price_per_kg, Total
        worksheet.append_row([date_str, weight, PRICE_PER_KG, total_price])
        
        st.session_state.weight_input = None
        st.session_state.last_saved = f"Saved {weight}kg successfully"
    else:
        st.error("Please enter a valid weight")

def undo_last_sale():
    records = worksheet.get_all_records()
    if len(records) > 0:
        # Headers are Row 1, last record is Row (Count + 1)
        last_row_index = len(records) + 1
        worksheet.delete_rows(last_row_index)
        st.sidebar.warning("Last sale deleted")
        st.rerun()
    else:
        st.sidebar.error("No sales found to delete")

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.write(f"Date (MY): **{get_malaysia_date()}**")

st.sidebar.number_input(
    "Weight (kg)", 
    value=None, 
    placeholder="Type weight here...", 
    format="%.2f",
    key="weight_input",
    on_change=save_data
)

st.sidebar.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")

if st.sidebar.button("Undo Last Sale"):
    undo_last_sale()

if st.sidebar.button("Refresh Dashboard"):
    st.rerun()

# --- DASHBOARD ---
if "last_saved" in st.session_state and st.session_state.last_saved:
    st.markdown(f'<div class="big-success">{st.session_state.last_saved}</div>', unsafe_allow_html=True)
    st.session_state.last_saved = ""

data = worksheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    col1, col2 = st.columns(2)
    # Force columns to numeric for calculation
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce')
    df = df.fillna(0)
    
    col1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    col2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
else:
    st.info("The sheet is currently empty. Start logging to see your stats")
