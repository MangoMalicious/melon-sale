import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz

# CONFIG
PRICE_PER_KG = 18.00
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- CSS FIX ---
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

# Auth
if 'ws' not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

@st.cache_data(ttl=10)
def load_recent_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    headers = all_values[0]
    recent_rows = all_values[-100:] if len(all_values) > 100 else all_values[1:]
    return pd.DataFrame(recent_rows, columns=headers)

@st.cache_data(ttl=10)
def get_totals():
    try:
        vals = ws.batch_get(['G1', 'G2'])
        rev = vals[0][0][0] if vals[0] and vals[0][0] else 0
        wgt = vals[1][0][0] if vals[1] and vals[1][0] else 0
        return float(rev), float(wgt)
    except:
        return 0.0, 0.0

# --- ACTIONS ---
def save_data():
    weight = st.session_state.weight_input
    if weight and weight > 0:
        now = datetime.now(MY_TZ)
        date_str = now.strftime("%Y-%m-%d")
        ws.append_row([date_str, weight, PRICE_PER_KG, round(weight * PRICE_PER_KG, 2)])
        st.toast(f"Saved {weight}kg")
        st.session_state.weight_input = None
        st.cache_data.clear()
    else:
        st.error("Invalid weight")

def delete_row():
    idx_to_del = st.session_state.get("row_to_delete")
    if idx_to_del is not None:
        try:
            # FIX: Convert the App ID (0, 1, 2) back to Sheet Row (2, 3, 4)
            # Logic: Sheet_Row = App_ID + 2
            sheet_row = int(idx_to_del) + 2
            ws.delete_rows(sheet_row)
            st.toast(f"ID {idx_to_del} removed")
            st.session_state.row_to_delete = None
            st.cache_data.clear()
        except Exception:
            st.error("Delete failed")

df = load_recent_data()
rev_total, wgt_total = get_totals()

# --- SIDEBAR ---
st.sidebar.header("Log New Sale")
st.sidebar.number_input("Weight (kg)", min_value=0.0, value=None, step=0.1, key="weight_input", on_change=save_data)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    # Starts at 0
    st.sidebar.number_input("Enter ID to Delete", min_value=0, step=1, value=None, key="row_to_delete", on_change=delete_row)

if st.sidebar.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN DASHBOARD ---
st.title("Family Melon Sale")

dashboard = st.empty()
with dashboard.container():
    if not df.empty:
        df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)
        df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
        
        display_rev = rev_total if rev_total > 0 else df["Total"].sum()
        display_wgt = wgt_total if wgt_total > 0 else df["Weight_kg"].sum()

        c1, c2 = st.columns(2)
        c1.metric("Total Revenue", f"RM {display_rev:,.2f}")
        c2.metric("Total Weight", f"{display_wgt:,.2f} kg")
        
        st.subheader("Sales History")
        
        df_display = df.copy()
        # FIX: Force index to start from 0
        df_display.index = range(len(df))
        
        # Show newest on top
        st.dataframe(df_display.iloc[::-1], use_container_width=True)
    else:
        st.info("No sales logged yet.")
