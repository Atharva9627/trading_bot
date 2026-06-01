def validate_inputs(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string (e.g., 'BTCUSDT').")
    
    if side.upper() not in ["BUY", "SELL"]:
        raise ValueError("Side must be either 'BUY' or 'SELL'.")
        
    if order_type.upper() not in ["MARKET", "LIMIT"]:
        raise ValueError("Order Type must be either 'MARKET' or 'LIMIT'.")
        
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
        
    if order_type.upper() == "LIMIT" and (price is None or price <= 0):
        raise ValueError("Price must be greater than 0 for LIMIT orders.")