import streamlit as st
import pandas as pd
import yfinance as yf

# V2 Dashboard(ChatGPT)=========
# App Config
# ==============================
st.set_page_config(
    page_title="Portfolio Referee v2",
    layout="wide"
)

st.title("🧑‍⚖️ AI ARENA since (2026/01/11) Referee Tony Dashboard")
st.info("📜 Rule: Each team must start with exactly 100,000 TWD (±1 TWD rounding tolerance).")

STARTING_CAPITAL = 100_000
TOLERANCE = 1

# ==============================
# Initial Portfolio Dataset
# ==============================
data = [
    # ---------- Gemini ----------
    {"Trader": "Gemini", "AssetType": "Cash",  "Ticker": None,      "Shares": 60848,   "Cost": 60848},
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "3231.TW", "Shares": 277,    "Cost": 40027},

    # ---------- Grok ----------
    {"Trader": "Grok", "AssetType": "Cash",  "Ticker": None,      "Shares": 2142, "Cost": 2142},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 23,   "Cost": 38640},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2317.TW", "Shares": 86,   "Cost": 20054},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2454.TW", "Shares": 14,   "Cost": 19880},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2308.TW", "Shares": 19,   "Cost": 19285},

    # ---------- Deepseek ----------
    {"Trader": "Deepseek", "AssetType": "Cash",  "Ticker": None,      "Shares": 57275, "Cost": 57275},
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
    prices = {}
    for t in tickers:
        try:
            prices[t] = round(
                yf.Ticker(t).history(period="1d")["Close"].iloc[-1], 2
            )
        except Exception:
            prices[t] = None
    return prices

stock_tickers = df.loc[df["AssetType"] == "Stock", "Ticker"].unique()
price_map = fetch_prices(stock_tickers)

df["PriceNow"] = df.apply(
    lambda r: 1.0 if r["AssetType"] == "Cash"
    else price_map.get(r["Ticker"], 0),
    axis=1
)

# ==============================
# Valuation Logic (Referee Rules)
# ==============================
df["MarketValue"] = df["PriceNow"] * df["Shares"]
df["PnL"] = df["MarketValue"] - df["Cost"]

df["Revenue%"] = df.apply(
    lambda r: 0.0 if r["AssetType"] == "Cash"
    else round((r["PnL"] / r["Cost"]) * 100, 2),
    axis=1
)

# ==============================
# Starting Capital Audit
# ==============================
capital_audit = (
    df.groupby("Trader")
      .agg(
          Cash=("Cost", lambda x: x[df.loc[x.index, "AssetType"] == "Cash"].sum()),
          TotalCost=("Cost", "sum")
      )
      .reset_index()
)

capital_audit["Diff"] = capital_audit["TotalCost"] - STARTING_CAPITAL
capital_audit["Valid"] = capital_audit["Diff"].abs() <= TOLERANCE

st.subheader("🧮 Starting Capital Audit (Referee Check)")
st.dataframe(capital_audit, use_container_width=True)

invalid_teams = capital_audit[~capital_audit["Valid"]]

if not invalid_teams.empty:
    st.error(
        "⛔ Capital violation detected: "
        + ", ".join(invalid_teams["Trader"])
    )
else:
    st.success("✅ All teams passed the starting capital rule")

# ==============================
# Enforce Rule (Exclude Invalid Teams)
# ==============================
valid_traders = capital_audit[capital_audit["Valid"]]["Trader"]
df = df[df["Trader"].isin(valid_traders)]

# ==============================
# Trader-Level Summary
# ==============================
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

# ==============================
# League Table
# ==============================
league = summary.sort_values(
    by=["Return%", "TotalPnL"],
    ascending=False
).reset_index(drop=True)

league.index += 1

st.subheader("🏆 League Table (Referee Ranking)")
st.dataframe(league, use_container_width=True)

# ==============================
# Transparency: Position-Level View
# ==============================
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
