import os
import streamlit as st
from dotenv import load_dotenv
from bot.client import BinanceFuturesClient
from bot.validators import validate_inputs

load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = BinanceFuturesClient(api_key=API_KEY, api_secret=API_SECRET)

st.set_page_config(page_title="Binance Testnet Bot", page_icon="🤖")
st.title("🤖 Binance Futures Trading Dashboard")
st.markdown("---")

with st.form(key="order_form"):
    st.markdown("### 📊 Order Parameter Specifications")
    symbol = st.text_input("Asset Token Pair Symbol", value="BTCUSDT").upper()
    side = st.selectbox("Execution Intent Side", options=["BUY", "SELL"])
    order_type = st.selectbox("Order Structure Type", options=["MARKET", "LIMIT"])
    quantity = st.number_input("Order Allocation Quantity", min_value=0.0, step=0.001, format="%.3f")
    
    price = None
    if order_type == "LIMIT":
        price = st.number_input("Limit Execution Target Price", min_value=0.0, step=0.1)

    submit_button = st.form_submit_button(label="⚡ Transmit Order to Exchange")

if submit_button:
    try:
        validate_inputs(symbol, side, order_type, quantity, price if order_type == "LIMIT" else None)
        st.info("🔄 Initiating network pipeline connection...")
        result = client.place_order(symbol=symbol, side=side, order_type=order_type, quantity=quantity, price=price if order_type == "LIMIT" else None)
        
        if result["success"]:
            st.success("🎉 Transaction Completed Successfully!")
            st.json(result["data"])
        else:
            st.error(f"❌ Order Rejected: {result['error']}")
    except ValueError as val_err:
        st.warning(f"⚠️ Validation Error: {str(val_err)}")