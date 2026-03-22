import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# === Streamlit titel ===
st.title("Crypto Trading Dashboard")

# === Verbinding met Coinbase ===
exchange = ccxt.coinbase({
    "apiKey": "apikey",
    "secret": "secret",
    "enableRateLimit": True
})

# === Sidebar instellingen ===
symbol = st.sidebar.selectbox(
    "Trading pair",
    ["BTC/USDC", "SOL/USDC", "XRP/USDC", "DOGE/USDC", "ADA/USDC"]
)

timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"])
stop_loss = st.sidebar.slider("Stop-loss (%)", 1, 20, 5)
take_profit = st.sidebar.slider("Take-profit (%)", 1, 20, 10)


# == Saldo ophalen en trade size berekenen ==
balance = exchange.fetch_balance()
usdc_balance = balance['USDC']['free']  # hoofdletters!

# Haal de actuele prijs van het gekozen pair op
current_price = exchange.fetch_ticker(symbol)['last']

# Bereken maximale trade size
max_trade_size = round(usdc_balance / current_price, 6)

# Stel een standaardwaarde in (bijv. 10% van max)
default_trade_size = round(max_trade_size * 0.1, 6)

# Sidebar input met dynamische label
trade_size = st.sidebar.number_input(
    f"Trade size ({symbol.split('/')[0]})",
    min_value=0.0,
    max_value=max_trade_size,
    value=default_trade_size,   # <-- niet max_trade_size!
    step=0.000001               # kleine stapjes mogelijk
)

st.sidebar.write(f"Beschikbaar saldo: {usdc_balance:.2f} USDC")
st.sidebar.write(f"Maximale trade size: {max_trade_size} {symbol.split('/')[0]}")
# == Bovenaan tekst tonen ==
st.write(f"**Trading pair:** {symbol}")
st.write(f"**Timeframe:** {timeframe}")
st.write(f"**Take-profit:** {take_profit}%")
st.write(f"**Stop-loss:** {stop_loss}%")
st.write(f"**Beschikbaar saldo:** {usdc_balance:.2f} USDC")
st.write(f"**Maximale trade size:** {max_trade_size} {symbol.split('/')[0]}")


# === Marktdata ophalen ===
ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# === Indicators ===
df['MA_short'] = df['close'].rolling(20).mean()
df['MA_long'] = df['close'].rolling(50).mean()

# RSI berekenen
delta = df['close'].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(14).mean()
avg_loss = pd.Series(loss).rolling(14).mean()
rs = avg_gain / avg_loss
df['RSI'] = 100 - (100 / (1 + rs))

# Buy/Sell signalen
buy_signals = df[(df['MA_short'] > df['MA_long']) & (df['RSI'] < 30)]
sell_signals = df[(df['MA_short'] < df['MA_long']) & (df['RSI'] > 70)]

# === Prijsgrafiek ===
fig, ax = plt.subplots(figsize=(12,6))
ax.plot(df['timestamp'], df['close'], label='Price', color='blue')
ax.plot(df['timestamp'], df['MA_short'], label='MA 20', color='orange')
ax.plot(df['timestamp'], df['MA_long'], label='MA 50', color='green')
ax.scatter(buy_signals['timestamp'], buy_signals['close'], label='Buy', marker='^', color='green')
ax.scatter(sell_signals['timestamp'], sell_signals['close'], label='Sell', marker='v', color='red')
ax.set_title(f"{symbol} - Multi-Strategie filter (RSI + MA)")
ax.legend()
st.pyplot(fig)

# === RSI grafiek ===
fig2, ax2 = plt.subplots(figsize=(12,4))
ax2.plot(df['timestamp'], df['RSI'], label='RSI', color='purple')
ax2.axhline(70, linestyle='--', color='red', label='Overbought')
ax2.axhline(30, linestyle='--', color='green', label='Oversold')
ax2.set_title("RSI Indicator")
ax2.legend()
st.pyplot(fig2)
