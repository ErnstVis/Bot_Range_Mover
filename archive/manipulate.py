import pybit.market
from web3 import Web3
import math
import requests
import time
import sqlite3
from datetime import datetime, timedelta
import config as cnf
import utils_chain
import utils_uniswap as uni
import utils_aux
import json
# import eth_defi
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

# =======================================================================================================================
# ============================================== Test Bybit api =========================================================

# BYBIT_API_KEY = cnf.bybit_api
# BYBIT_API_SECRET = cnf.bybit_key
# TESTNET = False  # True means your API keys were generated on testnet.bybit.com

# # Create direct HTTP session instance
# session = HTTP(
#     api_key=BYBIT_API_KEY,
#     api_secret=BYBIT_API_SECRET,
#     testnet=TESTNET,
# )

# symbol = "ETHUSDC"
# response = session.get_tickers(category="spot", symbol=symbol)
# # Извлекаем данные из ответа
# if response["retCode"] == 0:  # Успешный запрос
#     ticker_data = response["result"]["list"][0]
#     price = ticker_data["lastPrice"]  # Последняя цена
#     print(f"Price {symbol}: {price} USDC")
# else:
#     print(f"Error: {response['retMsg']}")
# # prices = utils_aux.get_bybit_prices("ETHUSDC")
# # last_bybit = round(float(prices['lastPrice']), 2)
# # bid_bybit = round(float(prices['bidPrice']), 2)
# # ask_bybit = round(float(prices['askPrice']), 2)


# x = session.get_wallet_balance(accountType="UNIFIED")
# tokens = x["result"]["list"][0]["coin"]
# def get_token_balance(token_name):
#     for token in tokens:
#         if token["coin"] == token_name:
#             return token["walletBalance"]
#     return "Token not found"

# # eth_balance = get_token_balance("ETH")
# # print(f"ETH: {eth_balance}")
# usdc_balance = get_token_balance("USDC")
# print(f"USDC: {usdc_balance}")

# amount_to_spend = float(usdc_balance) * 0.995  # Оставляем 1% как запас
# quantity = round(amount_to_spend / float(price), 6)  # Рассчитываем количество ETH
# print(f"ETH to buy: {quantity}")

# order_response = session.place_order(
#     category="spot",       # Тип рынка
#     symbol="ETHUSDC",         # Пара
#     side="Buy",            # Покупка
#     orderType="Market",    # Рыночный ордер
#     qty=quantity           # Количество ETH
# )

# if order_response["retCode"] == 0:
#     print("Done!")
#     print(order_response)
# else:
#     print("Error:", order_response["retMsg"])

# exit()
# =======================================================================================================================
# ============================================== Test Binance api =======================================================

# Введите свои ключи API
BINANCE_API_KEY = cnf.binance_api
BINANCE_API_SECRET = cnf.binance_key
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

# Шаг 1: Получить текущую рыночную цену ETH/USDC
symbol = "ETHUSDC"
ticker = client.get_ticker(symbol=symbol)
price = float(ticker["lastPrice"])  # Последняя цена
print(f"ETH/USDC: {price} USDC")

# Шаг 2: Рассчитать количество ETH для покупки
# usdc_balance = float(client.get_asset_balance(asset="USDC")["free"])  # Получить доступный баланс USDC
# print('Balance USDC:', usdc_balance)
# amount_to_spend = round(usdc_balance * 0.995, 2)  # Оставляем 1% как запас
# print('USDC:', amount_to_spend)
# quantity = round(amount_to_spend / price, 6)  # Рассчитываем количество ETH
# print(f"ETH for buy: {quantity}")

# Шаг 2: Рассчитать количество ETH для покупки
eth_balance = float(client.get_asset_balance(asset="ETH")["free"])
print('Balance ETH:', eth_balance)
amount_to_spend = math.floor(eth_balance * 100000) / 100000
print('ETH to spend:', amount_to_spend)
quantity = round(amount_to_spend * price, 2)
print(f"USD for buy: {quantity}")

# info = client.get_symbol_info('ETHUSDC')
# print(info['filters'])

# Шаг 3: Отправить рыночный ордер
try:
    order = client.create_order(
        symbol = symbol,
        side = SIDE_SELL,
        type = ORDER_TYPE_MARKET,
        quoteOrderQty = quantity
    )
    print("Done!", order)
except Exception as e:
    print("Error:", e)

# =======================================================================================================================



exit()
# Get balances
balance0 = utils_chain.get_balance_token(cnf.usd_contract, cnf.test_address)
balance1 = utils_chain.get_balance_token(cnf.eth_contract, cnf.test_address)

print(balance0, 'usd')
print(balance1, 'eth')

print(utils_chain.get_balance_native(cnf.chain_conn, cnf.test_address), 'matic')
print()



# approve_tx = utils_chain.approve_token(2**256 - 1, cnf.chain_conn, cnf.usd_contract, cnf.test_address, cnf.pool_5_address, cnf.private_key)
# print('Token 0:', cnf.pool_5_contract.functions.token0().call())
# print('Token 1:', cnf.pool_5_contract.functions.token1().call())



# allowance = cnf.usd_contract.functions.allowance(cnf.test_address, cnf.pool_5_address).call()
# print(f"Allowance: {allowance}")


pool_price, x = uni.get_pool_teo_price_inv(cnf.pool_5_contract)
amount1_test = balance0 / pool_price
amount0_test = balance1 * pool_price
amount1_fee_buy = balance0 / pool_price * 0.9993
amount0_fee_sell = balance1 * pool_price * 0.9993
print(pool_price, '        ', amount1_test, amount1_fee_buy, '        ', amount0_test, amount0_fee_sell)
# price_1 = price_fee_inc / 10**(18-6)
# price_2 = 1 / price_1
# price96 = ((price_2**0.5) * 2**96)
# print(pool_price, price_1, price_2, int(price96))


# USD to ETH
#uni.swap_token_router(balance0, cnf.chain_conn, amount1_fee_buy, 60, cnf.router_contract, cnf.usd_token, cnf.eth_token, 500, cnf.usd_contract, cnf.eth_contract, cnf.test_address, cnf.private_key)

# ETH to USD
#uni.swap_token_router(balance1, cnf.chain_conn, amount0_fee_sell, 60, cnf.router_contract, cnf.eth_token, cnf.usd_token, 500, cnf.eth_contract, cnf.usd_contract, cnf.test_address, cnf.private_key)



# tx_hash = uni.swap_token(0.5, cnf.chain_conn, int(price96), cnf.pool_5_contract, cnf.usd_contract, cnf.eth_contract, cnf.test_address, cnf.private_key)
# receipt = cnf.chain_conn.eth.wait_for_transaction_receipt(tx_hash)
# print(receipt)

# exit()
# print('pay!!!')

# amount_usd = 0.05           #USDC
# tx_hash = chain_utils.send_token(amount_usd, poly_conn, usdc_pol_ctr, config.test_address, config.main_address, config.private_key)
# receipt = poly_conn.eth.wait_for_transaction_receipt(tx_hash)
# print("Transaction confirmed!")

# amount_native = 0.01        #POL
# tx_hash = chain_utils.send_native(amount_native, poly_conn, config.test_address, config.main_address, config.private_key)
# receipt = poly_conn.eth.wait_for_transaction_receipt(tx_hash)
# print("Transaction confirmed!")
