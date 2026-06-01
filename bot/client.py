import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from bot.logging_config import logger

class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://testnet.binancefuture.com"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.headers = {"X-MBX-APIKEY": self.api_key}

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None):
        endpoint = "/fapi/v1/order"
        url = f"{self.base_url}{endpoint}"
        
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        
        if order_type.upper() == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        payload = f"{query_string}&signature={signature}"

        logger.info(f"Sending Order Request -> {side} {quantity} {symbol} ({order_type})")
        
        try:
            response = requests.post(url, data=payload, headers=self.headers, timeout=10)
            response_json = response.json()
            
            if response.status_code == 200:
                logger.info(f"Order Successful! OrderID: {response_json.get('orderId')}")
                return {
                    "success": True,
                    "data": {
                        "orderId": response_json.get("orderId"),
                        "status": response_json.get("status"),
                        "executedQty": response_json.get("executedQty"),
                        "avgPrice": response_json.get("avgPrice", "N/A")
                    }
                }
            else:
                error_code = response_json.get("code")
                error_msg = response_json.get("msg", "Unknown Error")
                logger.error(f"Binance API Refused Order [Code {error_code}]: {error_msg}")
                return {"success": False, "error": f"[{error_code}] {error_msg}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error encountered: {str(e)}")
            return {"success": False, "error": f"Network Failure: {str(e)}"}