import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# YOUR FIXED PRICE
PRICE_PER_KG = 18.00

st.set_page_config(page_title="Family Melon Sale", page_icon="🍈")
st.title("🍈 Family Melon Sale Dashboard")

# 1. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Read the data
df = conn.read()

# --- SIDEBAR: Input ---
st.sidebar.header("Log New Sale")
with st.sidebar.form("sale_form", clear_on_submit=True):
    sale_date = st.date_input("Date", date.today())
    weight = st.number_input("Weight (kg)", min_value=0.1, step=0.1)
    
    total_price = weight * PRICE_PER_KG
    st.write(f"Price: **RM {PRICE_PER_KG:.2f}/kg**")
    st.info(f"**Total to Charge: RM {total_price:.2f}**")
    
    submitted = st.form_submit_button("Confirm Sale")
    
    if submitted:
        new_row = pd.DataFrame([{
            "Date": str(sale_date),
            "Weight_kg": weight,
            "Price_per_kg": PRICE_PER_KG,
            "Total": total_price
        }])
        # Combine and upload
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("Successfully saved to Cloud!")
        st.rerun()

# --- MAIN DASHBOARD ---
if not df.empty:
    col1, col2 = st.columns(2)
    col1.metric("Total Revenue", f"RM {df['Total'].sum():,.2f}")
    col2.metric("Total Weight", f"{df['Weight_kg'].sum():,.2f} kg")
    
    st.subheader("Sales History")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
else:
    st.info("No sales recorded yet.")