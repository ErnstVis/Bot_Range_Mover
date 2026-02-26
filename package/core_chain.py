from dotenv import load_dotenv
from web3 import Web3, AsyncWeb3
from web3.exceptions import TimeExhausted
from web3.providers.persistent import WebSocketProvider, AsyncIPCProvider
from web3.exceptions import Web3Exception, TimeExhausted, BadResponseFormat, ContractLogicError, Web3RPCError
import requests
import time
import os
import math
import json
from datetime import datetime, timezone
import random
import sys
import matplotlib.pyplot as plt
from collections import deque
import numpy as np
import asyncio
from asyncio.exceptions import IncompleteReadError
import websockets
from websockets.exceptions import ConnectionClosedError

sys.stdout.reconfigure(encoding="utf-8")


class ChainLink2:
    def __init__(self, blockchain, proto):





        if blockchain == 'arbitrum':                                        # open chain config file
            path = 'config/addresses/arbitrum.json'
            self.gas_limit = 0.15
        elif blockchain == 'polygon':
            path = 'config/addresses/polygon.json'
            self.gas_limit = 1500
        elif blockchain == 'optimism':
            path = 'config/addresses/optimism.json'
        elif blockchain == 'mainnet':
            path = 'config/addresses/mainnet.json'
            self.gas_limit = 0.15
        with open(path, 'r') as f:
            params = json.load(f)
        self.tokens = params.get("tokens", {})      # get tokens dict, order is important
        for key, value in params.items():
            if key != "tokens":
                setattr(self, key, value)

        with open("config/abi/token.json", "r") as f:
            self.abi_token = json.load(f)
        if proto == 'uni3':                                              # set protocol addresses and abi
            self.address_factory = self.uniswap_factory
            self.address_router = self.uniswap_router
            self.address_quoter = self.uniswap_quoter
            self.address_manager = self.uniswap_manager
            with open("config/abi/uniswap_factory.json", "r") as f:
                self.abi_factory = json.load(f)
            with open("config/abi/uniswap_router.json", "r") as f:
                self.abi_router = json.load(f)
            with open("config/abi/uniswap_quoter.json", "r") as f:
                self.abi_quoter = json.load(f)
            with open("config/abi/uniswap_manager.json", "r") as f:
                self.abi_manager = json.load(f)
            with open("config/abi/uniswap_pool.json", "r") as f:
                self.abi_pool = json.load(f)            
            with open("config/abi/special.json", "r") as f:
                self.abi_special = json.load(f)
        else:
            print('Protocol not supported')
            return
        load_dotenv("private/secrets.env")                                          # set wallet
        self.address_withdraw = os.getenv("MAIN_ADR")
        self.address_wallet = os.getenv("WORK_ADR")
        self.key_wallet = os.getenv("WORK_KEY")
        self.key_rpc = os.getenv("INFURA_API")
        self.connection = Web3(Web3.HTTPProvider(self.rpc + self.key_rpc))          # connect to node
        if self.connection.is_connected():
            print("Connected!")
        else:
            print("Not connected!")
            return
        print('Address my:', self.address_wallet)

        # ETH_RPC = "https://mainnet.infura.io/v3/" + self.key_rpc
        # w3_eth = Web3(Web3.HTTPProvider(ETH_RPC))
        # self.reth_contract = w3_eth.eth.contract(address="0xae78736Cd615f374D3085123A210448E74Fc6393", abi=self.abi_special)
        # self.wsteth_contract = w3_eth.eth.contract(address="0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0", abi=self.abi_special)

        self.tokens_short = {
            "ETH": self.tokens["ETH"],
            "weETH": self.tokens["weETH"],
            "rETH": self.tokens["rETH"],
            "wstETH": self.tokens["wstETH"],
        }

        self.contract_factory = self.connection.eth.contract(address=self.address_factory, abi=self.abi_factory)
        self.contract_router = self.connection.eth.contract(address=self.address_router, abi=self.abi_router)
        self.contract_quoter = self.connection.eth.contract(address=self.address_quoter, abi=self.abi_quoter)
        self.contract_manager = self.connection.eth.contract(address=self.address_manager, abi=self.abi_manager)

        self.chain_id = self.connection.eth.chain_id

        self.tokens_data = {}
        self.pools = {}
        
        self.pools_data = {}
        self.combinations_starts = 0



    ''' ASYNC FNS '''

    async def listener(self, key, value):
        addr = value["address"]
        dec0 = self.tokens_data[key[0]]["decimals"]
        dec1 = self.tokens_data[key[1]]["decimals"]
        sym0 = self.tokens_data[key[0]]["cex_name"]
        sym1 = self.tokens_data[key[1]]["cex_name"]
        fee = str(key[2])
        while True:
            try:
                async with AsyncWeb3(
                    WebSocketProvider(self.rpcws + self.key_rpc)
                ) as w3:
                    pool = w3.eth.contract(address=addr, abi=self.abi_pool)
                    await w3.eth.subscribe(
                        "logs",
                        {"address": addr}
                    )
                    async for msg in w3.socket.process_subscriptions():
                        log = msg.get("result")
                        if not log:
                            continue
                        ts = datetime.now()
                        try:
                            event = pool.events.Swap().process_log(log)                    
                            a0 = event["args"]["amount0"] / 10**dec0
                            a1 = event["args"]["amount1"] / 10**dec1
                            sqrt_price = event["args"]["sqrtPriceX96"]
                            dex_price = ( (sqrt_price / 2**96) ** 2 * 10**dec0 / 10**dec1 )
                            swap_price = abs(a1 / a0) if a0 and a1 else 0
                            print(
                                f"[{ts}]\t {sym0} / {sym1} / {fee} "
                                f"\ta0= {a0:.6f} \ta1= {a1:.6f} "
                                f"\tswap price= {swap_price:.5f}"
                                f"\tact price= {dex_price:.5f}")

                                                                    # test part
                            await asyncio.to_thread(
                                self.check_fast_data(key, value, a0, a1, swap_price, dex_price))
                            
                            continue
                        except:
                            pass
                        try:
                            event = pool.events.Mint().process_log(log)
                            a0 = event["args"]["amount0"] / 10**dec0
                            a1 = event["args"]["amount1"] / 10**dec1
                            args = event["args"]
                            print(
                                f"MINT "
                                f"[{ts}]\t {sym0} / {sym1} / {fee} "
                                f"range=[{args['tickLower']}, {args['tickUpper']}] "
                                f"liq={args['amount']} "
                                f"\ta0={a0:.6f} \ta1={a1:.6f} "
                            )
                            continue
                        except:
                            pass
                        try:
                            event = pool.events.Burn().process_log(log)
                            a0 = event["args"]["amount0"] / 10**dec0
                            a1 = event["args"]["amount1"] / 10**dec1
                            args = event["args"]
                            print(
                                f"BURN "
                                f"[{ts}]\t {sym0} / {sym1} / {fee} "
                                f"range=[{args['tickLower']}, {args['tickUpper']}] "
                                f"liq={args['amount']} "
                                f"\ta0={a0:.6f} \ta1={a1:.6f} "
                            )
                            continue
                        except:
                            pass
            except (
                asyncio.IncompleteReadError,
                websockets.exceptions.ConnectionClosedError,
                ConnectionError,
            ) as e:
                print(f"[WS] {sym0} / {sym1} / {fee} reconnect:", e)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[FATAL] listener {sym0} / {sym1} / {fee}:", e)
                await asyncio.sleep(5)




    def check_fast_data(self, key, value, a0, a1, swap_price, dex_price):
        addr = value["address"]
        dec0 = self.tokens_data[key[0]]["decimals"]
        dec1 = self.tokens_data[key[1]]["decimals"]
        sym0 = self.tokens_data[key[0]]["cex_name"]
        sym1 = self.tokens_data[key[1]]["cex_name"]
        fee = str(key[2])
        # dex_price = self.get_slot_data(value["contract"], dec0, dec1)[0]                      # same from swap result
        # get_swap_ammount_quoter(cls, quoter_cntr, token_in, token_out, dec_in, dec_out, fee, amount, exact='I')

        # test back swap!
        if swap_price > dex_price * 1.001 or swap_price < dex_price * 0.999:
            print(f"Price delta detected!")

        
        if a0 > a1:
            amm_in = abs(a1)
            amm_out = self.get_swap_ammount_quoter(self.contract_quoter, 
                key[1], key[0], dec1, dec0, key[2], amm_in)
        else:
            amm_in = abs(a0)
            amm_out = self.get_swap_ammount_quoter(self.contract_quoter, 
                key[0], key[1], dec0, dec1, key[2], amm_in)
        print(f"Quoter back swap ammouns. IN {amm_in:.6f}\tOUT {amm_out:.6f}\tPrice {amm_out/amm_in:.5f}")


        balance0 = self.get_balance_token(self.tokens_data[key[0]]["contract"], value["address"], dec0)
        balance1 = self.get_balance_token(self.tokens_data[key[1]]["contract"], value["address"], dec1)
        print(f"New data - balance0: {balance0:.3f} | balance1: {balance1:.3f}")
        pass







    ''' ROUTINE FNS '''

    def scan_tokens(self, short=False):
        if short:
            self.tokens = self.tokens_short
        self.token_list = list(self.tokens.keys())

        print("\nFilling tokens data...\n", "="*25)
        for key, value in self.tokens.items():
            token_contract = self.connection.eth.contract(address=value, abi=self.abi_token)
            decimals = token_contract.functions.decimals().call()
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            print("Token", value, name, symbol, 'decimals:', decimals)
            self.tokens_data[value] = {
                "contract": token_contract,
                "decimals": decimals,
                "name": name,
                "symbol": symbol,
                "cex_name": key,}

    def scan_pools(self):
        self.pools_fee = [100, 500, 3000, 10000]
        print("\nAdding pools...\n", "="*25)
        for i in range(len(self.token_list)):
            for j in range(max(i + 1, self.combinations_starts), len(self.token_list)):
                token0 = self.token_list[j]
                token1 = self.token_list[i]
                t0 = self.tokens[token0]
                t1 = self.tokens[token1]
                for fee in self.pools_fee:
                    # self.scan_pool(t0, t1, fee)
                    pool_address = self.contract_factory.functions.getPool(t0, t1, fee).call()
                    if pool_address == "0x0000000000000000000000000000000000000000":
                        print('Pool', self.tokens_data[t0]["cex_name"], 
                        self.tokens_data[t1]["cex_name"], 
                        fee, '- not initiated')
                        continue
                    pool_contract = self.connection.eth.contract(address=pool_address, abi=self.abi_pool)
                    tick_spacing = pool_contract.functions.tickSpacing().call()
                    # check 0/1 order
                    addr0 = pool_contract.functions.token0().call()
                    addr1 = pool_contract.functions.token1().call()
                    if addr0.lower() == t0.lower() and addr1.lower() == t1.lower():
                        pool_reversed = False
                    else:
                        pool_reversed = True
                    key = (addr0, addr1, fee)
                    if key in self.pools_data: 
                        print('Pool', self.tokens_data[addr0]["cex_name"], 
                        self.tokens_data[addr1]["cex_name"], 
                        fee, '- alredy listed')
                        continue
                    self.pools_data[key] = {
                        "address": pool_address,
                        "contract": pool_contract,
                        "spacing": tick_spacing,
                        "reversed": pool_reversed,
                        "cex_price0": deque([0] * 400, maxlen=400),
                        "cex_price1": deque([0] * 400, maxlen=400),
                        "dex_price": deque([0] * 400, maxlen=400),
                        "liquidity": deque([0] * 400, maxlen=400),
                        "gross0": deque([0] * 400, maxlen=400),
                        "gross1": deque([0] * 400, maxlen=400),
                        "balance0": deque([0] * 400, maxlen=400),
                        "balance1": deque([0] * 400, maxlen=400),}
                    print('Pool', self.tokens_data[addr0]["cex_name"], 
                        self.tokens_data[addr1]["cex_name"], 
                        fee, pool_address, 'added. Spacing:', tick_spacing)

        print(f"\nTotal pools added: {len(self.pools_data)}\n")

    def get_token_reference_price(self, name):

        def get_from_binance(sym, retries=3):
            pair = sym + 'USDC'
            url = "https://api.binance.com/api/v3/ticker/bookTicker"
            params = {"symbol": pair}
            for attempt in range(retries):
                try:
                    r = requests.get(url, params=params, timeout=5)
                    r.raise_for_status()
                    data = r.json()
                    bid = float(data["bidPrice"])
                    ask = float(data["askPrice"])
                    return (bid + ask) / 2
                except requests.exceptions.RequestException as e:
                    print(f"[Binance retry {attempt+1}] {pair}: {e}")
                    time.sleep(5)
            return 0

        # def get_proto_nominal_reth():
        #     reth_rate_raw = self.reth_contract.functions.getExchangeRate().call()
        #     reth_rate = reth_rate_raw / 10 ** self.tokens_data[self.tokens[name]]["decimals"]
        #     return reth_rate
        # def get_proto_nominal_wsteth():
        #     wsteth_rate_raw = self.wsteth_contract.functions.stEthPerToken().call()
        #     wsteth_rate = wsteth_rate_raw / 10 ** self.tokens_data[self.tokens[name]]["decimals"]
        #     return wsteth_rate
        
        if (name == 'USDC' or
            name == 'USDT' or
            name == 'USDCe' or
            name == 'DAI' or
            name == 'MAI' or
            name == 'AxlUSDC' or
            name == 'GHST' or
            name == 'FRAX' or
            name == 'frxUSD' or
            name == 'sfrxUSD' or
            name == 'LUSD' or
            name == 'crvUSD'):
            result = 1.0
        elif name == 'wETH':
            result = get_from_binance("ETH")
        elif name == 'rETH':
            step1 = get_from_binance("ETH")
            # step2 = get_proto_nominal_reth()
            result = step1 * 1.111
        elif name == 'wstETH':
            step1 = get_from_binance("ETH")
            # step2 = get_proto_nominal_wsteth()
            result = step1 * 1.226
        elif name == 'weETH':
            step1 = get_from_binance("ETH")
            # step2 = get_proto_nominal_reth()
            result = step1 * 1.111
        elif name == 'sfrxETH':
            step1 = get_from_binance("ETH")
            # step2 = get_proto_nominal_reth()
            result = step1 * 1.111
        else:
            result = get_from_binance(name)

        self.tokens_data[self.tokens[name]]["cex_price"] = result
        return result

    def scan_pool_statistic(self, interval_h, print_flag=False, use=''):
        dust_arbitrage_pools = {}
        active_trade_pools = {}
        if use == 'Dust':
            pools = self.dust_arbitrage_pools.copy()
        elif use == 'Work':
            pools = self.active_trade_pools.copy()
        else:
            pools = self.pools_data.copy()
        for key, value in pools.items():

            # fill part
            dec0 = self.tokens_data[key[0]]["decimals"]
            dec1 = self.tokens_data[key[1]]["decimals"]
            token0_cex_price = self.get_token_reference_price(self.tokens_data[key[0]]["cex_name"])
            token1_cex_price = self.get_token_reference_price(self.tokens_data[key[1]]["cex_name"])
            dex_price = self.get_slot_data(value["contract"], dec0, dec1)[0]
            value["cex_price0"].append(token0_cex_price)
            value["cex_price1"].append(token1_cex_price)
            value["dex_price"].append(dex_price)
            liqid, gross0, gross1 = self.get_liquidity(value["contract"], dec0, dec1)            
            value["liquidity"].append(liqid)
            value["gross0"].append(gross0)
            value["gross1"].append(gross1)
            balance0 = self.get_balance_token(self.tokens_data[key[0]]["contract"], value["address"], dec0)
            balance1 = self.get_balance_token(self.tokens_data[key[1]]["contract"], value["address"], dec1)
            value["balance0"].append(balance0)
            value["balance1"].append(balance1)

            # log part
            balance0_usd = balance0 * token0_cex_price
            balance1_usd = balance1 * token1_cex_price
            balance_pool = balance0_usd + balance1_usd
            gross0_d = value["gross0"][-1] - value["gross0"][-2] if value["gross0"][-2] else 0
            gross1_d = value["gross1"][-1] - value["gross1"][-2] if value["gross1"][-2] else 0
            gross0_abs_d = gross0_d * liqid
            gross1_abs_d = gross1_d * liqid
            gross0_usd = gross0_abs_d * token0_cex_price
            gross1_usd = gross1_abs_d * token1_cex_price
            gross_usd = gross0_usd + gross1_usd
            gross_rel = (gross_usd / balance_pool * 100 * (24 / interval_h) * 365) if balance_pool > 5 else 0
            sym0 = self.tokens_data[key[0]]["cex_name"]
            sym1 = self.tokens_data[key[1]]["cex_name"]
            fee = key[2]                                          # filter value for show
            cex_price = token0_cex_price / token1_cex_price
            price_delta = (dex_price - cex_price) / cex_price * 100 if cex_price != 0 else 0
            if value["reversed"]:
                dex_price_w = 1 / dex_price if dex_price > 0 else 0
                cex_price_w = 1 / cex_price if cex_price > 0 else 0
                rev_flag = '!'
            else:
                dex_price_w = dex_price
                cex_price_w = cex_price
                rev_flag = ' '
            if price_delta > 1000: price_delta = 1000   
            if dex_price_w > 10**7: dex_price_w = 0   
            if balance_pool < 3 or liqid < 100:
                x = 'empty'
            elif balance_pool < 15000:
                x = '_SMALL'
                dust_arbitrage_pools[key] = value
            else:
                x = '_ACTIVE'
                active_trade_pools[key] = value
            print(f"{sym0:<7}{sym1:<7}{fee:<5}{rev_flag} | "
                f"PrC{cex_price_w:>14.5f} | "
                f"PrD{dex_price_w:>14.5f} | "
                f"Dlt{price_delta:>8.2f} | "
                f"Bl0{balance0_usd:>12.2f} | "
                f"Bl1{balance1_usd:>12.2f} | "
                f"APY {gross_rel:>8.1f} | "
                f"{x} | Liq{liqid:>10.1f}"
                f"Bl0row:{balance0:>10.3f} Bl1row:{balance1:>10.3f}")

            # plot part
            if print_flag:
                dp_list = []
                cp_list = []
                b0_list = []
                b1_list = []
                apr_list = []
                metric1_max_list = []
                metric1_min_list = []
                metric2_max_list = []
                metric2_min_list = []
                metric2_max_list = []
                metric3_max_list = []
                metric3_min_list = []

     
     
                horizon = window = 24
                k = 2.5
                width_list = []
                drift_list = []
                dp_avr_add = self.make_avg(horizon)
                prices_np = np.array(value["dex_price"])        # part for get vola moving values
                for i in range(window, len(prices_np)):
                    chunk = prices_np[i-window:i]               # how long is past window
                    if np.any(chunk <= 0):
                        width_list.append(0)
                        drift_list.append(0)
                        continue
                    returns = np.diff(np.log(chunk))
                    mu = np.mean(returns)
                    sigma = np.std(returns)
                    drift = (mu / (sigma + 1e-8)) * (np.cbrt(horizon))         # relative with zero devision protect
                    drift_norm = np.tanh(drift)
                    width_pct = k * (sigma ** (2/3)) * (np.cbrt(horizon)) 
                    width_list.append(width_pct)
                    drift_list.append(drift_norm)


                gross0 = list(value["gross0"])
                gross1 = list(value["gross1"])
                gr_avrg = None
                for cp0, cp1, dp, l, g0, g0p, g1, g1p, b0, b1, wdh, drf in zip(
                        value["cex_price0"], value["cex_price1"], value["dex_price"], value["liquidity"], 
                        gross0, [0] + gross0[:-1], gross1, [0] + gross1[:-1], value["balance0"], value["balance1"], 
                        [0] * window + [0] + width_list, [0] * window + [0] + drift_list):
                    cp = cp0 / cp1 if cp1 > 0 else 0
                    if value["reversed"]:
                        dpw = 1 / dp if dp > 0 else 0
                        cpw = 1 / cp if cp > 0 else 0
                    else:
                        dpw = dp
                        cpw = cp
                    dp_list.append(dpw)
                    cp_list.append(cpw)         # prices add
                    b0u = b0 * cp0
                    b1u = b1 * cp1
                    bu = b0u + b1u
                    b0_list.append(b0u)
                    b1_list.append(b1u)         # balances add
                    g0d = g0 - g0p if g0 and g0p else 0
                    g1d = g1 - g1p if g1 and g1p else 0
                    g0a = g0d * l
                    g1a = g1d * l
                    g0u = g0a * cp0
                    g1u = g1a * cp1
                    gu = g0u + g1u
                    gr = (gu / bu * 100 * (24 / interval_h) * 365) if bu and interval_h else 0
                    if gr < 0 or gr > 200:
                        print('debug' + str(gr) + " | " + str(g0) + " | " + str(g1) + " | " + str(g0p) + " | " + str(g1p) + " | " + str(l))
                    gr_avrg = self.sma_calc(gr_avrg, gr, 7)
                    apr_list.append(gr_avrg)         # apr add
                    
                    # Experemental metrics for future use - Metric group 1
                    liq_scaled = l / 10**(abs(dec0 - dec1)) if dec0 and dec1 else 0
                    s_p = math.sqrt(dpw) if dpw > 0 else 0
                    bal0_norm = b0 * dpw
                    bal1_norm = b1
                    bal_total = bal0_norm + bal1_norm
                    bal_not_in_use = bal0_norm - bal1_norm
                    bal_working = min(bal0_norm, bal1_norm) * 2
                    bal0_working = (bal_working / 2) / dpw if dpw > 0 else 0
                    bal1_working = (bal_working / 2) if dpw > 0 else 0
                    range1_offset = bal_not_in_use / bal_total if bal_total else 0              # calculation inputs prepared
                    s_p_min = s_p - bal1_working / liq_scaled if liq_scaled else 0              # L formula for price range borders with working balance and liquidity
                    s_p_max = (liq_scaled * s_p) / (liq_scaled - bal0_working * s_p) if liq_scaled and (liq_scaled - bal0_working * s_p) else 0
                    s_delta1 = s_p_max - s_p_min                                                 # final values preparating
                    s_p1_max_new = (s_p + s_delta1 * 0.5) + s_delta1 * 0.5 * range1_offset
                    s_p1_min_new = (s_p - s_delta1 * 0.5) + s_delta1 * 0.5 * range1_offset
                    metric1_teo_max = s_p1_max_new ** 2
                    metric1_teo_min = s_p1_min_new ** 2
                    metric1_max_list.append(metric1_teo_max)
                    metric1_min_list.append(metric1_teo_min)
                    
                    # Experemental metrics for future use - Metric group 2
                    s_delta2 = (s_p * b0 + b1) / liq_scaled if liq_scaled else 0
                    s_p2_max_new = s_p + s_delta2 * 0.5                 # + s_delta * 0.5 * range1_offset
                    s_p2_min_new = s_p - s_delta2 * 0.5                 # + s_delta * 0.5 * range1_offset
                    metric2_teo_max = s_p2_max_new ** 2
                    metric2_teo_min = s_p2_min_new ** 2
                    metric2_max_list.append(metric2_teo_max)
                    metric2_min_list.append(metric2_teo_min)

                    # Experemental metrics for future use - Metric group 3
                    if dpw > 0:
                        dp_avr = dp_avr_add(dpw)
                    else:
                        dp_avr = 0
                    center_shift = drf * wdh
                    up_log = wdh + center_shift
                    down_log = wdh - center_shift
                    metric3_teo_max = dp_avr * np.exp(up_log)
                    metric3_teo_min = dp_avr * np.exp(-down_log)
                    metric3_max_list.append(metric3_teo_max)
                    metric3_min_list.append(metric3_teo_min)




                # ===== PLOT =====
                x = range(len(dp_list))  # итерации
                plt.style.use("dark_background")
                fig, ax1 = plt.subplots(figsize=(18, 12))
                # ===== AXIS 1: Prices =====
                ax1.plot(x, dp_list, color="#22C049FF", label="DEX price", linewidth=1.5)
                ax1.plot(x, cp_list, color="#22C049FF", label="CEX price", linewidth=1.2, linestyle='--')
                ax1.plot(x, metric1_max_list, color="#FBFF1BFF", label="Teo range 1", linewidth=1.2, linestyle=':')
                ax1.plot(x, metric1_min_list, color="#FBFF1BFF", linewidth=1.2, linestyle=':')
                ax1.plot(x, metric2_max_list, color="#DDB500FF", label="Teo range 2", linewidth=1.2, linestyle=':')
                ax1.plot(x, metric2_min_list, color="#DDB500FF", linewidth=1.2, linestyle=':')
                ax1.plot(x, metric3_max_list, color="#FF6030FF", label="Teo range 3", linewidth=1.2, linestyle=':')
                ax1.plot(x, metric3_min_list, color="#FF6030FF", linewidth=1.2, linestyle=':')
                ax1.set_ylabel("Price")
                ax1.set_xlim(0, len(dp_list))
                ax1.grid(True, linestyle="--", alpha=0.25)
                ax1.spines["top"].set_visible(False)
                ax1.spines["right"].set_visible(False)
                # ===== AXIS 2: APR =====
                ax2 = ax1.twinx()
                ax2.plot(x, apr_list, color="#1DD7DD7D", linewidth=1, label="APR")
                ax2.set_ylim(0, 200)
                ax2.set_yticks([])
                ax2.set_ylabel("")
                ax2.spines["right"].set_visible(False)
                # ===== AXIS 3: Balances (log scale) =====
                ax3 = ax1.twinx()
                ax3.plot(x, b0_list, color="#4753FFFF", linewidth=1.2, label="Balance 0")
                ax3.plot(x, b1_list, color="#4753FFFF", linewidth=1.2, label="Balance 1", linestyle='--')
                ax3.set_yscale("log")
                ax3.set_ylim(1, 10**7)
                ax3.set_yticks([])
                ax3.set_ylabel("")
                ax3.spines["right"].set_visible(False)
                # ===== Legends =====
                lines = ax1.get_lines() + ax2.get_lines() + ax3.get_lines()
                labels = [l.get_label() for l in lines]
                ax1.legend(lines, labels, loc="upper left")
                fig.tight_layout()
                plt.savefig("saves/" + str(self.chain_id) + "_" + sym0 + "_" + sym1 + "_" + str(key[2]) + ".png", dpi=200)
                plt.close()

        if use != 'Dust' and use != 'Work':
            self.dust_arbitrage_pools = dust_arbitrage_pools.copy()
            self.active_trade_pools = active_trade_pools.copy()
        # self.pools_data = pools.copy()



    # single pool agbitrage check

    def check_arbitrage_possibilities(self):
        dust_arbitrage_pools = self.dust_arbitrage_pools.copy()
        for key, value in dust_arbitrage_pools.items():


            balance0 = value["balance0"][-1]
            balance1 = value["balance1"][-1]

            dec0 = self.tokens_data[key[0]]["decimals"]
            dec1 = self.tokens_data[key[1]]["decimals"]
            token0_cex_price = value["cex_price0"][-1]
            token1_cex_price = value["cex_price1"][-1]

            cex_price = token0_cex_price / token1_cex_price
            dex_price = value["dex_price"][-1]

            balance0_usd = balance0 * token0_cex_price
            balance1_usd = balance1 * token1_cex_price

            if value["reversed"]:
                dex_price_w = 1 / dex_price
                cex_price_w = 1 / cex_price
                rev_flag = '!'
            else:
                dex_price_w = dex_price
                cex_price_w = cex_price
                rev_flag = ' '
            
            price_delta = (dex_price - cex_price) / cex_price * 100 if cex_price != 0 else 0
            print('\nChecking pool:', self.tokens_data[key[0]]["cex_name"],
                self.tokens_data[key[1]]["cex_name"], key[2],
                '\t| CEX price:', round(cex_price_w, 5),
                '\t| DEX price:', round(dex_price_w, 5),
                '\t| Delta %:', round(price_delta, 2),
                '\t| Bal0:', round(balance0_usd, 3),
                '\t| Bal1:', round(balance1_usd, 3), '\t', rev_flag)
            
            check_volumes = [0.001, 0.00215, 0.00464, 0.01, 0.0215] #, 0.0464, 0.1, 0.215, 0.464]                               TRY LIMITED VOLUMES
            if price_delta > 0.5:
                max_search = 0
                for vol in check_volumes:           # token 0 to 1
                    amm_in_usd = vol * balance1_usd
                    amm_in = amm_in_usd / token0_cex_price
                    amm_out = self.get_swap_ammount_quoter(self.contract_quoter, 
                        key[0], key[1], dec0, dec1, key[2], amm_in)
                    amm_out_usd = amm_out * token1_cex_price
                    amm_d = amm_out_usd - amm_in_usd
                    print('Testing swap. Token 0 input usd/row:', round(amm_in_usd, 6), round(amm_in, 6),
                        '\tToken 1 output row/usd:', round(amm_out, 6), round(amm_out_usd, 6),
                        '\tDifference usd:', round(amm_d, 6))
                    if amm_d > max_search:
                        max_search = amm_d
                        token_main_arb_in = key[0]
                        token_main_arb_out = key[1]
                        amm_main_arb_in = amm_in
                        amm_main_arb_out = amm_out
                        used_fee = key[2]
                    else:
                        break
                    time.sleep(0.5)     # for avoid too many requests in short time
                if max_search > 0.02:
                    print('====================> OK', max_search)
                    self.found_best_sub_arb_swaps(token_main_arb_in, token_main_arb_out, amm_main_arb_in, amm_main_arb_out, used_fee)

            elif price_delta < -0.5:
                max_search = 0
                for vol in check_volumes:           # token 1 to 0
                    amm_in_usd = vol * balance0_usd
                    amm_in = amm_in_usd / token1_cex_price
                    amm_out = self.get_swap_ammount_quoter(self.contract_quoter, 
                        key[1], key[0], dec1, dec0, key[2], amm_in)
                    amm_out_usd = amm_out * token0_cex_price
                    amm_d = amm_out_usd - amm_in_usd
                    print('Testing swap. Token 1 input usd/row:', round(amm_in_usd, 6), round(amm_in, 6),
                        '\tToken 0 output row/usd:', round(amm_out, 6), round(amm_out_usd, 6),
                        '\tDifference usd:', round(amm_d, 6))
                    if amm_d > max_search:
                        max_search = amm_d
                        token_main_arb_in = key[1]
                        token_main_arb_out = key[0]
                        amm_main_arb_in = amm_in
                        amm_main_arb_out = amm_out
                        used_fee = key[2]
                    else:
                        break
                    time.sleep(0.5)     # for avoid too many requests in short time
                if max_search > 0.02:
                    print('====================> OK', max_search)
                    self.found_best_sub_arb_swaps(token_main_arb_in, token_main_arb_out, amm_main_arb_in, amm_main_arb_out, used_fee)
                    
    # arbitrage sub swaps decorator for fix profit fastly with defi
    def found_best_sub_arb_swaps(self, token_main_arb_in, token_main_arb_out, amm_main_arb_in, amm_main_arb_out, used_fee):
        ref_tokens = ["USDC", "USDT", "ETH"]
        token_main_arb_in_dec = self.tokens_data[token_main_arb_in]["decimals"]
        token_main_arb_out_dec = self.tokens_data[token_main_arb_out]["decimals"]

        for ref_tok in ref_tokens:
            print('\nUsing', ref_tok, 'as reference token')
            reference_token = self.tokens[ref_tok]
            reference_token_dec = self.tokens_data[reference_token]["decimals"]
            amm_start = amm_finish = best_fee_pre = best_fee_post = None

            if reference_token != token_main_arb_in:        # is pre swap needed?
                for fee in self.pools_fee:
                    if reference_token == token_main_arb_out and fee == used_fee:
                        print('ignore this way', fee)
                        continue
                    amm_start_res = self.get_swap_ammount_quoter(self.contract_quoter,          # preprocessing ammount, begin sub arbitrage swap
                        reference_token, token_main_arb_in, reference_token_dec, token_main_arb_in_dec, fee, amm_main_arb_in, exact="Q")
                    print(self.tokens_data[reference_token]["cex_name"], '>>>', self.tokens_data[token_main_arb_in]["cex_name"])
                    if amm_start_res:
                        if amm_start is None:
                            amm_start = amm_start_res
                            best_fee_pre = fee
                            print('debug by Q', fee, amm_start, 'first valid data') 
                        elif amm_start_res < amm_start:
                            amm_start = amm_start_res
                            best_fee_pre = fee
                            print('debug by Q', fee, amm_start, 'more better data') 
                    else:
                        print('debug by Q', fee, amm_start, 'not valid data') 
                    time.sleep(0.5)     # for avoid too many requests in short time

            if reference_token != token_main_arb_out:       # is post swap needed?
                for fee in self.pools_fee:
                    if reference_token == token_main_arb_in and fee == used_fee:
                        print('ignore this way', fee)
                        continue
                    amm_finish_res = self.get_swap_ammount_quoter(self.contract_quoter,         # postprocessing ammount, finish sub arbitrage swap
                        token_main_arb_out, reference_token, token_main_arb_out_dec, reference_token_dec, fee, amm_main_arb_out, exact="I")
                    print(self.tokens_data[token_main_arb_out]["cex_name"], '>>>', self.tokens_data[reference_token]["cex_name"])
                    if amm_finish_res:
                        if amm_finish is None:
                            amm_finish = amm_finish_res
                            best_fee_post = fee
                            print('debug by I', fee, amm_finish, 'first valid data') 
                        elif amm_finish_res > amm_finish:
                            amm_finish = amm_finish_res
                            best_fee_post = fee
                            print('debug by I', fee, amm_finish, 'more better data') 
                    else:
                        print('debug by I', fee, amm_finish, 'not valid data') 
                    time.sleep(0.5)     # for avoid too many requests in short time

            if amm_start and amm_finish:
                diff_netto = amm_finish - amm_start
            else:
                diff_netto = 0
            print('Amm In/Out:', amm_start, amm_finish, '\tBest feest pre/post:', best_fee_pre, best_fee_post, 'Diff:', diff_netto)        
        return








    ''' Utilitary functions '''

    def approve_token_1(self):
        self.approve_token(self.tokens_data[self.tokens["USDC"]]["contract"], 
            self.tokens_data[self.tokens["USDC"]]["decimals"], 
            0,
            self.connection, self.address_wallet, self.chain_id)

    def approve_token_2(self):
        self.approve_token(self.tokens_data[self.tokens["GMT"]]["contract"], 
            self.tokens_data[self.tokens["GMT"]]["decimals"], 
            0,
            self.connection, self.address_wallet, self.chain_id)

    def manual_swap_1(self):
        in_swap = 1.5 # usd
        out_limit = 1.4 # usd
        self.get_swap_ammount_router(self.contract_router, 
            self.tokens["USDC"],
            self.tokens["USDT"],
            self.tokens_data[self.tokens["USDC"]]["decimals"],
            self.tokens_data[self.tokens["USDT"]]["decimals"],
            500, 
            in_swap,
            out_limit / self.tokens_data[self.tokens["USDT"]]["cex_price"],
            self.connection, self.address_wallet, self.chain_id)

    def manual_swap_2(self):
        in_swap = 1 # usd
        out_limit = 2 # usd
        self.get_swap_ammount_router(self.contract_router, 
            self.tokens["GMT"],
            self.tokens["USDC"],
            self.tokens_data[self.tokens["GMT"]]["decimals"],
            self.tokens_data[self.tokens["USDC"]]["decimals"],
            10000, 
            in_swap / self.tokens_data[self.tokens["GMT"]]["cex_price"],
            out_limit,
            self.connection, self.address_wallet, self.chain_id)







    # Raz v sutki proverjatj vse na tvl
    # Raz v 2 chasa proverjatj aktivnqe na gross
    # Raz v 10 minut proverjatj trash dlia arbitrage

    # Ideja maswtabirovatj na sdk vqzovq
    # Websocets, subprocessq








    ''' Sayety wraped requests to rpc '''

    @classmethod
    def get_balance_token(cls, token_cntr, target_addr, dec):
        balance_row = cls.safe_call(
        lambda: token_cntr.functions.balanceOf(
            target_addr
        ).call())
        balance = balance_row / 10**dec
        return balance

    @classmethod
    def get_slot_data(cls, pool_cntr, dec0, dec1):
        slot0 = cls.safe_call(
            lambda: pool_cntr.functions.slot0().call())
        sqrtPriceX96 = slot0[0]
        price = (sqrtPriceX96 / 2**96) ** 2
        price_scaled = price * 10**(dec0 - dec1)
        current_tick = slot0[1]
        return price_scaled, current_tick

    @classmethod
    def get_liquidity(cls, pool_cntr, dec0, dec1):
        l_row = cls.safe_call(
            lambda: pool_cntr.functions.liquidity().call())
        row_fee0 = cls.safe_call(
            lambda: pool_cntr.functions.feeGrowthGlobal0X128().call())
        row_fee1 = cls.safe_call(
            lambda: pool_cntr.functions.feeGrowthGlobal1X128().call())
        fee0_real = row_fee0 / 2**128
        fee1_real = row_fee1 / 2**128
        fee0 = fee0_real / 10**dec0
        fee1 = fee1_real / 10**dec1
        return l_row, fee0, fee1

    @classmethod
    def get_swap_ammount_quoter(cls, quoter_cntr, token_in, token_out, dec_in, dec_out, fee, amount, exact='I'):
        if exact == 'I':
            amount_scaled = int(amount * (10 ** dec_in))
            amount_row = cls.safe_call(
                lambda: quoter_cntr.functions.quoteExactInputSingle(
                    token_in, token_out, fee, amount_scaled, 0
                ).call())
            ammount_norm = amount_row / (10 ** dec_out)
        elif exact == 'Q':
            amount_scaled = int(amount * (10 ** dec_out))
            amount_row = cls.safe_call(
                lambda: quoter_cntr.functions.quoteExactOutputSingle(
                    token_in, token_out, fee, amount_scaled, 0
                ).call())
            ammount_norm = amount_row / (10 ** dec_in)
        else: return None
        return ammount_norm






    @staticmethod
    def get_swap_ammount_router(router_cntr, token_in, token_out, dec_in, dec_out, fee, amount, amount_lim, conn, wallet, chain_id, exact='I', deadline=60):
        if exact == 'I':
            amount_scaled = int(amount * (10 ** dec_in))
            amount_scaled_lim = int(amount_lim * (10 ** dec_out))
        elif exact == 'Q':
            amount_scaled = int(amount * (10 ** dec_out))
            amount_scaled_lim = int(amount_lim * (10 ** dec_in))
        else: return 0


        nonce = conn.eth.get_transaction_count(wallet)
        gas_price = conn.eth.gas_price
        print('Gas:', conn.from_wei(gas_price, 'gwei'), 'gwei', end=' ')


        if exact == 'I':
            params = {
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": fee,
            "recipient": wallet,
            "deadline": int(time.time()) + deadline,
            "amountIn": amount_scaled,
            "amountOutMinimum": amount_scaled_lim,
            "sqrtPriceLimitX96": 0,
            }
            transaction = router_cntr.functions.exactInputSingle(params).build_transaction({
            'gas': 300000,
            'gasPrice': int(gas_price * 1.05),
            'nonce': nonce,
            'chainId': chain_id,
            })
        elif exact == 'Q':
            params = {
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": fee,
            "recipient": wallet,
            "deadline": int(time.time()) + deadline,
            "amountOut": amount_scaled,
            "amountInMaximum": amount_scaled_lim,
            "sqrtPriceLimitX96": 0,
            }
            transaction = router_cntr.functions.exactOutputSingle(params).build_transaction({
            'gas': 300000,
            'gasPrice': int(gas_price * 1.05),
            'nonce': nonce,
            'chainId': chain_id,
            })
        else: return 0

        key = os.getenv("WORK_KEY")
        signed_transaction = conn.eth.account.sign_transaction(transaction, key)
        transaction_hash = conn.eth.send_raw_transaction(signed_transaction.raw_transaction)
        print(f"Hash: {conn.to_hex(transaction_hash)}", end=' ')

        receipt = conn.eth.wait_for_transaction_receipt(transaction_hash, timeout=120, poll_latency=2)
        if receipt and receipt.get("status") == 1:
            print(" - Transaction confirmed")
        else:
            print(" - Transaction failed")

        test_output = 1
        if exact == 'I':
            ammount_out = test_output / (10 ** dec_out)
        elif exact == 'Q':
            ammount_out = test_output / (10 ** dec_in)
        else: return 0
        return ammount_out



    @staticmethod
    def approve_token(token_cntr, dec, amount, conn, wallet, chain_id):

        if amount == 0:
            amount_scaled = int(2**256 - 1)
        else:
            amount_scaled = int(amount * 10**dec)

        nonce = conn.eth.get_transaction_count(wallet)
        gas_price = conn.eth.gas_price
        print('Gas:', conn.from_wei(gas_price, 'gwei'), 'gwei...', end=' ')


        transaction = token_cntr.functions.approve(wallet, amount_scaled).build_transaction({
        'gas': 210000,
        'gasPrice':  int(gas_price * 1.05),
        'nonce': nonce,
        'chainId': chain_id,
        })

        key = os.getenv("WORK_KEY")
        signed_transaction = conn.eth.account.sign_transaction(transaction, key)
        transaction_hash = conn.eth.send_raw_transaction(signed_transaction.raw_transaction)
        print(f"Hash: {conn.to_hex(transaction_hash)}", end=' ')

        receipt = conn.eth.wait_for_transaction_receipt(transaction_hash, timeout=120, poll_latency=2)
        if receipt and receipt.get("status") == 1:
            print(" - Transaction confirmed")
        else:
            print(" - Transaction failed")
        return



    ''' HELPERS '''

    def resolve_pool_key(self, pools, token_sym0, token_sym1, fee):
        token_addr0 = self.tokens[token_sym0]
        token_addt1 = self.tokens[token_sym1]
        key = (token_addr0, token_addt1, fee) if token_addr0.lower() < token_addt1.lower() else (token_addt1, token_addr0, fee)
        value = pools.get(key)
        return key, value


    @staticmethod
    def safe_call(fn, retries=6, delay=6):
        for attempt in range(retries):
            try:
                return fn()
            except Web3RPCError as e:
                print(f"[RPC retry {attempt+1}] {e}")
            except Exception as e:
                print(f"[Error retry {attempt+1}] {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
        return 0

    @staticmethod
    def make_avg(window_size):
        values = deque(maxlen=window_size)
        def add(x):
            if x is not None:
                values.append(x)
            return sum(values) / len(values) if values else None
        return add

    @staticmethod
    def sma_calc(prev_sma, new_value, period):
        if prev_sma is None:
            return new_value
        if period <= 1:
            period = 1
        alpha = 1 / period
        new_sma = (1 - alpha) * prev_sma + alpha * new_value
        return new_sma



# OPTIMIZE REPITED CODE

'''
# ===================================================================================== Blockchain operations



    def get_balance_native(self, addr=None):
        if addr is None:
            addr = self.address_wallet
        try:
            balance = self.connection.eth.get_balance(addr)
        except (BadResponseFormat, Web3Exception) as e:
            print(f"Web3 error while fetching balance: {e}")
            time.sleep(300)
        except Exception as e:
            print(f"Unexpected error while fetching balance: {e}")
            time.sleep(300)
        else:
            self.balance_native = native = self.connection.from_wei(balance, 'ether')
        print('Balance native :', self.balance_native)
        return native



    def send_native(self, amount, wait=1):
        amount_in_wei = self.connection.to_wei(amount, "ether")
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        transaction = {
        "to": self.address_withdraw,
        "value": amount_in_wei,
        "gas": 21000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,}
        return self.post_transaction(transaction, wait)

    def send_token(self, amount, token, wait=1):
        if token == 0:
            contract_token = self.contract_token0
            decimals = self.decimals0
        elif token == 1:
            contract_token = self.contract_token1
            decimals = self.decimals1
        amount_scaled = int(amount * 10**decimals)
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        transaction = contract_token.functions.transfer(self.address_withdraw, amount_scaled).build_transaction({
        "gas": 210000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,})
        return self.post_transaction(transaction, wait)

    def approve_token(self, amount, token, target, wait=1):
        print('\n!APP!', end=' ')
        if token == 0:
            contract_token = self.contract_token0
            decimals = self.decimals0
        elif token == 1:
            contract_token = self.contract_token1
            decimals = self.decimals1
        if target == 'r':
            address = self.address_router
        elif target == 'm':
            address = self.address_manager
        elif target == 'p':
            address = self.address_pool
        if amount == 0:
            amount_scaled = int(2**256 - 1)
        else:
            amount_scaled = int(amount * 10**decimals)
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        transaction = contract_token.functions.approve(address, amount_scaled).build_transaction({
        'gas': 210000,
        'gasPrice':  int(gas_price * 1.05),
        'nonce': nonce,
        'chainId': self.chain_id,
        })
        return self.post_transaction(transaction, wait)

    def allowance(self, token, target):
        if token == 0:
            contract_token = self.contract_token0
            decimals = self.decimals0
        elif token == 1:
            contract_token = self.contract_token1
            decimals = self.decimals1
        if target == 'r':
            address = self.address_router
        elif target == 'm':
            address = self.address_manager
        elif target == 'p':
            address = self.address_pool
        allowance = contract_token.functions.allowance(self.address_wallet, address).call()
        return allowance / 10**decimals

    def price_from_tick(self, tick, fee=None):
        if fee is None:
            fee = self.L_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        if pool['reversed']:
            P = (1 / (1.0001**tick)) * 10**(self.decimals0 - self.decimals1)
        else:
            P = (1.0001**tick) * 10**(self.decimals0 - self.decimals1)
        return(P)

    def tick_from_price(self, P, fee=None):
        if fee is None:
            fee = self.L_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        if pool['reversed']:
            tick = math.log(1 / P * 10**(self.decimals0 - self.decimals1)) / math.log(1.0001)
        else:
            tick = math.log(P * 10**(self.decimals1 - self.decimals0)) / math.log(1.0001)
        return(tick)

    def tick_normalize(self, tick, direction='', fee=None):
        if fee is None:
            fee = self.L_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        if pool['reversed']:
            if direction == 'smx':
                tick_corrected = tick - tick % pool['spacing']
            elif direction == 'smn':
                tick_corrected = tick - tick % pool['spacing'] + pool['spacing']
            elif direction == 'mx':
                tick_corrected = math.floor(tick)
            elif direction == 'mn':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % pool['spacing'] >= pool['spacing'] / 2:
                    tick_corrected = tick - tick % pool['spacing'] + pool['spacing']
                else:
                    tick_corrected = tick - tick % pool['spacing']
            else:
                tick_corrected = round(tick)
        else:
            if direction == 'smn':
                tick_corrected = tick - tick % pool['spacing']
            elif direction == 'smx':
                tick_corrected = tick - tick % pool['spacing'] + pool['spacing']
            elif direction == 'mn':
                tick_corrected = math.floor(tick)
            elif direction == 'mx':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % pool['spacing'] >= pool['spacing'] / 2:
                    tick_corrected = tick - tick % pool['spacing'] + pool['spacing']
                else:
                    tick_corrected = tick - tick % pool['spacing']
            else:
                tick_corrected = round(tick)
        return int(tick_corrected)

    def get_current_tick(self, fee=None, retries=5, delay=5):
        if fee is None:
            fee = self.G_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        for attempt in range(retries):
            try:
                slot0 = pool['contract'].functions.slot0().call()
            except (BadResponseFormat, Web3Exception) as e:
                print(f"[{attempt+1}/{retries}] Web3 error: {e}")
                time.sleep(delay)
            except Exception as e:
                print(f"[{attempt+1}/{retries}] Unexpected error: {e}")
                time.sleep(delay)
            else:
                self.current_tick = slot0[1]
                sqrtPriceX96 = slot0[0]
                price = (sqrtPriceX96 / 2**96) ** 2
                if pool['reversed']:
                    self.current_price = (1 / price) * 10**(self.decimals0 - self.decimals1)
                else:
                    self.current_price = price * 10**(self.decimals0 - self.decimals1)
                print('(', fee, ') Cur price: ', round(self.current_price, 3), ' (', self.current_tick, ')', end=' ', sep = '')
                return self.current_tick, self.current_price
        return None

    def get_liquidity(self, tick=None, fee=None, retries=5, delay=5):
        if fee is None:
            fee = self.G_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        if tick is None:
            for attempt in range(retries):    
                try:
                    l_row = pool['contract'].functions.liquidity().call()
                    row_fee0 = pool['contract'].functions.feeGrowthGlobal0X128().call()
                    row_fee1 = pool['contract'].functions.feeGrowthGlobal1X128().call()
                except Exception as e:
                    print(f"[{attempt+1}/{retries}] Unexpected error on call: {e}")
                    time.sleep(delay)
                else:
                    # print(row_fee0, row_fee1)        
                    fee0_real = row_fee0 / 2**128
                    fee1_real = row_fee1 / 2**128
                    # print(self.decimals0, self.decimals1)
                    # print(l_row)
                    if pool['reversed']:
                        fee0 = fee1_real / 10**self.decimals1
                        fee1 = fee0_real / 10**self.decimals0
                    else:
                        fee0 = fee0_real / 10**self.decimals0
                        fee1 = fee1_real / 10**self.decimals1
                    # liquidity = l_row**2 / 10**(self.decimals0 + self.decimals1)
                    # print(liquidity)
                    # print(fee0, fee1)
                    return l_row, fee0, fee1
            return None
        # next part not used
        else:
            tick_data = pool['contract'].functions.ticks(tick).call()
            liquidity_net = tick_data[0]
            liquidity_gross = tick_data[1]
            return liquidity_net, liquidity_gross            

    def get_swap_ammount_quoter(self, amount, token, by, fee=None):
        if fee is None:
            fee = self.S_fee
        if token:
            tokenIn = self.address_token0
            tokenOut = self.address_token1
        else:
            tokenIn = self.address_token1
            tokenOut = self.address_token0
        if (token == 0 and by == 'I') or (token == 1 and by == 'Q'):
            amount_scaled = int(amount * (10**self.decimals1))
        elif (token == 0 and by == 'Q') or (token == 1 and by == 'I'):
            amount_scaled = int(amount * (10**self.decimals0))
        if by == 'I':
            amount_row = self.contract_quoter.functions.quoteExactInputSingle(
            tokenIn, tokenOut, fee, amount_scaled, 0
            ).call()
        elif by == 'Q':
            amount_row = self.contract_quoter.functions.quoteExactOutputSingle(
            tokenIn, tokenOut, fee, amount_scaled, 0
            ).call()
        if (token == 0 and by == 'I') or (token == 1 and by == 'Q'):
            ammount_norm = amount_row / (10 ** self.decimals0)
        elif (token == 0 and by == 'Q') or (token == 1 and by == 'I'):
            ammount_norm = amount_row / (10 ** self.decimals1)
        return ammount_norm

    def get_swap_ammount_router(self, amount, amount_lim, token, by, fee=None, deadline=60, wait=1):
        print('\n!SWP!', end=' ')
        if fee is None:
            fee = self.S_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        if token:
            tokenIn = self.address_token0
            tokenOut = self.address_token1
        else:
            tokenIn = self.address_token1
            tokenOut = self.address_token0
        if (token == 0 and by == 'I') or (token == 1 and by == 'Q'):
            amount_scaled = int(amount * (10**self.decimals1))
            amount_lim_scaled = int(amount_lim * (10**self.decimals0))
        elif (token == 0 and by == 'Q') or (token == 1 and by == 'I'):
            amount_scaled = int(amount * (10**self.decimals0))
            amount_lim_scaled = int(amount_lim * (10**self.decimals1))
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        if by == 'I':
            params = {
            "tokenIn": tokenIn,
            "tokenOut": tokenOut,
            "fee": fee,
            "recipient": self.address_wallet,
            "deadline": int(time.time()) + deadline,
            "amountIn": amount_scaled,
            "amountOutMinimum": amount_lim_scaled,
            "sqrtPriceLimitX96": 0,
            }
            transaction = self.contract_router.functions.exactInputSingle(params).build_transaction({
            'gas': 300000,
            'gasPrice': int(gas_price * 1.05),
            'nonce': nonce,
            'chainId': self.chain_id,
            })
        else:
            params = {
            "tokenIn": tokenIn,
            "tokenOut": tokenOut,
            "fee": fee,
            "recipient": self.address_wallet,
            "deadline": int(time.time()) + deadline,
            "amountOut": amount_scaled,
            "amountInMaximum": amount_lim_scaled,
            "sqrtPriceLimitX96": 0,
            }
            transaction = self.contract_router.functions.exactOutputSingle(params).build_transaction({
            'gas': 300000,
            'gasPrice': int(gas_price * 1.05),
            'nonce': nonce,
            'chainId': self.chain_id,
            })
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            events = pool['contract'].events.Swap().process_receipt(receipt)
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if pool['reversed']:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
        else:
            amm0_ok = 0
            amm1_ok = 0
        return status, amm0_ok, amm1_ok

    def liq_add(self, range_min, range_max, amount0, amount1, deadline=60, wait=1, fee=None):
        print('\n!ADD!', end=' ')
        if fee is None:
            fee = self.L_fee
        pool = self.pools.get(fee)
        if pool is None:
            return None
        amount0_scaled = int(amount0 * (10**self.decimals0))
        amount1_scaled = int(amount1 * (10**self.decimals1))
        if pool['reversed']:
            lower = range_max
            upper = range_min
            address_token0_corrected = self.address_token1
            address_token1_corrected = self.address_token0
            amount0_corrected = amount1_scaled
            amount1_corrected = amount0_scaled
        else:
            lower = range_min
            upper = range_max
            address_token0_corrected = self.address_token0
            address_token1_corrected = self.address_token1
            amount0_corrected = amount0_scaled
            amount1_corrected = amount1_scaled
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit*1.1)
        params = {
        "token0": address_token0_corrected,
        "token1": address_token1_corrected,
        "fee": fee,
        "tickLower": lower,
        "tickUpper": upper,
        "amount0Desired": amount0_corrected,
        "amount1Desired": amount1_corrected,
        "amount0Min": 0,
        "amount1Min": 0,
        "recipient": self.address_wallet,
        "deadline": int(time.time()) + deadline,
        }
        transaction = self.contract_manager.functions.mint(params).build_transaction({
        "from": self.address_wallet,
        'gas': 800000,
        'gasPrice': int(gas_price * 1.05),
        'nonce': nonce,
        'chainId': self.chain_id,
        })
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            events = self.contract_manager.events.IncreaseLiquidity().process_receipt(receipt)
            for e in events:
                token_id = e["args"]["tokenId"]
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]            
                if pool['reversed']:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
            position = self.contract_manager.functions.positions(token_id).call()
            current_liquidity = position[7]
        else:
            token_id = 0
            amm0_ok = 0
            amm1_ok = 0
            current_liquidity = 0
        return status, amm0_ok, amm1_ok, token_id, current_liquidity

    def liq_remove(self, token_id, deadline=60, wait=1):
        print('\n!REM!', end=' ')
        position = self.contract_manager.functions.positions(token_id).call()
        current_liquidity = position[7]
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        params = {
        "tokenId": token_id,
        "liquidity": current_liquidity,
        "amount0Min": 0,
        "amount1Min": 0,
        "deadline": int(time.time()) + deadline,
        }
        transaction = self.contract_manager.functions.decreaseLiquidity(params).build_transaction({
        "from": self.address_wallet,
        "gas": 300000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,
        })
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            events = self.contract_manager.events.DecreaseLiquidity().process_receipt(receipt)
            position = self.contract_manager.functions.positions(token_id).call()
            fee = position[4]
            pool = self.pools.get(fee)
            if pool is None:
                return None
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if pool["reversed"]:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
        else:
            amm0_ok = 0
            amm1_ok = 0
        return status, amm0_ok, amm1_ok

    def collect(self, token_id, wait=1):
        print('\n!COL!', end=' ')
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit*1.1)
        params = {
        "tokenId": token_id,
        "recipient": self.address_wallet,
        "amount0Max": 2**128 - 1,
        "amount1Max": 2**128 - 1,
        }
        transaction = self.contract_manager.functions.collect(params).build_transaction({
        "from": self.address_wallet,
        "gas": 300000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,
        })
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            events = self.contract_manager.events.Collect().process_receipt(receipt)
            position = self.contract_manager.functions.positions(token_id).call()
            fee = position[4]
            pool = self.pools.get(fee)
            if pool is None:
                return None
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if pool["reversed"]:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
        else:
            amm0_ok = 0
            amm1_ok = 0
        return status, amm0_ok, amm1_ok

    def burn(self, token_id, wait=1):
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=self.gas_limit)
        transaction = self.contract_manager.functions.burn(token_id).build_transaction({
            "from": self.address_wallet,
            "gas": 200000,
            "gasPrice": int(gas_price * 1.05),
            "nonce": nonce,
            "chainId": self.chain_id,
        })
        return self.post_transaction(transaction, wait)

    def pre_transaction(self, gas_price_limit_gwei):
        nonce = self.connection.eth.get_transaction_count(self.address_wallet)
        gas_price = self.connection.eth.gas_price
        print('Gas:', self.connection.from_wei(gas_price, 'gwei'), 'gwei', end=' ')
        gas_price_limit = self.connection.to_wei(gas_price_limit_gwei, 'gwei')
        if gas_price > gas_price_limit:
            print('Limited!', end=' ')
            gas_price = gas_price_limit
        return nonce, gas_price

    def post_transaction(self, transaction, wait=0):
        try:
            signed_transaction = self.connection.eth.account.sign_transaction(transaction, self.key_wallet)
            transaction_hash = self.connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
            print(f"Hash: {self.connection.to_hex(transaction_hash)}", end=' ')
            if wait:
                try:
                    # print("Waiting for transaction receipt...")
                    receipt = self.connection.eth.wait_for_transaction_receipt(transaction_hash, timeout=120, poll_latency=2)
                    if receipt and receipt.get("status") == 1:
                        # print("Done!", receipt.get("blockNumber"))
                        return 1, receipt
                    else:
                        print("Rejected!")
                        return 0, 0
                except TimeExhausted:
                    print("Timed out!")
                    return 9, 0
            else:
                return -1, 0
        except (BadResponseFormat, Web3Exception) as e:
            print(f"Web3 error: {e}")
            return 8, 0
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 7, 0
'''
