import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz # Standard for timezone handling

# CONFIG
PRICE_PER_KG = 18.00
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="Family Melon Sale", layout="centered")

# --- THE AGGRESSIVE ANTI-FLICKER CSS ---
st.markdown(
    """
    <style>
    [data-testid="stWidgetInstructions"], 
    div[data-testid="stNumberInput"] > div:nth-child(3),
    section[data-testid="stSidebar"] small,
    div[data-testid="stNumberInput"] div[data-testid="caption"] {
        display: none !important;
    }
    [data-testid="stVerticalBlock"] > div { opacity: 1 !important; transition: none !important; }
    [data-testid="stAppViewBlockContainer"] { opacity: 1 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Authenticate
if 'ws' not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.ws = sh.get_worksheet(0)
    # We'll use this to fetch totals without downloading the whole sheet
    st.session_state.sh = sh 

ws = st.session_state.ws

# --- OPTIMIZED DATA LOADING ---
@st.cache_data(ttl=60)
def load_recent_data():
    # Fix 1: Only fetch the last 100 rows to keep the app fast on 4G/5G
    all_values = ws.get_all_values()
    headers = all_values[0]
    # Get last 100 rows + headers
    recent_rows = [headers] + all_values[-100:] if len(all_values) > 100 else all_values
    df = pd.DataFrame(recent_rows[1:], columns=recent_rows[0])
    return df

@st.cache_data(ttl=60)
def get_totals():
    # Fix 1 cont.: Fetching totals from specific cells in the sheet 
    # (Assuming you put =SUM(D:D) in cell G1 and =SUM(B:B) in cell G2)
    # This prevents downloading 10,000 rows just to get a sum.
    vals = ws.batch_get(['G1', 'G2']) 
    revenue = vals[0][0][0] if vals[0] else "0.00"
    weight = vals[1][0][0] if vals[1] else "0.00"
    return revenue, weight

# --- ACTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight and weight > 0:
        # Fix 3: Proper Timezone Handling
        now = datetime.now(MY_TZ)
        date_str = now.strftime("%Y-%m-%d")
        
        # Fix 2: Using actual Row ID (based on total length) to avoid mismatch
        # For a truly unique ID, you could use: str(int(now.timestamp()))
        ws.append_row([date_str, weight, PRICE_PER_KG, round(weight * PRICE_PER_KG, 2)])
        
        st.toast(f"Saved {weight}kg")
        st.session_state.weight_input = None
        st.cache_data.clear()
    else:
        st.error("Invalid weight")

def delete_row():
    row_to_del = st.session_state.get("row_to_delete")
    if row_to_del:
        try:
            # Fix 2: Safety check - ensure row exists
            ws.delete_rows(row_to_del + 1)
            st.toast(f"Row {row_to_del} removed")
            st.session_state.row_to_delete = None
            st.cache_data.clear()
        except:
            st.error("Delete failed")

# Load Data
df = load_recent_data()
rev_total, wgt_total = get_totals()

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.number_input("Weight (kg)", min_value=0.0, value=None, step=0.1, key="weight_input", on_change=save_data)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    # Using the last row number as the max value to keep it synced
    st.sidebar.number_input("Sheet Row ID", min_value=1, step=1, value=None, key="row_to_delete", on_change=delete_row)

if st.sidebar.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN DASHBOARD ---
st.title("Family Melon Sale")

dashboard = st.empty()
with dashboard.container():
    if not df.empty:
        c1, c2 = st.columns(2)
        # Using the lightweight totals fetched from specific cells
        c1.metric("Total Revenue", f"RM {float(rev_total):,.2f}")
        c2.metric("Total Weight", f"{float(wgt_total):,.2f} kg")
        
        st.subheader("Recent Sales (Last 100)")
        df_display = df.iloc[::-1].copy()
        # We display the actual Sheet Row Number so parents know exactly what to delete
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No sales logged yet.")
