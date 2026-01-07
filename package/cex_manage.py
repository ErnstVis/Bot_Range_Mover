import requests
from datetime import datetime
import time



# from pybit.unified_trading import HTTP
# from pybit.unified_trading import WebSocket
# from binance.client import Client
# from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET



def get_market_snapshot(exchange: str, pair: str = "ETHUSDC", timeout=5):
    if exchange.lower() == "binance":
        return _get_binance_snapshot(pair, timeout)
    elif exchange.lower() == "bybit":
        return _get_bybit_snapshot(pair, timeout)
    else:
        raise ValueError(f"Unknown exchange: {exchange}")
    

def _get_binance_snapshot(pair, timeout):
    # 24h статистика — тут есть и last, и volume
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": pair}

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    return {
        "exchange": "binance",
        "pair": pair,
        "last": float(data["lastPrice"]),
        "bid": float(data["bidPrice"]),
        "ask": float(data["askPrice"]),
        "volume_24h": float(data["quoteVolume"]),  # объём в котируемой валюте (USDC)
        "timestamp": datetime.utcnow()
    }

def _get_bybit_snapshot(pair, timeout):
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "spot",
        "symbol": pair
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    if data["retCode"] != 0:
        raise RuntimeError(data["retMsg"])

    ticker = data["result"]["list"][0]

    return {
        "exchange": "bybit",
        "pair": pair,
        "last": float(ticker["lastPrice"]),
        "bid": float(ticker["bid1Price"]),
        "ask": float(ticker["ask1Price"]),
        "volume_24h": float(ticker["turnover24h"]),  # оборот за 24h в котируемой валюте
        "timestamp": datetime.utcnow()
    }

def get_binance_volume(pair="ETHUSDC", interval="1m", timeout=5):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": pair,
        "interval": interval,
        "limit": 1
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    kline = r.json()[0]

    return {
        "volume_base": float(kline[5]),   # объём в ETH
        "volume_quote": float(kline[7])   # объём в USDC
    }
def get_binance_volume_closed(pair="ETHUSDC", interval="1m", timeout=5):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": pair,
        "interval": interval,
        "limit": 2
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    klines = r.json()

    closed_kline = klines[-2]  # предыдущая закрытая свеча

    return {
        "volume_base": float(closed_kline[5]),
        "volume_quote": float(closed_kline[7])
    }




def get_bybit_volume(pair="ETHUSDC", interval="1", timeout=5):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "spot",
        "symbol": pair,
        "interval": interval,
        "limit": 1
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    if data["retCode"] != 0:
        raise RuntimeError(data["retMsg"])

    kline = data["result"]["list"][0]

    return {
        "volume_base": float(kline[5]),     # объём в ETH
        "volume_quote": float(kline[6])     # оборот в USDC
    }
def get_bybit_volume_closed(pair="ETHUSDC", interval="1", timeout=5):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "spot",
        "symbol": pair,
        "interval": interval,
        "limit": 2
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    if data["retCode"] != 0:
        raise RuntimeError(data["retMsg"])


    klines = data["result"]["list"]
    klines_sorted = sorted(klines, key=lambda x: int(x[0]))
    closed_kline = klines_sorted[-2]

    return {
        "volume_base": float(closed_kline[5]),
        "volume_quote": float(closed_kline[6])
    }





def get_binance_orderbook(pair="ETHUSDC", limit=5, timeout=5):
    url = "https://api.binance.com/api/v3/depth"
    params = {
        "symbol": pair,
        "limit": limit
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    bids = [(float(p), float(q)) for p, q in data["bids"]]
    asks = [(float(p), float(q)) for p, q in data["asks"]]

    return {
        "exchange": "binance",
        "pair": pair,
        "best_bid": bids[0],
        "best_ask": asks[0],
        "bids": bids,
        "asks": asks
    }


def get_bybit_orderbook(pair="ETHUSDC", depth=5, timeout=5):
    url = "https://api.bybit.com/v5/market/orderbook"
    params = {
        "category": "spot",
        "symbol": pair,
        "limit": depth
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    if data["retCode"] != 0:
        raise RuntimeError(data["retMsg"])

    bids = [(float(p), float(q)) for p, q in data["result"]["b"]]
    asks = [(float(p), float(q)) for p, q in data["result"]["a"]]

    return {
        "exchange": "bybit",
        "pair": pair,
        "best_bid": bids[0],
        "best_ask": asks[0],
        "bids": bids,
        "asks": asks
    }





# vol = (high - low) / open
# can be normalive with volume or liquidity
# this needed to predict about potential range outbreaks



















b = get_market_snapshot("binance", "ETHUSDC")
y = get_market_snapshot("bybit", "ETHUSDC")

spread = y["bid"] - b["ask"]

print(b)
print(y)
print("Spread:", spread)



print(get_binance_volume_closed("ETHUSDC", "1m")["volume_quote"])

print(get_bybit_volume_closed("ETHUSDC", "1")["volume_quote"])



ob_binance = get_binance_orderbook("ETHUSDC", limit=5)
print(ob_binance)
ob_bybit = get_bybit_orderbook("ETHUSDC", depth=5)
print(ob_bybit)

bid_price, bid_qty = ob_binance["best_bid"]
ask_price, ask_qty = ob_binance["best_ask"]

print("Bid:", bid_price, bid_qty)
print("Ask:", ask_price, ask_qty)



print("BINANCE")
print("Bid:", ob_binance["best_bid"])
print("Ask:", ob_binance["best_ask"])

print("\nBYBIT")
print("Bid:", ob_bybit["best_bid"])
print("Ask:", ob_bybit["best_ask"])
#

binance_bid_qty = ob_binance["best_bid"][1]
bybit_bid_qty = ob_bybit["best_bid"][1]

print("Binance best bid qty:", binance_bid_qty)
print("Bybit best bid qty:", bybit_bid_qty)
#

def total_quote_volume(levels):
    return sum(price * qty for price, qty in levels)

binance_bid_depth = total_quote_volume(ob_binance["bids"])
binance_ask_depth = total_quote_volume(ob_binance["asks"])

print("Binance bid depth (USDC):", binance_bid_depth)
print("Binance ask depth (USDC):", binance_ask_depth)


#

for _ in range(5):
    ob = get_binance_orderbook("ETHUSDC", limit=5)
    print(ob["best_bid"], ob["best_ask"])
    time.sleep(1)