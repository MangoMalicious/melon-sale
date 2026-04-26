import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz
import io 
import math 

# CONFIG
PRICE_PER_KG = 20.00
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- INITIALIZE STATE ---
if "v_num" not in st.session_state:
    st.session_state.v_num = 0

# Auth
if 'ws' not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1g2zv0E68IMtvDTmaqkOhr1QdGhGUTitBzfoLjnTmiX0/edit?usp=sharing")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

# --- SAVE CALLBACK ---
def quick_save():
    v = st.session_state.v_num
    w_text = st.session_state.get(f"w_{v}", "")
    p_text = st.session_state.get(f"p_{v}", "")
    
    try:
        w_val = float(w_text) if w_text else 0.0
        std_p = float(math.floor(w_val * PRICE_PER_KG))
        p_val = float(p_text) if p_text else std_p

        if w_val > 0:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y") 
            ws.append_row([date_str, w_val, PRICE_PER_KG, p_val])
            st.cache_data.clear()
            st.session_state.v_num += 1 
    except:
        pass

# --- SIDEBAR LOG SALE ---
st.sidebar.header("Log New Sale")
v = st.session_state.v_num

# 1. Manual Price (Optional)
# If you type here, it updates the "preview" in the weight box placeholder
manual_p = st.sidebar.text_input("Discount Price (Optional)", value="", placeholder="Final RM...", key=f"p_{v}")

# 2. Weight Input (THE MAIN BOX)
# We get the value from the session state to show the preview in the label
current_w = st.session_state.get(f"w_{v}", "")
try:
    w_float = float(current_w) if current_w else 0.0
    calc_p = float(math.floor(w_float * PRICE_PER_KG))
    # If there's a weight, we show the price in the dropdown label
    label_msg = f"Weight (kg) — [Total: RM {calc_p:.0f}]" if w_float > 0 else "Weight (kg)"
except:
    label_msg = "Weight (kg)"

# Typing and hitting ENTER here updates the label (Preview)
# Hitting ENTER again (without changing the number) triggers the save
weight_text = st.sidebar.text_input(
    label_msg, 
    value="", 
    placeholder="Type weight & hit Enter", 
    key=f"w_{v}",
    on_change=quick_save
)

# 3. EXPANDER (The Dropdown heads-up)
if weight_text:
    with st.sidebar.expander("📊 Calculation Details", expanded=True):
        try:
            w_val = float(weight_text)
            std_p = float(math.floor(w_val * PRICE_PER_KG))
            if manual_p:
                st.write(f"Original: ~~RM {std_p:.0f}~~")
                st.write(f"Final: **RM {float(manual_p):.0f}**")
            else:
                st.write(f"Total: **RM {std_p:.0f}**")
            st.info("Hit Enter again in the box to Save")
        except:
            st.error("Invalid number")

st.sidebar.markdown("---")

# --- DASHBOARD ---
@st.cache_data(ttl=10)
def load_recent_data():
    all_values = ws.get_all_values()
    if len(all_values) <= 1: return pd.DataFrame()
    headers = all_values[0]
    recent_rows = all_values[-100:] if len(all_values) > 100 else all_values[1:]
    return pd.DataFrame(recent_rows, columns=headers)

df = load_recent_data()

st.title("BG Melon Sale")
if not df.empty:
    rev = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
    wgt = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {rev:,.0f}")
    c2.metric("Total Weight", f"{wgt:,.2f} kg")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No sales logged yet.")
