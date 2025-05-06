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

# Инициализация биржи (например, Binance)
exchange = ccxt.binance()

# Получение данных для ALT1/USDT
ohlcv_alt1 = exchange.fetch_ohlcv(symbol_alt1usdt, timeframe, limit=limit)
df_alt1 = pd.DataFrame(ohlcv_alt1, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df_alt1['timestamp'] = pd.to_datetime(df_alt1['timestamp'], unit='ms')

# Получение данных для ALT2/USDT
ohlcv_alt2 = exchange.fetch_ohlcv(symbol_alt2usdt, timeframe, limit=limit)
df_alt2 = pd.DataFrame(ohlcv_alt2, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df_alt2['timestamp'] = pd.to_datetime(df_alt2['timestamp'], unit='ms')

# Вычисление цены ALT1/ALT2
df_alt1[symbol_alt1usdt] = df_alt1['close']
df_alt2[symbol_alt2usdt] = df_alt2['close']

# Объединение данных по времени
df = pd.merge(df_alt1[['timestamp', symbol_alt1usdt]], df_alt2[['timestamp', symbol_alt2usdt]], on='timestamp')

# Вычисление цены SUI/SOL
df[symbol_alt1alt2] = df[symbol_alt1usdt] / df[symbol_alt2usdt]

# Построение графика
plt.figure(figsize=(10, 6))
plt.plot(df['timestamp'], df[symbol_alt1alt2], label=symbol_alt1alt2, marker='o')
plt.title('График цены ' + symbol_alt1alt2)
plt.xlabel('Время')
plt.ylabel('Цена ' + symbol_alt1alt2)
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output.png')