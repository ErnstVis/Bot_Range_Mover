# This script fetches the price data for two altcoins from Binance, calculates the price ratio between them, and plots the resulting curve.


import ccxt
import matplotlib.pyplot as plt
import pandas as pd

# Tokens
symbol_alt1 = 'POL'
symbol_alt2 = 'LINK'

# Periods
timeframe = '1d'
limit = 720


symbol_alt1alt2 = symbol_alt1 + '/' + symbol_alt2
symbol_alt1usdt = symbol_alt1 + '/USDT'
symbol_alt2usdt = symbol_alt2 + '/USDT'


exchange = ccxt.binance()


ohlcv_alt1 = exchange.fetch_ohlcv(symbol_alt1usdt, timeframe, limit=limit)
df_alt1 = pd.DataFrame(ohlcv_alt1, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df_alt1['timestamp'] = pd.to_datetime(df_alt1['timestamp'], unit='ms')


ohlcv_alt2 = exchange.fetch_ohlcv(symbol_alt2usdt, timeframe, limit=limit)
df_alt2 = pd.DataFrame(ohlcv_alt2, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df_alt2['timestamp'] = pd.to_datetime(df_alt2['timestamp'], unit='ms')


df_alt1[symbol_alt1usdt] = df_alt1['close']
df_alt2[symbol_alt2usdt] = df_alt2['close']


df = pd.merge(df_alt1[['timestamp', symbol_alt1usdt]], df_alt2[['timestamp', symbol_alt2usdt]], on='timestamp')


df[symbol_alt1alt2] = df[symbol_alt1usdt] / df[symbol_alt2usdt]


plt.figure(figsize=(10, 6))
plt.plot(df['timestamp'], df[symbol_alt1alt2], label=symbol_alt1alt2, marker='o')
plt.title('Price curve ' + symbol_alt1alt2)
plt.xlabel('Time')
plt.ylabel('Price ' + symbol_alt1alt2)
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('pictures/curves_' + symbol_alt1 + symbol_alt2 + '.png')