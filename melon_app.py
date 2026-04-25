import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# CONFIG
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", layout="centered")

# --- THE AGGRESSIVE ANTI-FLICKER CSS ---
st.markdown(
    """
    <style>
    /* 1. Hides all instructions */
    [data-testid="stWidgetInstructions"], 
    div[data-testid="stNumberInput"] > div:nth-child(3),
    section[data-testid="stSidebar"] small,
    div[data-testid="stNumberInput"] div[data-testid="caption"] {
        display: none !important;
    }

    /* 2. THE FLICKER KILLER: Forces opacity to stay at 1 during reruns */
    [data-testid="stVerticalBlock"] > div {
        opacity: 1 !important;
        transition: none !important;
    }
    
    /* 3. Removes the gray 'loading' overlay that causes the blink */
    [data-testid="stAppViewBlockContainer"] {
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate with Session State Persistence
if 'worksheet' not in st.session_state:
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.worksheet = sh.get_worksheet(0)

ws = st.session_state.worksheet

# --- CACHED DATA ---
@st.cache_data(ttl=60)
def load_data():
    return pd.DataFrame(ws.get_all_records())

# --- ACTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight and weight > 0:
        date_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
        ws.append_row([date_str, weight, PRICE_PER_KG, round(weight * PRICE_PER_KG, 2)])
        st.toast(f"Saved {weight}kg successfully")
        st.session_state.weight_input = None
        st.cache_data.clear()
    else:
        st.error("Invalid weight")

def delete_row():
    row_to_del = st.session_state.get("row_to_delete")
    if row_to_del:
        try:
            ws.delete_rows(row_to_del + 1)
            st.toast(f"Row {row_to_del} removed")
            st.session_state.row_to_delete = None
            st.cache_data.clear()
        except:
            st.error("Delete failed")

# Title
st.title("Family Melon Sale Dashboard")

# Load Data
df = load_data()

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.number_input("Weight (kg)", min_value=0.0, value=None, step=0.1, placeholder="0.00", format="%.2f", key="weight_input", on_change=save_data)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    st.sidebar.number_input("Row ID to Delete", min_value=1, max_value=len(df), step=1, value=None, key="row_to_delete", on_change=delete_row)
    st.sidebar.button("Remove Row", on_click=delete_row)
    
    st.sidebar.markdown("---")
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download CSV", data=csv, file_name="melon_sales.csv", mime="text/csv")

if st.sidebar.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- DATA PREP (Before drawing to prevent pop-in) ---
if not df.empty:
    df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
    rev = f"RM {df['Total'].sum():,.2f}"
    wgt = f"{df['Weight_kg'].sum():,.2f} kg"
    
    df_display = df.iloc[::-1].copy()
    df_display.index = range(len(df), 0, -1)

# --- DASHBOARD SLOT ---
dashboard = st.empty()

with dashboard.container():
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Revenue", rev)
        c2.metric("Total Weight", wgt)
        
        st.subheader("Sales History")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No sales logged yet.")
