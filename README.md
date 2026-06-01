# ⚡ Quantum Core Algorithmic Trading Console

Quantum Core is a high-performance, responsive full-stack trading workspace engineered to interface natively with the Binance Futures Testnet gateway. The terminal provides retail traders with professional-grade execution frameworks, incorporating low-latency state polling, automated precision clamping, and an asynchronous, multi-threaded background Time-Weighted Average Price (TWAP) algorithmic trading engine.

---

## ✨ Key System Features

### 📊 Real-Time Interface Matrix
* **Synchronized Charting:** Employs the native TradingView advanced charting widget to visualize active token price trajectories.
* **Low-Latency Polling Engine:** Utilizes a highly optimized 2-second client-side thread loop to continuously keep available margin, contract inventory size, working limits, and execution history updated on screen without full page refreshes.
* **Dual-State Controller:** Supports high-impact structural toggling between **BUY / LONG** and **SELL / SHORT** modes, instantly flipping form properties and visual color feedback cues (Neon Green vs Warning Red).

### 🛠️ Core Order Handling
* **Market Dispatches:** Transmits lightning-fast market execution payloads directly to the order book.
* **Resting Limit Books:** Allows precise, tick-aligned limit entry staging. Order state isolation filters keep unexecuted limits entirely within the pending queues, leaving your active positions and holding values completely undisturbed until an official execution occurs.

### 🤖 Detached TWAP Slicing Algorithm
* **Non-Blocking Background Threads:** Spawns detached, asynchronous Python daemon workers to run allocation loops over 5, 10, 30, or 60-minute domains without freezing user interface loops or blocking backend web requests.
* **Visual Slicing Pipelines:** Renders running algorithm metrics inside custom tracking cells, featuring progress indicators, exact execution counts, and active sub-status text feeds.
* **Emergency Halt Switch:** Exposes an immediate structural kill routine to safely abort running background loops mid-cycle.

### 🛡️ Safety & Clamping Guardrails
* **Dynamic Notional Scaling:** Automatically enforces the exchange's strict $50 minimum notional parameter. If standard configurations fall under $50, the backend calculates the required offset size and steps up the contract volume seamlessly before transmission to avoid Code `-4164` failures.
* **Precision Formatting Gates:** Feeds all transactional values through math filters to cleanly clip floats down to token-specific lot sizes (`stepSize`) and pricing steps (`tickSize`), entirely eliminating round-off validation errors.

---


<img width="919" height="412" alt="image" src="https://github.com/user-attachments/assets/b9832654-7df2-4877-99b6-a2a14b1798e6" />

---

## ⚙️ Setup & Installation Steps

### 1. Prerequisites & Environment Initialization
Ensure Python 3.8+ is installed on your local host system. Create a secure environment configuration file named `.env` in the root folder containing your testnet credentials:


BINANCE_API_KEY=your_binance_testnet_api_key_here
BINANCE_API_SECRET=your_binance_testnet_api_secret_here
2. Dependency Allocation
Install the required production-grade dependencies by running:

Bash
pip install -r requirements.txt
3. Launching the Local Server
Boot up the engine console proxy router interface:

Bash
python server.py
Open your web browser workspace engine and navigate to: http://127.0.0.1:5000

##🚀 How to Run Examples

A. Executing a Standard MARKET Order
Select ETHUSDT from the top ticker pills matrix.

Ensure the Master Execution Mode toggle is highlighted on BUY / LONG.

Select MARKET under the Order Frame Structure.

Input your desired size (e.g., 0.05). Note: If the final notional value falls under $50, the backend gateway will automatically scale it to pass exchange floors cleanly.

Click Transmit Long Order.

B. Deploying an Asynchronous TWAP Algorithm
Toggle the target structure to TWAP.

Select your calculation window (e.g., 5 Minutes) and target Execution Slices Count (e.g., 5). This configures the engine to drop 1 slice every 60 seconds.

Input your Total Accumulation Volume (e.g., 0.1).

Click Deploy TWAP Long Algorithm.

Switch to the Open Pending Orders tab section below the chart area to watch your progress bars update in real-time.

🧠 System Assumptions & Bounds
USDT Collateralization: The engine assumes an active, funded USDT-M Futures Contract Wallet setup. It strictly filters account balance streams to parse USDT values.

Isolated vs. Cross Margin: Leverage sizing maximums default to standard cross matrix indicators returned via positionRisk structures.

Testnet Domain Locks: Requests route strictly through the https://testnet.binancefuture.com network layer endpoints.

<img width="1185" height="249" alt="image" src="https://github.com/user-attachments/assets/2be16a58-9bd4-4736-bbfd-a7f01516d3ee" />

🟢 1. MARKET Order Log Signature
Plaintext
 System UI mapping loaded.
 Linked backend Flask proxy server successfully.
 Submitting execution sequence payload blocks to engine...
 [RECOVERY GATEWAY] Sizing up tiny notional value ($3.12) to safe allocation quantity: 0.017
 [API POST] Path /fapi/v1/order executed payload -> symbol=ETHUSDT&side=BUY&type=MARKET&quantity=0.017
 Order Dispatched: MARKET | Status: FILLED | Executed Qty: 0.017 | Avg Price: $3412.50
 [POLLED] Balance updated: 1450.23 USDT | ETH Position parsed: +0.017
🟡 2. LIMIT Order Log Signature
Plaintext
 Context switched to BTCUSDT
 Loaded bounds for BTCUSDT: Min=0.001, Max Safe=0.241, Tick=0.1
 Submitting execution sequence payload blocks to engine...
 [API POST] Path /fapi/v1/order executed payload -> symbol=BTCUSDT&side=SELL&type=LIMIT&quantity=0.005&price=67200.0&timeInForce=GTC
 Order Dispatched: LIMIT | Status: NEW | OrderID: 8824109521 | Resting on book at $67,200.0
 [CONSOLE] Auditing active pending limit queues for BTCUSDT -> 1 Resting Order mounted safely.
