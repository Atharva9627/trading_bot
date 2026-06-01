import os
import time
import hmac
import hashlib
import math
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE_URL = "https://testnet.binancefuture.com"

# Local cache for exchange symbol rules (avoids hammering exchangeInfo endpoint unnecessarily)
EXCHANGE_INFO_CACHE = {}

def fetch_exchange_rules(symbol):
    """
    Fetches LOT_SIZE and PRICE_FILTER constraints for a symbol from Binance Testnet.
    Saves metadata to EXCHANGE_INFO_CACHE to optimize performance.
    """
    global EXCHANGE_INFO_CACHE
    symbol = symbol.upper()
    
    if symbol in EXCHANGE_INFO_CACHE:
        return EXCHANGE_INFO_CACHE[symbol]
        
    try:
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        response = requests.get(url)
        data = response.json()
        
        symbols_list = data.get("symbols", [])
        for sym_data in symbols_list:
            s_name = sym_data.get("symbol")
            filters = sym_data.get("filters", [])
            
            # Extract filters matching lot limits and price increments
            lot_filter = next((f for f in filters if f.get("filterType") == "LOT_SIZE"), {})
            price_filter = next((f for f in filters if f.get("filterType") == "PRICE_FILTER"), {})
            
            EXCHANGE_INFO_CACHE[s_name] = {
                "stepSize": float(lot_filter.get("stepSize", 0.00000001)),
                "minQty": float(lot_filter.get("minQty", 0.001)),
                "maxQty": float(lot_filter.get("maxQty", 9999999.0)),
                "tickSize": float(price_filter.get("tickSize", 0.01)),
                "minPrice": float(price_filter.get("minPrice", 0.01)),
                "maxPrice": float(price_filter.get("maxPrice", 9999999.0)),
                "quantityPrecision": int(sym_data.get("quantityPrecision", 3)),
                "pricePrecision": int(sym_data.get("pricePrecision", 2))
            }
            
        return EXCHANGE_INFO_CACHE.get(symbol, None)
    except Exception as e:
        print(f"Error fetching exchange filters: {e}")
        return None

def format_value_to_step(value, step):
    """
    Formats and rounds down a float/string value to match the exact 
    allowable increment (stepSize or tickSize) to prevent Binance rejection errors.
    """
    if not value:
        return ""
    try:
        value = float(value)
        step = float(step)
        if step == 0:
            return str(value)
        
        # Calculate trailing decimal places from the step size representation
        step_str = f"{step:.10f}".rstrip('0')
        if '.' in step_str:
            decimals = len(step_str.split('.')[1])
        else:
            decimals = 0
            
        # Floor value to the nearest step size to avoid exceeding constraints
        rounded_val = math.floor(value / step) * step
        return f"{rounded_val:.{decimals}f}"
    except Exception:
        return str(value)

def send_signed_request(method, endpoint, params_str=""):
    timestamp = int(time.time() * 1000)
    query_string = f"{params_str}&timestamp={timestamp}" if params_str else f"timestamp={timestamp}"
    
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}
    
    if method.upper() == "POST":
        return requests.post(url, headers=headers).json()
    elif method.upper() == "DELETE":
        return requests.delete(url, headers=headers).json()
    return requests.get(url, headers=headers).json()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/symbol_rules', methods=['GET'])
def get_symbol_rules():
    """
    API endpoint exposing specific symbol rules (precision limits) AND calculating
    the dynamic safe maximum affordable size based on leverage, live price, and margin.
    """
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    rules = fetch_exchange_rules(symbol)
    
    if not rules:
        return jsonify({"error": "Symbol rules not found"}), 404
        
    try:
        # 1. Fetch current live ticker price
        price_url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
        price_res = requests.get(price_url).json()
        current_price = float(price_res.get("price", 1.0))
        
        # 2. Fetch user's available USDT margin balance
        balance_res = send_signed_request("GET", "/fapi/v2/balance")
        available_balance = 0.0
        if isinstance(balance_res, list):
            usdt_data = next((item for item in balance_res if item.get('asset') == 'USDT'), None)
            if usdt_data:
                available_balance = float(usdt_data.get('balance', 0.0))
                
        # 3. Fetch current account leverage for this symbol (default to 20x if not found)
        leverage = 20
        position_res = send_signed_request("GET", "/fapi/v2/positionRisk")
        if isinstance(position_res, list):
            sym_position = next((item for item in position_res if item.get('symbol') == symbol), None)
            if sym_position:
                leverage = int(sym_position.get('leverage', 20))
                
        # 4. Compute absolute safe maximum trade quantity: (Balance * Leverage) / Price
        # Apply a conservative 5% buffer (0.95 multiplier) to ensure no rejection for fees/slippage
        max_affordable = (available_balance * leverage * 0.95) / current_price
        
        # Format/Round max affordable to the symbol's exact allowable step size
        formatted_max_affordable = float(format_value_to_step(max_affordable, rules['stepSize']))
        
        # Ensure it does not exceed the exchange's absolute maximum contract limit
        final_max_qty = min(rules['maxQty'], formatted_max_affordable)
        # Ensure we don't return negative values if balance is low
        final_max_qty = max(rules['minQty'], final_max_qty)

        rules_extended = {
            **rules, 
            "currentPrice": current_price, 
            "maxSafeQty": final_max_qty,
            "availableUSDT": available_balance,
            "currentLeverage": leverage
        }
        return jsonify(rules_extended)
        
    except Exception as e:
        print(f"Error computing dynamic limits: {e}")
        return jsonify({**rules, "currentPrice": 0.0, "maxSafeQty": rules['maxQty']})

@app.route('/api/balance', methods=['GET'])
def get_balance():
    result = send_signed_request("GET", "/fapi/v2/balance")
    if isinstance(result, list):
        usdt_balance = next((item for item in result if item.get('asset') == 'USDT'), None)
        if usdt_balance:
            return jsonify(usdt_balance)
    return jsonify(result)

@app.route('/api/positions', methods=['GET'])
def get_positions():
    raw_positions = send_signed_request("GET", "/fapi/v2/positionRisk")
    if isinstance(raw_positions, list):
        active = [p for p in raw_positions if float(p.get('positionAmt', 0.0)) != 0.0]
        return jsonify(active)
    return jsonify(raw_positions)

@app.route('/api/open_orders', methods=['GET'])
def get_open_orders():
    symbol = request.args.get('symbol', '').upper()
    params = f"symbol={symbol}" if symbol else ""
    result = send_signed_request("GET", "/fapi/v1/openOrders", params)
    return jsonify(result)

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    symbol = data.get('symbol', 'BTCUSDT').upper()
    side = data.get('side', 'BUY')
    order_type = data.get('type', 'MARKET')
    raw_quantity = data.get('quantity', '0.001')
    raw_price = data.get('price', '')

    rules = fetch_exchange_rules(symbol)
    
    if rules:
        step_size = rules['stepSize']
        min_qty = rules['minQty']
        
        sanitized_qty = format_value_to_step(raw_quantity, step_size)
        
        if float(sanitized_qty) < min_qty:
            return jsonify({
                "code": -4005, 
                "msg": f"Quantity {raw_quantity} was formatted to {sanitized_qty}, which is below Minimum allowed ({min_qty})."
            })
            
        if order_type == "LIMIT":
            tick_size = rules['tickSize']
            sanitized_price = format_value_to_step(raw_price, tick_size)
        else:
            sanitized_price = ""
    else:
        sanitized_qty = raw_quantity
        sanitized_price = raw_price

    order_params = f"symbol={symbol}&side={side}&type={order_type}&quantity={sanitized_qty}"
    if order_type == "LIMIT":
        order_params += f"&price={sanitized_price}&timeInForce=GTC"

    result = send_signed_request("POST", "/fapi/v1/order", order_params)
    return jsonify(result)

@app.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    data = request.json
    symbol = data.get('symbol', '').upper()
    order_id = data.get('orderId', '')
    
    if not symbol or not order_id:
        return jsonify({"code": -1, "msg": "Missing Symbol or Order ID parameters"}), 400
        
    params = f"symbol={symbol}&orderId={order_id}"
    result = send_signed_request("DELETE", "/fapi/v1/order", params)
    return jsonify(result)

@app.route('/api/history', methods=['GET'])
def get_history():
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    history_params = f"symbol={symbol}&limit=10"
    result = send_signed_request("GET", "/fapi/v1/allOrders", history_params)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)