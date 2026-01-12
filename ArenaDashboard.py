import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Multi-Trader Portfolio", layout="wide")

st.title("📊 Multi-Trader Portfolio Performance")

# -----------------------------
# Portfolio Input (Demo Data)
# -----------------------------
data = [
    {"Trader": "Gemini", "Ticker": "2330.TW", "Shares": 24, "Cost": 40320},
    {"Trader": "Gemini", "Ticker": "2313.TW", "Shares": 519, "Cost": 59483},
    {"Trader": "Grok", "Ticker": "2317.TW", "Shares": 86, "Cost": 20054},
    {"Trader": "Grok", "Ticker": "2308.TW", "Shares": 19, "Cost": 19285},
    {"Trader": "Deepseek", "Ticker": "2454.TW", "Shares": 10, "Cost": 14200},
]

df = pd.DataFrame(data)

# -----------------------------
# Fetch Live Prices
# -----------------------------
@st.cache_data(ttl=300)
def fetch_prices(tickers):
    prices = {}
    for t in tickers:
        try:
            price = yf.Ticker(t).history(period="1d")["Close"].iloc[-1]
            prices[t] = round(price, 2)
        except:
            prices[t] = None
    return prices

price_map = fetch_prices(df["Ticker"].unique())
df["PriceNow"] = df["Ticker"].map(price_map)

# -----------------------------
# Calculations
# -----------------------------
df["MarketValue"] = df["PriceNow"] * df["Shares"]
df["PnL"] = df["MarketValue"] - df["Cost"]
df["Revenue%"] = (df["PnL"] / df["Cost"] * 100).round(2)

# -----------------------------
# Trader Filter
# -----------------------------
traders = ["All"] + sorted(df["Trader"].unique())
selected_trader = st.selectbox("Select Trader", traders)

if selected_trader != "All":
    df = df[df["Trader"] == selected_trader]

# -----------------------------
# Display Table
# -----------------------------
st.dataframe(
    df[[
        "Trader", "Ticker", "PriceNow", "Shares",
        "Cost", "MarketValue", "PnL", "Revenue%"
    ]],
    use_container_width=True
)

# -----------------------------
# Summary Metrics
# -----------------------------
total_cost = df["Cost"].sum()
total_value = df["MarketValue"].sum()
total_pnl = total_value - total_cost
total_return = (total_pnl / total_cost * 100) if total_cost else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cost (TWD)", f"{total_cost:,.0f}")
col2.metric("Market Value (TWD)", f"{total_value:,.0f}")
col3.metric("PnL (TWD)", f"{total_pnl:,.0f}")
col4.metric("Return %", f"{total_return:.2f}%")

