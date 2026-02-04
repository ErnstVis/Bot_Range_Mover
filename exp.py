
import requests






url = "https://api.binance.com/api/v3/exchangeInfo"

r = requests.get(url, timeout=10)
r.raise_for_status()
data = r.json()

symbols = [s["symbol"] for s in data["symbols"]]

for s in sorted(symbols):
    if s[0] == "E":
        print(s)
