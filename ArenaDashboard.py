import streamlit as st
import pandas as pd
import yfinance as yf

# ==============================
# 1. App Config (Must be first)
# ==============================
st.set_page_config(
    page_title="Portfolio Referee v2",
    layout="wide"
)

st.title("🧑‍⚖️ AI ARENA: Referee Tony's Dashboard, Game On since 2026/01/11")
st.info("📜 Note: Total Assets may exceed 100k if a team has Realized Profits (Sold stocks).")

STARTING_CAPITAL = 100_000

# ==============================
# 2. Initial Portfolio Dataset
# ==============================
data = [
    # ---------- Gemini (The Profit Taker) ----------
     # Update Jan 28: SOLD 5 shares of 2330 @ 1805. Realized +600 Profit.
 # Update Feb 2: Bought 100 Wistron @ 127.5.
    # Cash: 39,523 - 12,750 = 26,773
    # Wistron Shares: 377 + 100 = 477
    # Wistron Cost: 53,527 + 12,750 = 66,277
    {"Trader": "Gemini", "AssetType": "Cash",  "Ticker": "TWD",       "Shares": 26773,   "Cost": 26773}, 
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "3231.TW", "Shares": 477,     "Cost": 66277},
    {"Trader": "Gemini", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 5,       "Cost": 8425},
    
    # ---------- Grok (The Hodler) ----------
    {"Trader": "Grok", "AssetType": "Cash",  "Ticker": "TWD",       "Shares": 2412, "Cost": 2412},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2330.TW", "Shares": 38,    "Cost": 64890},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2454.TW", "Shares": 10,    "Cost": 18100},
    {"Trader": "Grok", "AssetType": "Stock", "Ticker": "2308.TW", "Shares": 19,    "Cost": 20235},

    # ---------- Deepseek (The Tech Bull) ----------
    {"Trader": "Deepseek", "AssetType": "Cash",  "Ticker": "TWD",       "Shares": 48091.5, "Cost": 48091.5},
    {"Trader": "Deepseek", "AssetType": "Stock",  "Ticker": "2317.TW",  "Shares": 165, "Cost": 36599.5},
    {"Trader": "Deepseek", "AssetType": "Stock",  "Ticker": "3034.TW",  "Shares": 30, "Cost": 11895},
]

df = pd.DataFrame(data)

# ==============================
# 3. Live Price Fetching
# ==============================
@st.cache_data(ttl=300)
def fetch_prices(tickers):
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
                prices[t] = 0.0 # Handle missing data safely
        except Exception:
            prices[t] = 0.0
    return prices
    
# Get unique tickers
stock_tickers = df[df["AssetType"] == "Stock"]["Ticker"].unique().tolist()
price_map = fetch_prices(stock_tickers)

# Map Prices to DataFrame
def get_current_price(row):
    if row["AssetType"] == "Cash":
        return 1.0
    return price_map.get(row["Ticker"], 0.0)

df["PriceNow"] = df.apply(get_current_price, axis=1)

# ==============================
# 4. Valuation Logic
# ==============================
# Market Value (Shares * Current Price)
df["MarketValue"] = df["PriceNow"] * df["Shares"]

# Unrealized PnL
df["Unrealized_PnL"] = df["MarketValue"] - df["Cost"]

# ==============================
# 5. League Table Logic
# ==============================
st.subheader("🏆 League Table (Live)")

summary = (
    df.groupby("Trader")
      .agg(
          TotalAssets=("MarketValue", "sum"),
          CashReserve=("MarketValue", lambda x: x[df.loc[x.index, "AssetType"] == "Cash"].sum())
      )
      .reset_index()
)

# ROI Calculation based on fixed 100k
summary["StartingCapital"] = STARTING_CAPITAL
summary["TotalPnL"] = summary["TotalAssets"] - STARTING_CAPITAL
summary["ROI %"] = (summary["TotalPnL"] / STARTING_CAPITAL * 100).round(2)

# Ranking
league = summary.sort_values(by="ROI %", ascending=False).reset_index(drop=True)
league.index += 1

# Highlighting Leader
def highlight_leader(s):
    # Safe check to ensure we only highlight if data exists
    is_max = s == s.max()
    return ['background-color: #d4edda' if v else '' for v in is_max]

try:
    st.dataframe(
        league.style.apply(highlight_leader, subset=["ROI %"]), 
        use_container_width=True
    )
except Exception as e:
    # Fallback if styling fails (rare, but prevents crash)
    st.error(f"Styling Error: {e}")
    st.dataframe(league, use_container_width=True)

# ==============================
# 6. Audit Section
# ==============================
with st.expander("🕵️ Referee Audit Log"):
    st.write("Checking underlying math:")
    st.dataframe(summary)

# ==============================
# 7. Detailed Inspector
# ==============================
st.divider()
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🔍 Inspector")
    selected_trader = st.radio("Select Team:", df["Trader"].unique())

with col2:
    st.subheader(f"{selected_trader}'s Portfolio")
    team_df = df[df["Trader"] == selected_trader].copy()
    
    # Calculate Revenue %
    # Avoid division by zero with a small lambda or numpy check if needed, 
    # but Cost should rarely be 0 in this dataset.
    team_df["Revenue %"] = ((team_df["MarketValue"] - team_df["Cost"]) / team_df["Cost"] * 100).round(2)
    
    st.dataframe(
        team_df[["AssetType", "Ticker", "Shares", "Cost", "PriceNow", "MarketValue", "Revenue %"]],
        use_container_width=True
    )
    
    # Cash Drag Analysis
    total_val = team_df["MarketValue"].sum()
    cash_val = team_df[team_df["AssetType"] == "Cash"]["MarketValue"].sum()
    
    if total_val > 0:
        ratio = cash_val / total_val
        st.progress(ratio, text=f"Cash Position: {round(ratio * 100)}%")
    else:
        st.warning("Total Value is 0 (Data fetch error?), cannot calculate Cash Position.")
