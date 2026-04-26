import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz

PRICE_PER_KG = 20.0
MY_TZ = pytz.timezone('Asia/Kuala_Lumpur')

st.set_page_config(page_title="BG Melon Sale", layout="centered")

# --- GOOGLE SHEETS ---
if "ws" not in st.session_state:
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url("YOUR_GOOGLE_SHEET_URL")
    st.session_state.ws = sh.get_worksheet(0)

ws = st.session_state.ws

# --- SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 1

if "weight" not in st.session_state:
    st.session_state.weight = 0.0

if "discount" not in st.session_state:
    st.session_state.discount = 0.0

# --- INPUT ---
st.sidebar.header("Log New Sale")

weight = st.sidebar.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
discount = st.sidebar.number_input("Discount (%)", min_value=0.0, max_value=100.0, step=1.0)

base_price = weight * PRICE_PER_KG
final_price = base_price * (1 - discount / 100)

# --- STEP 1: PREVIEW LOCK ---
if st.session_state.step == 1:
    if st.sidebar.button("Enter (Preview)"):
        if weight <= 0:
            st.error("Enter valid weight")
        else:
            st.session_state.weight = weight
            st.session_state.discount = discount
            st.session_state.base_price = base_price
            st.session_state.final_price = final_price
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: CONFIRM SAVE ---
elif st.session_state.step == 2:
    st.sidebar.write("Preview Locked")
    st.sidebar.write(f"Weight: {st.session_state.weight} kg")
    st.sidebar.write(f"Final: RM {st.session_state.final_price:.2f}")

    if st.sidebar.button("Enter (Save)"):
        try:
            date_str = datetime.now(MY_TZ).strftime("%d-%m-%Y")

            ws.append_row([
                date_str,
                st.session_state.weight,
                PRICE_PER_KG,
                st.session_state.final_price
            ])

            st.success("Sale saved")

            # reset flow
            st.session_state.step = 1
            st.rerun()

        except Exception as e:
            st.error(f"Save failed: {e}")

    if st.sidebar.button("Cancel"):
        st.session_state.step = 1
        st.rerun()
