
from datetime import datetime, timedelta
import requests

def log_data(values, cursor, dbconn):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO data_log (timestamp, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, *values))
    dbconn.commit()
    #print('Writed to db')



def get_bybit_prices(pair="ETHUSDC"):
    # Bybit Public API для тикеров
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "spot", "symbol": pair}
    response = requests.get(url, params=params).json()

    if response["retCode"] == 0:
        for ticker in response["result"]["list"]:
            if ticker["symbol"] == pair:
                return {
                    "lastPrice": ticker["lastPrice"],  # Последняя сделка
                    "bidPrice": ticker["bid1Price"],  # Лучшая цена покупки
                    "askPrice": ticker["ask1Price"]   # Лучшая цена продажи
                }
    return "Prices not found"



def get_binance_prices(pair="ETHUSDC"):
    url = "https://api.binance.com/api/v3/ticker/bookTicker"
    params = {"symbol": pair}
    response = requests.get(url, params=params).json()
    if "bidPrice" in response and "askPrice" in response:
        return {
            "lastPrice": get_binance_last_price(pair),  # Последняя сделка (нужен отдельный запрос)
            "bidPrice": response["bidPrice"],          # Лучшая цена покупки
            "askPrice": response["askPrice"]           # Лучшая цена продажи
        }
    return "Prices not found"


def get_binance_last_price(pair="ETHUSDC"):
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": pair}
    response = requests.get(url, params=params).json()
    if "price" in response:
        return response["price"]
    return "Last price not found"


def peak_filter(in_value, tolerance):
    global x
    return 0