from web3 import Web3
import requests
import time
import sqlite3
from datetime import datetime, timedelta
import config as cnf
import utils_chain
import utils_uniswap as uni
import utils_aux


db_name = 'prices.db'
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
stat_fast_ans = 0
stat_slow_ans = 0

while True:
    try: 
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "ETHUSDT"}
        start_time = time.time()
        response = requests.get(url, params=params)
        end_time = time.time()
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error Binance: {response.status_code}, {response.text}")
        cex_price = float(data['price'])
        t_cex_price = end_time - start_time


        #print(data_to_db[0])
        # # Get balances
        # usdc_pol_abi = chain_utils.load_abi("polygon/usdc.json")
        # usdc_pol_adr = config.usdc_token_polygon
        # usdc_pol_ctr = poly_conn.eth.contract(address=usdc_pol_adr, abi=usdc_pol_abi)
        # chain_utils.get_balance_token(usdc_pol_ctr, config.test_address)
        # chain_utils.get_balance_native(poly_conn, config.test_address)
        # print()
        #print('WETH/USDT 0.3%')

        teo_price_03, t_teo_price_03 = uni.get_pool_teo_price_inv(cnf.pool_3_contract)
        buy_price_03, t_buy_price_03 = uni.get_pool_price_usdtoeth(4000, cnf.quoter_contract, cnf.usd_token, cnf.eth_token, 3000)
        sell_price_03, t_sell_price_03 = uni.get_pool_price_ethtousd(1, cnf.quoter_contract, cnf.chain_conn, cnf.eth_token, cnf.usd_token, 3000)

        teo_price_005, t_teo_price_005 = uni.get_pool_teo_price_inv(cnf.pool_5_contract)
        buy_price_005, t_buy_price_005 = uni.get_pool_price_usdtoeth(4000, cnf.quoter_contract, cnf.usd_token, cnf.eth_token, 500)
        sell_price_005, t_sell_price_005 = uni.get_pool_price_ethtousd(1, cnf.quoter_contract, cnf.chain_conn, cnf.eth_token, cnf.usd_token, 500)

        tick_value_005, liq_com_005, liq_tick_005 = uni.get_analyse_data(cnf.pool_5_contract)
        token0_tvl_005 = utils_chain.get_balance_token(cnf.eth_contract, cnf.pool_5_address)
        token1_tvl_005 = utils_chain.get_balance_token(cnf.usd_contract, cnf.pool_5_address)

        if t_cex_price > 1 or t_buy_price_03 > 1 or t_sell_price_03 > 1 or t_buy_price_005 > 1 or t_sell_price_005 > 1:
            stat_slow_ans += 1
            print(stat_slow_ans/(stat_fast_ans+stat_slow_ans)*100, '%  timeouts, slow / fast', stat_slow_ans, stat_fast_ans)
        else:
            stat_fast_ans += 1

        # Cross
        data_to_db[0] = cex_price
        data_to_db[1] = buy_price_03
        data_to_db[2] = sell_price_03
        data_to_db[3] = buy_price_005
        data_to_db[4] = sell_price_005
        data_to_db[10] = teo_price_03
        data_to_db[11] = teo_price_005
        # new part
        data_to_db[5] = tick_value_005
        data_to_db[6] = token0_tvl_005
        data_to_db[7] = token1_tvl_005
        data_to_db[8] = liq_com_005
        data_to_db[9] = liq_tick_005

        utils_aux.log_data(data_to_db, cursor, dbconn)

        #time.sleep(4)

    except KeyboardInterrupt:
        break
    # except Exception as e:
    #     print(f"Error: {e}")
    
# Закрытие соединения
dbconn.close()

# to do
# prices from router
# price from cex


# ===================================================================

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
