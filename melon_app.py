import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# CONFIG
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", layout="centered")

# --- THE AGGRESSIVE CSS FIX ---
st.markdown(
    """
    <style>
    /* Hides subtext and 'Press Enter' hints */
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

    /* REDUCES LOADING FLICKER: Stops the 'fade' effect on elements */
    .stApp [data-testid="stVerticalBlock"] > div {
        transition: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate (Moving this outside to prevent re-auth on every rerun)
if 'gc' not in st.session_state:
    credentials = dict(st.secrets["gcp_service_account"])
    st.session_state.gc = gspread.service_account_from_dict(credentials)
    st.session_state.sh = st.session_state.gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.worksheet = st.session_state.sh.get_worksheet(0)

worksheet = st.session_state.worksheet

# --- CACHED DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    return pd.DataFrame(worksheet.get_all_records())

# --- ACTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight and weight > 0:
        total_price = round(weight * PRICE_PER_KG, 2)
        date_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
        try:
            worksheet.append_row([date_str, weight, PRICE_PER_KG, total_price])
            st.toast(f"Saved {weight}kg successfully")
            st.session_state.weight_input = None
            st.cache_data.clear()
        except Exception:
            st.error("Sheet Connection Error")
    else:
        st.error("Enter valid weight")

def delete_row():
    row_to_del = st.session_state.get("row_to_delete")
    if row_to_del:
        try:
            worksheet.delete_rows(row_to_del + 1)
            st.toast(f"Row {row_to_del} removed")
            st.session_state.row_to_delete = None
            st.cache_data.clear()
        except Exception:
            st.error("Delete failed")

# Title stays outside the container so it never moves
st.title("Family Melon Sale Dashboard")

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.write(f"Date: **{(datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d')}**")

st.sidebar.number_input(
    "Weight (kg)", min_value=0.0, value=None, step=0.1, 
    placeholder="0.00", format="%.2f", key="weight_input", on_change=save_data
)

# Load data once per rerun
df = load_data()

st.sidebar.markdown("---")
if not df.empty:
    st.sidebar.header("Manage Data")
    st.sidebar.number_input("Row ID to Delete", min_value=1, max_value=len(df), step=1, value=None, key="row_to_delete", on_change=delete_row)
    st.sidebar.button("Remove Row", on_click=delete_row)
    
    st.sidebar.markdown("---")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Report", data=csv_data, file_name="melon_sales.csv", mime="text/csv")

if st.sidebar.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- THE STABLE DASHBOARD CONTAINER ---
# This is the "Anchor" that stops the entire dashboard from disappearing
main_placeholder = st.empty()

with main_placeholder.container():
    if not df.empty:
        # Pre-process numeric columns
        df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)
        df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
        
        # Metrics
        m1, m2 = st.columns(2)
        m1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
        m2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
        
        st.subheader("Sales History")
        df_display = df.iloc[::-1].copy()
        df_display.index = range(len(df), 0, -1)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No sales logged yet.")
