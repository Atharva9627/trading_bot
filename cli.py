import os
import sys
import questionary
from dotenv import load_dotenv
from bot.client import BinanceFuturesClient
from bot.validators import validate_inputs
from bot.logging_config import logger

load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

def run_interactive_cli():
    print("=" * 50)
    print("   Binance Futures Testnet Trading Engine   ")
    print("=" * 50)

    if not API_KEY or not API_SECRET:
        logger.error("API configuration error. Missing credentials in environment.")
        print("\n[!] Error: Please configure your keys in a .env file.\n")
        sys.exit(1)

    client = BinanceFuturesClient(api_key=API_KEY, api_secret=API_SECRET)

    symbol = questionary.text("Enter Token Pair Asset Symbol (e.g., BTCUSDT):", default="BTCUSDT").ask()
    side = questionary.select("Select Order Intent Action:", choices=["BUY", "SELL"]).ask()
    order_type = questionary.select("Select Order Structure Type:", choices=["MARKET", "LIMIT"]).ask()
    quantity = questionary.text("Specify Order Allocation Quantity:", default="0.001").ask()

    price = None
    if order_type == "LIMIT":
        price = questionary.text("Set Limit Order Target Execution Price:").ask()

    try:
        qty_float = float(quantity)
        price_float = float(price) if price else None
        validate_inputs(symbol, side, order_type, qty_float, price_float)
    except ValueError as val_err:
        logger.error(f"Input validation failure: {str(val_err)}")
        print(f"\n❌ Validation Failure: {str(val_err)}\n")
        return

    print("\n[ Running Engine Communications Pipeline... ]")
    result = client.place_order(symbol=symbol, side=side, order_type=order_type, quantity=qty_float, price=price_float)

    print("\n" + "-" * 40)
    if result["success"]:
        print("🎉 Execution Context Completed Successfully!")
        for k, v in result["data"].items():
            print(f" • {k}: {v}")
    else:
        print(f"❌ Transaction Refused: {result['error']}")
    print("-" * 40 + "\n")

if __name__ == "__main__":
    try:
        run_interactive_cli()
    except KeyboardInterrupt:
        print("\nEngine Shutdown Safely.")