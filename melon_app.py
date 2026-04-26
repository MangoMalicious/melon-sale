import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz
import io 

# CONFIG
PRICE_PER_KG = 18.00
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(
    page_title="BG Melon Sale", 
    layout="centered"
)

# --- THE ULTIMATE CSS FIX (Anti-Flicker) ---
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

# Auth with Persistence
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
    # Use the selected date from session state
    selected_date = st.session_state.date_input
    
    if weight and weight > 0:
        # Format the selected date to match your sheet preference
        date_str = selected_date.strftime("%d-%m-%Y") 
        ws.append_row([date_str, weight, PRICE_PER_KG, round(weight * PRICE_PER_KG, 2)])
        st.toast(f"Saved {weight}kg for {date_str}")
        st.session_state.weight_input = None
        st.cache_data.clear()
    else:
        st.error("Invalid weight")

def delete_row():
    idx_to_del = st.session_state.get("row_to_delete")
    if idx_to_del is not None:
        try:
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

# Date Picker (Defaults to current live date in Malaysia)
st.sidebar.date_input(
    "Sale Date", 
    value=datetime.now(MY_TZ), 
    key="date_input"
)

st.sidebar.number_input(
    "Weight (kg)", 
    min_value=0.0, 
    value=None, 
    step=0.1, 
    key="weight_input", 
    on_change=save_data
)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("Manage Data")
    st.sidebar.number_input("Enter ID to Delete", min_value=0, step=1, value=None, key="row_to_delete", on_change=delete_row)

    st.sidebar.markdown("---")
    st.sidebar.header("Reports")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales')
    
    current_date_str = datetime.now(MY_TZ).strftime('%d-%m-%Y')
    
    st.sidebar.download_button(
        label="Download Excel Report",
        data=buffer.getvalue(),
        file_name=f"bg_melon_sales_{current_date_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.sidebar.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN DASHBOARD ---
st.title("BG Melon Sale")

dashboard = st.empty()
with dashboard.container():
    if not df.empty:
        total_col = "Total(RM)" if "Total(RM)" in df.columns else "Total"
        weight_col = "Weight(kg)" if "Weight(kg)" in df.columns else "Weight_kg"
        
        df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
        df[weight_col] = pd.to_numeric(df[weight_col], errors='coerce').fillna(0)
        
        display_rev = rev_total if rev_total > 0 else df[total_col].sum()
        display_wgt = wgt_total if wgt_total > 0 else df[weight_col].sum()

        c1, c2 = st.columns(2)
        c1.metric("Total Revenue", f"RM {display_rev:,.2f}")
        c2.metric("Total Weight", f"{display_wgt:,.2f} kg")
        
        st.subheader("Sales History")
        
        df_display = df.copy()
        df_display.index = range(len(df))
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No sales logged yet.")
