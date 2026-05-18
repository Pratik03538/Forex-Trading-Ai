🌌 Pratik's AuraQuant Pro AI

Institutional God-Level Algorithmic Trading Terminal & Simulator

AuraQuant Pro AI is a high-frequency, machine-learning-powered trading terminal built on Python and Streamlit, designed to interface seamlessly with MetaTrader 5 (MT5). It features a limitless profit backtesting simulator and a fully automated live trading engine with dynamic risk management.

📸 Dashboard Previews

(Screenshots will be added here)

🚀 Key Features

🔴 Live MT5 Integration: Real-time execution of trades directly to your MetaTrader 5 terminal with auto-sync every 5 seconds.

📊 Limitless Simulator: Deep backtesting engine that outputs detailed Excel/CSV reports and renders beautiful Area & Pie charts.

💎 Glassmorphism UI: A premium, modern, dark-themed Streamlit interface built for hedge-fund level monitoring.

🧠 Machine Learning S&R: Uses K-Means Clustering to detect highly accurate Support and Resistance zones for dynamic targets.

🛡️ Dynamic Risk Management: Features Kelly Criterion-based lot sizing and God-Level Trailing Stop Losses to lock in profits.

🚨 Panic Liquidation: One-click emergency position closing for all active trades.

📋 Prerequisites

Before you begin, ensure you have met the following requirements:

Operating System: Windows OS (MetaTrader 5 Python library only works on Windows)

Trading Platform: MetaTrader 5 Terminal installed and logged in (Master Password required for live trades).

Environment: Python 3.9 or higher.

⚙️ Installation

Clone the repository:

git clone https://github.com/Pratik03538/Forex-Trading-Ai.git
cd Forex-Trading-Ai


Create a virtual environment (Recommended):

python -m venv venv
venv\Scripts\activate


Install the required dependencies:

pip install -r requirements.txt


🖥️ Usage Guide

Open your MetaTrader 5 desktop application.

Click on the "Algo Trading" button in the top toolbar to turn it Green (🟢).

Go to Tools -> Options -> Expert Advisors and tick "Allow algorithmic trading".

Open your terminal in the project folder and run the Streamlit dashboard:

streamlit run auraquant_app.py


Enter your active asset symbol (e.g., XAUUSD or GOLD.i#) and click Connect!

⚠️ Disclaimer

This software is for educational, research, and simulation purposes only. The algorithms and machine learning models do not guarantee profits. Do not risk money which you are afraid to lose. The developers and contributors are not responsible for any financial losses incurred while using this bot in live markets.
