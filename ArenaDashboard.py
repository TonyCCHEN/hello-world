import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Referee Portfolio", layout="wide")

st.title("🧑‍⚖️ Portfolio Referee Dashboard")

# --------------------------------
# Portfolio Rules (Input Data)
# --------------------------------
data = [
    # Gemini
    {"Trader": "Gemini", "AssetType": "Cash",  "Ticker": None,      "Shares": 198,   "Cost": 198},
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 24,    "Cost": 40320},
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "2313.TW", "Shares": 519,   "Cost": 59483},

    # Grok
    {"Trader": "Grok", "AssetType": "Cash",  "Ticker": None,      "Shares": 2142, "Cost": 2142},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2317.TW", "Shares": 86,   "Cost": 20054},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2308.TW", "Shares": 19,   "Cost": 19285},

    # Deepseek
    {"Trader": "Deepseek", "AssetType": "Cash",  "Ticker": None,      "Shares": 69000, "Cost": 69000},
    {"Trader": "Deepseek", "AssetType": "Stock", "Ticker": "2454.TW", "Shares": 10,    "Cost": 14200},
]

df = pd.DataFrame(data)

# --------------------------------
# Fetch Live Prices (Stocks Only)
# --------------------------------
@st.cache_data(ttl=300)
def fetch_prices(tickers):
    prices = {}
    for t in tickers:
        try:
            prices[t] = round(
                yf.Ticker(t).history(period="1d")["Close"].iloc[-1], 2
            )
        except:
            prices[t] = None
    return prices

stock_tickers = df.loc[df["AssetType"] == "Stock", "Ticker"].unique()
price_map = fetch_prices(stock_tickers)

df["PriceNow"] = df.apply(
    lambda r: 1.0 if r["AssetType"] == "Cash" else price_map.get(r["Ticker"], 0),
    axis=1
)

# --------------------------------
# Referee Valuation Rules
# --------------------------------
df["MarketValue"] = df["PriceNow"] * df["Shares"]
df["PnL"] = df["MarketValue"] - df["Cost"]

df["Revenue%"] = df.apply(
    lambda r: 0.0 if r["AssetType"] == "Cash"
    else round(r["PnL"] / r["Cost"] * 100, 2),
    axis=1
)

# --------------------------------
# Trader-Level Aggregation
# --------------------------------
summary = (
    df.groupby("Trader")
    .agg(
        TotalCost=("Cost", "sum"),
        MarketValue=("MarketValue", "sum"),
        TotalPnL=("PnL", "sum"),
        Cash=("MarketValue", lambda x: x[df.loc[x.index, "AssetType"] == "Cash"].sum())
    )
    .reset_index()
)

summary["Return%"] = (summary["TotalPnL"] / summary["TotalCost"] * 100).round(2)
summary["CashRatio%"] = (summary["Cash"] / summary["MarketValue"] * 100).round(1)

# --------------------------------
# League Table (Referee Ranking)
# --------------------------------
league = summary.sort_values(
    by=["Return%", "TotalPnL"], ascending=False
).reset_index(drop=True)

league.index += 1  # Rank starts from 1

st.subheader("🏆 League Table (Referee Ranking)")
st.dataframe(league, use_container_width=True)

# --------------------------------
# Detail View (Transparency)
# --------------------------------
st.subheader("🔍 Position-Level Transparency")
selected_trader = st.selectbox(
    "Inspect Trader",
    df["Trader"].unique()
)

st.dataframe(
    df[df["Trader"] == selected_trader][[
        "AssetType", "Ticker", "PriceNow",
        "Shares", "Cost", "MarketValue",
        "PnL", "Revenue%"
    ]],
    use_container_width=True
)
