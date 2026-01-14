import streamlit as st
import pandas as pd
import yfinance as yf

# ==============================
# App Config
# ==============================
st.set_page_config(
    page_title="Portfolio Referee v2",
    layout="wide"
)

st.title("🧑‍⚖️ AI ARENA: Referee Dashboard")
st.info("📜 Note: Total Assets may exceed 100k if a team has Realized Profits (Sold stocks).")

STARTING_CAPITAL = 100_000

# ==============================
# Initial Portfolio Dataset
# ==============================
data = [
    # ---------- Gemini (The Profit Taker) ----------
    # Note: Cash includes Realized Profit from TSMC (Buy 59,150 -> Sell 60,025)
    # To track PnL correctly, we separate "Original Capital" vs "Realized Gain" implicitly here
    {"Trader": "Gemini", "AssetType": "Cash",  "Ticker": "TWD",       "Shares": 60848,   "Cost": 60848}, 
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "3231.TW", "Shares": 277,    "Cost": 40027},

    # ---------- Grok (The Hodler) ----------
    {"Trader": "Grok", "AssetType": "Cash",  "Ticker": "TWD",      "Shares": 2142, "Cost": 2142},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 23,   "Cost": 38640},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2317.TW", "Shares": 86,   "Cost": 20054},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2454.TW", "Shares": 14,   "Cost": 19880},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2308.TW", "Shares": 19,   "Cost": 19285},

    # ---------- Deepseek (The Tech Bull) ----------
    {"Trader": "Deepseek", "AssetType": "Cash",  "Ticker": "TWD",      "Shares": 57275, "Cost": 57275},
    {"Trader": "Deepseek", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 10,    "Cost": 16900},
    {"Trader": "Deepseek", "AssetType": "Stock", "Ticker": "2454.TW", "Shares": 10,    "Cost": 14450},
    {"Trader": "Deepseek", "AssetType": "Stock", "Ticker": "2317.TW", "Shares": 50,    "Cost": 11375},
]

df = pd.DataFrame(data)

# ==============================
# Live Price Fetching (Stocks Only)
# ==============================
@st.cache_data(ttl=300)
def fetch_prices(tickers):
    # REMOVED st.toast to fix CacheReplayClosureError
    prices = {}
    for t in tickers:
        try:
            # Check if Ticker is TWD (Cash) to avoid API errors
            if t == "TWD":
                prices[t] = 1.0
                continue
            
            stock = yf.Ticker(t)
            hist = stock.history(period="1d")
            if not hist.empty:
                prices[t] = round(hist["Close"].iloc[-1], 2)
            else:
                prices[t] = 0 # Error handling
        except Exception:
            prices[t] = 0
    return prices
    
# Get unique tickers (excluding TWD placeholders if needed)
stock_tickers = df[df["AssetType"] == "Stock"]["Ticker"].unique().tolist()
price_map = fetch_prices(stock_tickers)

# Map Prices
def get_current_price(row):
    if row["AssetType"] == "Cash":
        return 1.0
    return price_map.get(row["Ticker"], 0)

df["PriceNow"] = df.apply(get_current_price, axis=1)

# ==============================
# Valuation Logic
# ==============================
# 1. Market Value (What is it worth today?)
df["MarketValue"] = df["PriceNow"] * df["Shares"]

# 2. Unrealized PnL (For Open Positions)
# For Cash, MarketValue = Cost, so PnL is 0 naturally.
# BUT Gemini has Realized Profit sitting in Cash. 
# We calculate Total Portfolio Value to derive Total PnL vs 100k Capital.
df["Unrealized_PnL"] = df["MarketValue"] - df["Cost"]

# ==============================
# League Table (The Truth)
# ==============================
st.subheader("🏆 League Table (Live)")

# Group by Trader to get Total Assets
summary = (
    df.groupby("Trader")
      .agg(
          TotalAssets=("MarketValue", "sum"),
          CashReserve=("MarketValue", lambda x: x[df.loc[x.index, "AssetType"] == "Cash"].sum())
      )
      .reset_index()
)

# Calculate ROI based on FIXED 100k Starting Capital
# This captures Realized Gains accurately.
summary["StartingCapital"] = STARTING_CAPITAL
summary["TotalPnL"] = summary["TotalAssets"] - STARTING_CAPITAL
summary["ROI %"] = (summary["TotalPnL"] / STARTING_CAPITAL * 100).round(2)

# Ranking
league = summary.sort_values(by="ROI %", ascending=False).reset_index(drop=True)
league.index += 1

# Display with Highlight for Leader
def highlight_leader(s):
    is_max = s == s.max()
    return ['background-color: #d4edda' if v else '' for v in is_max]

st.dataframe(
    league.style.apply(highlight_leader, subset=["ROI %"]), 
    use_container_width=True
)

# ==============================
# Audit Section (Non-Blocking)
# ==============================
with st.expander("🕵️ Referee Audit Log"):
    st.write("Checking if Total Assets >= 100,000 (Did anyone lose money?)")
    st.dataframe(summary)

# ==============================
# Detailed View
# ==============================
st.divider()
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🔍 Inspector")
    selected_trader = st.radio("Select Team:", df["Trader"].unique())

with col2:
    st.subheader(f"{selected_trader}'s Portfolio")
    team_df = df[df["Trader"] == selected_trader].copy()
    
    # Beautify
    team_df["Revenue %"] = ((team_df["MarketValue"] - team_df["Cost"]) / team_df["Cost"] * 100).round(2)
    
    st.dataframe(
        team_df[["AssetType", "Ticker", "Shares", "Cost", "PriceNow", "MarketValue", "Revenue %"]],
        use_container_width=True
    )
    
    # Cash Drag Analysis
    total_val = team_df["MarketValue"].sum()
    cash_val = team_df[team_df["AssetType"] == "Cash"]["MarketValue"].sum()
    st.progress(cash_val / total_val, text=f"Cash Position: {round(cash_val / total_val * 100)}%")
