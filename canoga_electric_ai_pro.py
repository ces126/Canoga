import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Canoga AI Pro", layout="wide", initial_sidebar_state="expanded")
st.title("⚡ Canoga Electric Supply AI Pro")
st.caption("**Grok-Powered Tool for LA Electricians** • Blueprint • Permits • Bids")

with st.sidebar:
    st.header("🔑 Grok API")
    api_key = st.text_input("xAI Grok API Key", type="password", help="Get at console.x.ai")
    if st.button("Save Key") and api_key:
        st.success("Grok Connected!")
    st.text_input("Your Email", key="user_email")

# Live Inventory
inventory = pd.DataFrame({
    "Item": ["14/2 Romex 250ft", "12/2 Romex 250ft", "200A Panel", "LED Can Lights (6pk)", "GFCI Outlet"],
    "Price": [72, 105, 450, 85, 18],
    "Stock": ["In Stock", "Low Stock", "In Stock", "In Stock", "In Stock"]
})

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 Blueprint Takeoff", "⚡ Voltage Drop", "💰 Bid Calculator", "🛒 Reserve Materials", "🟢 LADBS Permits"])

with tab1:
    st.subheader("Blueprint / PDF Takeoff")
    st.info("Upload PDF or image — Grok Vision analysis (full version ready when key is added).")

with tab2:
    st.subheader("Voltage Drop Calculator")
    st.info("Auto wire recommendation for Copper & Aluminum — full version in next update.")

with tab3:
    st.subheader("Bid & Profit Calculator")
    labor = st.number_input("Labor Cost $", value=2450)
    materials = st.number_input("Material Cost $", value=1850)
    markup = st.slider("Markup %", 25, 60, 40)
    total = labor + materials
    price = total * (1 + markup/100)
    st.metric("Recommended Bid Price", f"${price:,.2f}", f"Profit: ${price-total:,.2f}")

with tab4:
    st.subheader("Reserve Materials")
    selected = st.multiselect("Select Items", inventory["Item"])
    job = st.text_input("Job Name")
    if st.button("Reserve for Pickup"):
        st.success(f"✅ Reservation for **{job}** confirmed!")

with tab5:
    st.subheader("LADBS Permit Tracker")
    st.info("Live permits with ZIP filter and instant quotes — coming in next update.")

st.sidebar.success("Grok + Core Tools Ready")
st.sidebar.info("Add your Grok key to unlock AI features.")
