# to do cex price log

import time
import sqlite3
import utils_aux

db_name = 'prices_cex.db'
dbconn = sqlite3.connect(db_name)
cursor = dbconn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS data_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    value1 REAL,
    value2 REAL,
    value3 REAL,
    value4 REAL,
    value5 REAL,
    value6 REAL,
    value7 REAL,
    value8 REAL,
    value9 REAL,
    value10 REAL,
    value11 REAL,
    value12 REAL
)
''')
dbconn.commit()
data_to_db = [0,0,0,0,0,0,0,0,0,0,0,0]
i = 0

while i < 500:
    prices = utils_aux.get_bybit_prices("ETHUSDC")
    last_bybit = round(float(prices['lastPrice']), 2)
    bid_bybit = round(float(prices['bidPrice']), 2)
    ask_bybit = round(float(prices['askPrice']), 2)
    # print(f"(Last): {last_bybit}")
    # print(f"(Bid): {bid_bybit}")
    # print(f"(Ask): {ask_bybit}")

    print(i)

    prices = utils_aux.get_binance_prices("ETHUSDC")
    last_binance = round(float(prices['lastPrice']), 2)
    bid_binance = round(float(prices['bidPrice']), 2)
    ask_binance = round(float(prices['askPrice']), 2)
    # print(f"(Last): {last_binance}")
    # print(f"(Bid): {bid_binance}")
    # print(f"(Ask): {ask_binance}")

    # Cross
    data_to_db[0] = last_bybit
    data_to_db[1] = bid_bybit
    data_to_db[2] = ask_bybit
    data_to_db[3] = last_binance
    data_to_db[4] = bid_binance
    data_to_db[5] = ask_binance

    utils_aux.log_data(data_to_db, cursor, dbconn)

    i += 1