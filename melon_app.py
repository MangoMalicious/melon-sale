import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# CONFIG
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale")
st.title("Family Melon Sale Dashboard")

# --- CSS FIX ---
st.markdown(
    """
    <style>
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
    .big-success {
        padding: 20px; background-color: #d4edda; color: #155724;
        border-radius: 10px; text-align: center; font-weight: bold;
        font-size: 24px; margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing") 
worksheet = sh.get_worksheet(0)

# --- ACTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight and weight > 0:
        date_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
        worksheet.append_row([date_str, weight, PRICE_PER_KG, weight * PRICE_PER_KG])
        st.session_state.weight_input = None
        st.session_state.last_saved = f"Saved {weight}kg successfully"
    else:
        st.error("Enter a valid weight")

def delete_row():
    row_to_del = st.session_state.get("row_to_delete")
    if row_to_del:
        try:
            # +1 because Sheet headers are row 1
            worksheet.delete_rows(row_to_del + 1)
            # Store success message in state to survive the rerun
            st.session_state.last_deleted = f"Row {row_to_del} removed successfully"
        except Exception:
            st.session_state.delete_error = "Delete failed"

# Load data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.write(f"Date: **{(datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d')}**")

st.sidebar.number_input(
    "Weight (kg)", value=None, placeholder="Type weight here...", 
    format="%.2f", key="weight_input", on_change=save_data
)

st.sidebar.markdown("---")
if not df.empty:
    st.sidebar.header("Manage Data")
    
    # Adding on_change here allows pressing ENTER to delete
    st.sidebar.number_input(
        "Row ID to Delete", 
        min_value=1, 
        max_value=len(df), 
        step=1, 
        value=None,
        placeholder="Enter ID...",
        key="row_to_delete",
        on_change=delete_row
    )
    st.sidebar.button("Remove Row", on_click=delete_row)

    # Show delete status in sidebar
    if st.session_state.get("last_deleted"):
        st.sidebar.success(st.session_state.last_deleted)
        st.session_state.last_deleted = ""
    if st.session_state.get("delete_error"):
        st.sidebar.error(st.session_state.delete_error)
        st.session_state.delete_error = ""

st.sidebar.button("Refresh Dashboard")

# --- MAIN DASHBOARD ---
if st.session_state.get("last_saved"):
    st.markdown(f'<div class="big-success">{st.session_state.last_saved}</div>', unsafe_allow_html=True)
    st.session_state.last_saved = ""

if not df.empty:
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
    
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    c2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    
    # SORT BY LATEST: Reverse data and assign IDs in descending order
    df_display = df.iloc[::-1].copy()
    df_display.index = range(len(df), 0, -1)
    
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("No sales logged yet.")
