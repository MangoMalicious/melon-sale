import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale")
st.title("Family Melon Sale Dashboard")

# --- THE ULTIMATE CSS FIX (Reinforced) ---
st.markdown(
    """
    <style>
    /* Hides the 'Press Enter' subtext container permanently */
    [data-testid="stWidgetInstructions"], 
    div[data-testid="stNumberInput"] > div:nth-child(3),
    section[data-testid="stSidebar"] small,
    div[data-testid="stNumberInput"] div[data-testid="caption"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        position: absolute !important;
    }

    /* Success message styling */
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
    msia_now = datetime.utcnow() + timedelta(hours=8)
    return msia_now.strftime("%Y-%m-%d")

# --- LOGIC FUNCTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight is not None and weight > 0:
        total_price = weight * PRICE_PER_KG
        date_str = get_malaysia_date()
        worksheet.append_row([date_str, weight, PRICE_PER_KG, total_price])
        st.session_state.weight_input = None
        st.session_state.last_saved = f"Saved {weight}kg successfully"
    else:
        st.error("Please enter a valid weight")

def delete_specific_row():
    row_to_delete = st.session_state.row_to_delete
    # Adding 1 because Google Sheets is 1-indexed and Row 1 is headers
    actual_row = row_to_delete + 1
    try:
        worksheet.delete_rows(actual_row)
        st.sidebar.success(f"Row {row_to_delete} deleted")
        st.rerun()
    except Exception as e:
        st.sidebar.error("Could not delete row")

# Load data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

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

st.sidebar.markdown("---")
st.sidebar.header("Manage Data")

# Specific Row Delete
if not df.empty:
    st.sidebar.number_input("Enter Row ID to Delete", min_value=1, max_value=len(df), step=1, key="row_to_delete")
    if st.sidebar.button("Remove Row"):
        delete_specific_row()

if st.sidebar.button("Refresh Dashboard"):
    st.rerun()

# --- DASHBOARD ---
if "last_saved" in st.session_state and st.session_state.last_saved:
    st.markdown(f'<div class="big-success">{st.session_state.last_saved}</div>', unsafe_allow_html=True)
    st.session_state.last_saved = ""

if not df.empty:
    col1, col2 = st.columns(2)
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce')
    df = df.fillna(0)
    
    col1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    col2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    
    # --- TABLE SORT FIX ---
    # 1. Flip data so latest is at the top
    df_display = df.iloc[::-1].copy()
    
    # 2. Assign Row IDs in descending order (e.g., 5, 4, 3, 2, 1)
    # This ensures Row 5 in the table is actually Row 5 in the Sheet
    df_display.index = range(len(df), 0, -1)
    
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("The sheet is currently empty. Start logging to see your stats")
