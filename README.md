# 🌌 AuraQuant Pro AI

### Institutional-Grade Algorithmic Trading Terminal & Backtesting Simulator

AuraQuant Pro AI is a high-frequency, machine-learning-powered trading terminal built with Python and Streamlit. It integrates directly with MetaTrader 5 (MT5) to deliver advanced backtesting simulations, automated live trading execution, and intelligent risk management for professional-grade trading workflows.

---

# 🚀 Key Features

### 🔴 Live MT5 Integration
- Real-time trade execution directly through MetaTrader 5
- Auto-sync with MT5 terminal every 5 seconds
- Supports forex, gold, indices, and custom broker symbols

### 📊 Advanced Backtesting Simulator
- High-speed historical strategy testing
- Generates detailed Excel & CSV performance reports
- Interactive analytics and equity curve visualization

### 💎 Premium Dashboard UI
- Modern dark-themed Streamlit interface
- Glassmorphism-inspired trading panels
- Institutional-style monitoring experience

### 🧠 AI-Powered Support & Resistance
- Uses K-Means Clustering for intelligent Support & Resistance detection
- Dynamic target and stop-loss calculations
- Adaptive market structure analysis

### 🛡️ Dynamic Risk Management
- Kelly Criterion-based lot sizing
- Intelligent trailing stop-loss engine
- Capital protection mechanisms for volatile markets

### 🚨 Panic Liquidation System
- One-click emergency close for all open positions
- Instant risk-off functionality during market instability

---

# 📸 Dashboard Previews

## Live Trading Dashboard

<!-- Add Screenshot Here -->

<img width="1913" height="915" alt="Screenshot (865)" src="https://github.com/user-attachments/assets/5a927e65-c71c-4414-a596-4bb8d7ca1e9b" />


## Backtesting Analytics

<!-- Add Screenshot Here -->

<img width="1827" height="933" alt="Screenshot 2026-05-18 213941" src="https://github.com/user-attachments/assets/b66a8bc0-cc84-409e-a8d6-bae8fab9b85f" />


---

# 📋 Prerequisites

Before getting started, make sure the following requirements are met:

- **Operating System:** Windows OS  
  *(MetaTrader5 Python package officially supports Windows only)*

- **Trading Platform:**  
  - MetaTrader 5 Terminal installed
  - Logged into your broker account
  - Algorithmic Trading enabled

- **Python Version:** Python 3.9 or higher

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Pratik03538/Forex-Trading-Ai.git
cd Forex-Trading-Ai
```

## 2️⃣ Create a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🖥️ Usage Guide

## Step 1 — Open MetaTrader 5
Launch your MetaTrader 5 desktop terminal.

## Step 2 — Enable Algo Trading
Click the **"Algo Trading"** button in the toolbar until it turns **Green 🟢**.

## Step 3 — Allow Algorithmic Trading
Navigate to:

```text
Tools → Options → Expert Advisors
```

Enable:

```text
✔ Allow algorithmic trading
```

## Step 4 — Run the Dashboard

```bash
streamlit run auraquant_app.py
```

## Step 5 — Connect to Market
- Enter your trading symbol  
  *(Example: XAUUSD, GOLD.i#, BTCUSD, EURUSD)*

- Click **Connect**

---

# 📁 Project Structure

```text
Forex-Trading-Ai/
│
├── auraquant_app.py
├── requirements.txt
├── strategy/
├── models/
├── reports/
├── images/
├── backtesting/
├── live_trading/
└── utils/
```

---

# 🧠 Technologies Used

- Python
- Streamlit
- MetaTrader5 API
- Pandas
- NumPy
- Scikit-Learn
- Plotly
- OpenPyXL

---

# ⚠️ Disclaimer

This project is intended strictly for:

- Educational purposes
- Research & development
- Trading simulations

Trading financial markets involves substantial risk.  
The algorithms and AI models included in this project do **not** guarantee profits.

> Never trade with money you cannot afford to lose.

The developers are not responsible for any financial losses, damages, or liabilities resulting from the use of this software in live markets.

---

# ⭐ Support

If you like this project:

- ⭐ Star the repository
- 🍴 Fork the project
- 🛠️ Contribute improvements
- 🧠 Share feedback

---

# 📜 License

This project is licensed under the MIT License.
