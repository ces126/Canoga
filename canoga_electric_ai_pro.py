import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Canoga AI Pro", layout="wide", initial_sidebar_state="expanded")
st.title("⚡ Canoga Electric Supply AI Pro")
st.caption("**The Ultimate Free Tool for LA Electricians** • Multi-Family Focus")

with st.sidebar:
    st.header("👷 Your Profile")
    name = st.text_input("Name / Company")
    email = st.text_input("Email")
    if st.button("Save Profile"):
        st.success("✅ Saved! Canoga will send you priority deals.")

# Inventory
inventory = pd.DataFrame({
    "Item": ["14/2 Romex 250ft", "12/2 Romex 250ft", "200A Panel", "LED Can Lights (6pk)", "GFCI Outlet"],
    "Price": [72, 105, 450, 85, 18],
    "Stock": ["In Stock", "Low Stock", "In Stock", "In Stock", "In Stock"]
})

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 Blueprint", "💰 Bid Calculator", "🛒 Reserve", "🔍 Code Tools", "🟢 LADBS Permits"])

with tab1:
    st.subheader("Blueprint Takeoff")
    st.info("Upload PDF or images — Grok Vision coming in next update.")

with tab2:
    st.subheader("Bid & Profit Calculator")
    labor = st.number_input("Labor Cost $", value=2450)
    materials = st.number_input("Material Cost $", value=1850)
    markup = st.slider("Markup %", 25, 60, 40)
    total = labor + materials
    price = total * (1 + markup/100)
    st.metric("Recommended Bid Price", f"${price:,.2f}", f"Profit: ${price - total:,.2f}")

with tab3:
    st.subheader("Reserve Materials")
    selected = st.multiselect("Select Items", inventory["Item"])
    job = st.text_input("Job Name")
    if st.button("Reserve for Pickup"):
        st.success(f"✅ Reservation for **{job}** confirmed! Ready at Canoga store.")

with tab4:
    st.subheader("Code Tools")
    st.info("Voltage Drop, Conduit Fill, Box Fill, NEC lookup — ready to expand.")

with tab5:
    st.subheader("LADBS Permits")
    st.info("Live permit tracker with ZIP filter and instant quotes coming next.")

st.sidebar.success("App is LIVE!")
st.sidebar.info("Share this link with electricians!")
