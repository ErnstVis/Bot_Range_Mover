from web3 import Web3
import requests
import time
import sqlite3
from datetime import datetime, timedelta
import config as cnf
import utils_chain
import utils_uniswap as uni
import utils_aux
# import eth_defi


# Get balances
tokenA_blnc = utils_chain.get_balance_token(cnf.usd_contract, cnf.test_address)
tokenB_blnc = utils_chain.get_balance_token(cnf.eth_contract, cnf.test_address)
native_blnc = utils_chain.get_balance_native(cnf.chain_conn, cnf.test_address)
teo_price_005, t_teo_price_005 = uni.get_pool_teo_price_inv(cnf.pool_5_contract)
average_price = teo_price_005
m_teo_price_005 = teo_price_005
i = 0
j = 0
bl = 0
print(teo_price_005, average_price, i, tokenA_blnc, tokenB_blnc, native_blnc, bl, t_teo_price_005)
while i < 5:
    teo_price_005, t_teo_price_005 = uni.get_pool_teo_price_inv(cnf.pool_5_contract)
    if teo_price_005 != m_teo_price_005:
        print(teo_price_005, average_price, i, tokenA_blnc, tokenB_blnc, native_blnc, bl, t_teo_price_005)
        m_teo_price_005 = teo_price_005
    if teo_price_005 < average_price - 30 and tokenA_blnc > 0.01 and bl >= 100: 
        # USD to ETH                            tokenA_blnc/(teo_price_005+10)
        uni.swap_token_router(tokenA_blnc, cnf.chain_conn, 0, 10, cnf.router_contract, cnf.usd_token, cnf.eth_token, 500, cnf.usd_contract, cnf.eth_contract, cnf.test_address, cnf.private_key)
        bl = 0
        i += 1
        if j >= 1:
            average_price = average_price * 0.95 + teo_price_005 * 0.05
        j += 1
    elif teo_price_005 > average_price + 30 and tokenB_blnc > 0.00001 and bl >= 100: 
        # ETH to USD                            tokenB_blnc*(teo_price_005-10)
        uni.swap_token_router(tokenB_blnc, cnf.chain_conn, 0, 10, cnf.router_contract, cnf.eth_token, cnf.usd_token, 500, cnf.eth_contract, cnf.usd_contract, cnf.test_address, cnf.private_key)
        bl = 0
        i += 1
        if j >= 1:
            average_price = average_price * 0.95 + teo_price_005 * 0.05
        j += 1
    else:
        average_price = average_price * 0.95 + teo_price_005 * 0.05
        j = 0
        bl += 1
    if bl == 100:
        tokenA_blnc = utils_chain.get_balance_token(cnf.usd_contract, cnf.test_address)
        tokenB_blnc = utils_chain.get_balance_token(cnf.eth_contract, cnf.test_address)
        native_blnc = utils_chain.get_balance_native(cnf.chain_conn, cnf.test_address)
    



