import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz

# CONFIG
PRICE_PER_KG = 20.0
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- GOOGLE SHEETS AUTH ---
if "ws" not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("YOUR_GOOGLE_SHEET_URL")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

# --- INPUT FORM ---
st.sidebar.header("Log New Sale")

with st.sidebar.form("sale_form", clear_on_submit=True):

    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
    discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, step=1.0)

    # --- CALCULATION ---
    base_price = weight * PRICE_PER_KG
    final_price = base_price * (1 - discount / 100)

    # --- PREVIEW ---
    if weight > 0:
        st.write("Price Preview")
        st.write(f"Base price: RM {base_price:.2f}")
        st.write(f"Discount: {discount:.0f}%")
        st.write(f"Final total: RM {final_price:.2f}")
    else:
        st.write("Total: RM 0.00")

    submitted = st.form_submit_button("Confirm & Save")

    if submitted:
        if weight <= 0:
            st.error("Weight must be greater than 0")
        else:
            try:
                date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y")

                # MATCHING YOUR SHEET FORMAT EXACTLY:
                # Date | Weight(kg) | Price(per_kg) | Total(RM)
                ws.append_row([
                    date_str,
                    weight,
                    PRICE_PER_KG,
                    final_price
                ])

                st.success(f"Saved: {weight}kg | RM {final_price:.2f}")
                st.cache_data.clear()

            except Exception as e:
                st.error(f"Save failed: {e}")

st.sidebar.markdown("---")

# --- LOAD DATA ---
@st.cache_data(ttl=10)
def load_data():
    data = ws.get_all_values()

    if len(data) <= 1:
        return pd.DataFrame()

    headers = data[0]
    rows = data[1:]

    return pd.DataFrame(rows, columns=headers)

df = load_data()

# --- DASHBOARD ---
st.title("BG Melon Sale")

if not df.empty:
    df["Total(RM)"] = pd.to_numeric(df["Total(RM)"], errors="coerce")
    df["Weight(kg)"] = pd.to_numeric(df["Weight(kg)"], errors="coerce")

    total_revenue = df["Total(RM)"].sum()
    total_weight = df["Weight(kg)"].sum()

    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"RM {total_revenue:,.2f}")
    c2.metric("Total Weight", f"{total_weight:,.2f} kg")

    st.subheader("Recent Sales")
    st.dataframe(df, use_container_width=True)

else:
    st.info("No sales data yet")
