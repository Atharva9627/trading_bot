import os
import time
import hmac
import hashlib
import requests
import questionary
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE_URL = "https://testnet.binancefuture.com"

def get_binance_headers():
    return {"X-MBX-APIKEY": API_KEY}

def send_signed_request(method, endpoint, params_str=""):
    timestamp = int(time.time() * 1000)
    
    # Combine user parameters with mandatory timestamp
    if params_str:
        query_string = f"{params_str}&timestamp={timestamp}"
    else:
        query_string = f"timestamp={timestamp}"
        
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=get_binance_headers())
    return response.json()

def main():
    print("\n--- 🔍 Binance Futures Order History Lookup ---")
    
    # 1. Ask user for the asset symbol
    symbol = questionary.text(
        "Enter the trading pair symbol (e.g., BTCUSDT):",
        default="BTCUSDT"
    ).ask().strip().upper()
    
    if not symbol:
        print("❌ Symbol cannot be empty.")
        return

    print(f"\n📡 Fetching recent order history for {symbol} from Testnet...")
    
    # 2. Pull all historical entries for this symbol from the API
    try:
        history_params = f"symbol={symbol}&limit=10"
        orders = send_signed_request("GET", "/fapi/v1/allOrders", history_params)
        
        if isinstance(orders, dict) and "code" in orders:
            print(f"❌ Error from Binance: {orders.get('msg')}")
            return
            
        if not orders:
            print(f"🤷 No recent orders found for {symbol} on this account.")
            return
            
        # Reverse the list so your newest orders appear at the very top of the menu
        orders.reverse()
        
        # 3. Format choices for the interactive menu
        choices = []
        order_map = {}
        
        for order in orders:
            order_id = str(order.get('orderId'))
            side = order.get('side')
            order_type = order.get('type')
            qty = order.get('origQty')
            price = order.get('price') if float(order.get('price')) > 0 else "MARKET"
            status = order.get('status')
            
            # Simple clean display label for the console select list
            label = f"ID: {order_id} | {side} {qty} | Type: {order_type} | Target: {price} | [Last Status: {status}]"
            choices.append(label)
            order_map[label] = order_id

        # 4. Prompt user to select an order visually
        selected_label = questionary.select(
            "Select an order from your history to double-check its live fill status:",
            choices=choices
        ).ask()
        
        if not selected_label:
            return
            
        chosen_id = order_map[selected_label]
        
        # 5. Query the exact live status for the selected order ID
        print(f"\n🔄 Fetching absolute real-time status for Order #{chosen_id}...")
        single_params = f"symbol={symbol}&orderId={chosen_id}"
        live_data = send_signed_request("GET", "/fapi/v1/order", single_params)
        
        # 6. Beautifully print out the final verification metrics
        print("\n================ LIVE STATUS REPORT ================")
        print(f" 📦 Asset Symbol     : {live_data.get('symbol')}")
        print(f" 🆔 Order ID         : {live_data.get('orderId')}")
        print(f" 🚦 Execution Side   : {live_data.get('side')}")
        print(f" ⚡ Order Type       : {live_data.get('type')}")
        print(f" 🎯 Order Status     : {live_data.get('status')}")
        print(f" 📈 Original Qty     : {live_data.get('origQty')}")
        print(f" ✅ Executed Qty     : {live_data.get('executedQty')}")
        print(f" 💰 Avg Fill Price   : ${float(live_data.get('avgPrice', 0.0)):,.2f}")
        print("====================================================\n")
        
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()