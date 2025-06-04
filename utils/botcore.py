from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TimeExhausted
import os
import math
import random
import json

class ChainLink:
    def __init__(self, blockchain, token0, token1, proto, wallet, fee):
        if blockchain == 'arbitrum':                                        # open chain config file
            path = 'config/addresses/arbitrum.json'
        elif blockchain == 'polygon':
            path = 'config/addresses/polygon.json'
        elif blockchain == 'optimism':
            path = 'config/addresses/optimism.json'
        with open(path, 'r') as f:
            params = json.load(f)
        for key, value in params.items():
            setattr(self, key, value)
        self.address_token0 = getattr(self, token0)                         # set tokens
        self.address_token1 = getattr(self, token1)
        with open("config/abi/token.json", "r") as f:
            self.abi_token = json.load(f)
        if proto == 'uniswap':                                              # set protocol addresses and abi
            self.address_factory = self.uniswap_factory
            self.address_router = self.uniswap_router
            self.address_quoter = self.uniswap_quoter
            with open("config/abi/uniswap_factory.json", "r") as f:
                self.abi_factory = json.load(f)
            with open("config/abi/uniswap_router.json", "r") as f:
                self.abi_router = json.load(f)
            with open("config/abi/uniswap_quoter.json", "r") as f:
                self.abi_quoter = json.load(f)
            with open("config/abi/uniswap_pool.json", "r") as f:
                self.abi_pool = json.load(f)
        load_dotenv("private/secrets.env")
        if wallet == 'test':                                                # set wallet
            self.address_withdraw = os.getenv("MAIN_ADR")
            self.address_wallet = os.getenv("WORK_ADR")
            self.key_wallet = os.getenv("WORK_KEY")
        elif wallet == 'work':
            self.address_withdraw = os.getenv("WORK_ADR")
            self.address_wallet = os.getenv("MAIN_ADR")
            self.key_wallet = os.getenv("WORK_KEY")
        self.connection = Web3(Web3.HTTPProvider(self.rpc))                 # connect to node
        if self.connection.is_connected():
            print("Connected!")
        else:
            print("Not connected!")
        print(self.address_token0, self.address_token1)
        self.contract_token0 = self.connection.eth.contract(address=self.address_token0, abi=self.abi_token)
        self.contract_token1 = self.connection.eth.contract(address=self.address_token1, abi=self.abi_token)
        self.contract_factory = self.connection.eth.contract(address=self.address_factory, abi=self.abi_factory)
        self.contract_router = self.connection.eth.contract(address=self.address_router, abi=self.abi_router)
        self.contract_quoter = self.connection.eth.contract(address=self.address_quoter, abi=self.abi_quoter)
        self.address_pool = self.contract_factory.functions.getPool(self.address_token0, self.address_token1, fee).call()
        self.address_pool_test = self.contract_factory.functions.getPool(self.address_token1, self.address_token0, fee).call()
        print(f"Address pool: {self.address_pool}")                         # set contracts
        self.contract_pool = self.connection.eth.contract(address=self.address_pool, abi=self.abi_pool)
    
    def get_balance_native(self):
        balance = self.connection.eth.get_balance(self.address_wallet)
        self.balance_native = self.connection.from_wei(balance, 'ether')
        print('Balance native :', self.balance_native)

    def get_balance_token(self, token):
        if token == 0:
            address = self.address_token0
            contract = self.contract_token0
        elif token == 1:
            address = self.address_token1
            contract = self.contract_token1
        balance = contract.functions.balanceOf(self.address_wallet).call()
        decimals = contract.functions.decimals().call()
        balance_token = balance / 10**decimals
        print("Balance", address, ':', balance_token)
        if token == 0:
            self.balance_token0 = balance_token
        elif token == 1:
            self.balance_token1 = balance_token

    def send_native(self, amount, wait=0):
        amount_in_wei = self.connection.to_wei(amount, "ether")
        nonce = self.connection.eth.get_transaction_count(self.address_wallet)
        gas_price = self.connection.eth.gas_price
        print(f"Recomended gas price: {self.connection.from_wei(gas_price, 'gwei')} Gwei")
        if gas_price > 1000000000000:
            print('Gas price very high')
        chain_id = self.connection.eth.chain_id
        transaction = {
            "to": self.address_withdraw,
            "value": amount_in_wei,
            "gas": 21000,
            "gasPrice": int(gas_price * 1.05),
            "nonce": nonce,
            "chainId": chain_id,}
        signed_transaction = self.connection.eth.account.sign_transaction(transaction, self.key_wallet)
        tx_hash = self.connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
        print(f"Transaction sent! Hash: {self.connection.to_hex(tx_hash)}")
        if wait:
            try:
                print("Waiting for transaction receipt...")
                receipt = self.connection.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=2)
                if receipt and receipt.get("status") == 1:
                    print("Done!", receipt.get("blockNumber"))
                    return 1
                else:
                    print("Rejected!")
                    return 0
            except TimeExhausted:
                print("Transaction timed out!")
                return 9

    def send_token(self, amount, token, wait=0):
        if token:
            contract_token = self.contract_token1
        else:
            contract_token = self.contract_token0
        decimals = contract_token.functions.decimals().call()
        amount_scaled = int(amount * 10**decimals)
        nonce = self.connection.eth.get_transaction_count(self.address_wallet)
        gas_price = self.connection.eth.gas_price
        print(f"Recomended gas price: {self.connection.from_wei(gas_price, 'gwei')} Gwei")
        if gas_price > 1000000000000:
            print('Gas price very high')
        chain_id = self.connection.eth.chain_id
        transaction = contract_token.functions.transfer(self.address_withdraw, amount_scaled).build_transaction({
            "gas": 210000,
            "gasPrice": int(gas_price * 1.05),
            "nonce": nonce,
            "chainId": chain_id,})
        signed_transaction = self.connection.eth.account.sign_transaction(transaction, self.key_wallet)
        tx_hash = self.connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
        print(f"Transaction sent! Hash: {self.connection.to_hex(tx_hash)}")
        if wait:
            try:
                print("Waiting for transaction receipt...")
                receipt = self.connection.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=2)
                if receipt and receipt.get("status") == 1:
                    print("Done!", receipt.get("blockNumber"))
                    return 1
                else:
                    print("Rejected!")
                    return 0
            except TimeExhausted:
                print("Transaction timed out!")
                return 9


# def approve_token(amount, connection, token_cont, wallet, address_from, private_key):
#     decimals = token_cont.functions.decimals().call()
#     amount_scaled = int(amount * 10**decimals)
#     nonce = connection.eth.get_transaction_count(wallet)
#     tx = token_cont.functions.approve(
#         address_from,
#         amount #amount_scaled
#     ).build_transaction({
#         'chainId': 137,
#         'gas': 210000,
#         'gasPrice': int(connection.eth.gas_price * 1.1),
#         'nonce': nonce
#     })
#     signed_tx = connection.eth.account.sign_transaction(tx, private_key)
#     tx_hash = connection.eth.send_raw_transaction(signed_tx.raw_transaction)
#     print(f"Approve sended: {connection.to_hex(tx_hash)}")
#     return connection.to_hex(tx_hash)


# ===================================================================================== Operations with bot, simulation
class LiqPos:
    def __init__(self, amm0, amm1, sim):        # chain argument
        self.amm0 = amm0
        self.amm1 = amm1
        self.sim = sim
        params = LiqPos.load_config()           # MUST DO REWRITEBLE WITH RUNING
        for key, value in params.items():
            setattr(self, key, value)
        self.P_act_normal = self.reference_price
        self.P_act = self.reference_price_tick = LiqPos.prc_norm(self.P_act_normal)
        self.range_width_tick = LiqPos.prc_norm(self.reference_price + 0.5 * self.range_width_init, 1) - LiqPos.prc_norm(self.reference_price - 0.5 * self.range_width_init, 1)
        self.range_width_max_tick = LiqPos.prc_norm(self.reference_price + 0.5 * self.range_width_max, 1) - LiqPos.prc_norm(self.reference_price - 0.5 * self.range_width_max, 1)
        self.range_width_min_tick = LiqPos.prc_norm(self.reference_price + 0.5 * self.range_width_min, 1) - LiqPos.prc_norm(self.reference_price - 0.5 * self.range_width_min, 1)
        self.prices_max = []
        self.prices_min = []
        self.prices = []
        self.balances = []
        self.balances_alt = []
        self.times = []
    
    def proc_shift(self, mode):
        # new range.                                                            # need to price upd, after close
        if mode == 'UT':
            self.P_max_tick = round((self.P_act + self.range_width_tick * self.range_move_trend) / 10) * 10
            self.P_min_tick = round((self.P_act - self.range_width_tick * (1 - self.range_move_trend)) / 10) * 10
        elif mode == 'DT':
            self.P_min_tick = round((self.P_act - self.range_width_tick * self.range_move_trend) / 10) * 10
            self.P_max_tick = round((self.P_act + self.range_width_tick * (1 - self.range_move_trend)) / 10) * 10
        elif mode == 'UF':
            self.P_max_tick = round((self.P_act + self.range_width_tick * self.range_move_float) / 10) * 10
            self.P_min_tick = round((self.P_act - self.range_width_tick * (1 - self.range_move_float)) / 10) * 10
        elif mode == 'DF':
            self.P_min_tick = round((self.P_act - self.range_width_tick * self.range_move_float) / 10) * 10
            self.P_max_tick = round((self.P_act + self.range_width_tick * (1 - self.range_move_float)) / 10) * 10

    def proc_swap(self, mode):
        # do swap.
        if mode == 'UT' or mode == 'UF':                                        # need to check amm1
            self.k0 = LiqPos.clc_amm(1.0001 ** self.P_min_tick, 1.0001 ** self.P_max_tick, 1.0001 ** self.P_act, 1, 0)
            self.amm0_get = (self.k0 * self.amm1) / (1 + self.k0 * (1.0001 ** self.P_act))
            self.amm1 -= self.amm0_get * (1.0001 ** self.P_act)
            self.amm0 += self.amm0_get
            # am0new = k * am1 / (1 + k * p)                swap!
        elif mode == 'DT' or mode == 'DF':                                      # need to check amm0
            self.k1 = LiqPos.clc_amm(1.0001 ** self.P_min_tick, 1.0001 ** self.P_max_tick, 1.0001 ** self.P_act, 1, 1)
            self.amm1_get = (self.k1 * self.amm0 * (1.0001 ** self.P_act)) / (self.k1 + (1.0001 ** self.P_act))
            self.amm0 -= self.amm1_get / (1.0001 ** self.P_act)
            self.amm1 += self.amm1_get  
            # am1new = (k * am0 * p) / (k + p)              swap!

    def proc_open(self, mode):
        # do pos calc one more time                                             # need to ammount and price upd, after swap
        if mode == 'UT' or mode == 'UF':                                        # need to correct border (min or max?)
            self.bruto_max = LiqPos.clc_rng(1.0001 ** self.P_min_tick, 1.0001 ** self.P_act, self.amm0, self.amm1)
            self.P_max_tick = LiqPos.prc_norm(self.bruto_max, 1, 1, 'l')
            self.amm1_lock = self.amm1
            self.amm0_lock = LiqPos.clc_amm(1.0001 ** self.P_min_tick, 1.0001 ** self.P_max_tick, 1.0001 ** self.P_act, self.amm1_lock, 0)
            self.L = self.amm1_lock / (math.sqrt(1.0001 ** self.P_act) - math.sqrt(1.0001 ** self.P_min_tick))
            self.L2 = self.amm0_lock / ((math.sqrt(1.0001 ** self.P_max_tick) - math.sqrt(1.0001 ** self.P_act)) / (math.sqrt(1.0001 ** self.P_max_tick) * math.sqrt(1.0001 ** self.P_act)))
        elif mode == 'DT' or mode == 'DF':
            self.bruto_min = LiqPos.clc_rng(1.0001 ** self.P_max_tick, 1.0001 ** self.P_act, self.amm0, self.amm1)
            self.P_min_tick = LiqPos.prc_norm(self.bruto_min, 1, 1, 'l')
            self.amm0_lock = self.amm0
            self.amm1_lock = LiqPos.clc_amm(1.0001 ** self.P_min_tick, 1.0001 ** self.P_max_tick, 1.0001 ** self.P_act, self.amm0_lock, 1)
            self.L = self.amm1_lock / (math.sqrt(1.0001 ** self.P_act) - math.sqrt(1.0001 ** self.P_min_tick))
            self.L2 = self.amm0_lock / ((math.sqrt(1.0001 ** self.P_max_tick) - math.sqrt(1.0001 ** self.P_act)) / (math.sqrt(1.0001 ** self.P_max_tick) * math.sqrt(1.0001 ** self.P_act)))
        # entry po position. Get position liquidity
        self.opened = 1
        self.amm0 -= self.amm0_lock
        self.amm1 -= self.amm1_lock
        self.P_max = 1.0001 ** self.P_max_tick
        self.P_min = 1.0001 ** self.P_min_tick

    def proc_close(self, mode):
        # exit position. Return position liquidity
        if mode == 'UT' or mode == 'UF':
            self.amm0_lock = 0
            self.amm1_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min))
        elif mode == 'DT' or mode == 'DF':
            self.amm0_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min)) / (math.sqrt(self.P_max) * math.sqrt(self.P_min))
            self.amm1_lock = 0
        # calc statuses
        self.opened = 0
        self.L = 0
        self.amm0 += self.amm0_lock
        self.amm1 += self.amm1_lock
        self.amm0_lock = 0
        self.amm1_lock = 0

    def proc_modify(self, mode):
        # new range width
        if mode == 'UT' or mode == 'DT':
            self.range_width_tick *= self.range_scale_trend
        elif mode == 'UF' or mode == 'DF':
            self.range_width_tick *= self.range_scale_float
        if self.range_width_tick > self.range_width_max_tick:
            self.range_width_tick = self.range_width_max_tick
        if self.range_width_tick < self.range_width_min_tick:
            self.range_width_tick = self.range_width_min_tick
    
    def proc_cycle(self, mode):             # here can be balance and price actuators
        self.proc_close(mode)
        self.proc_modify(mode)
        self.proc_shift(mode)
        self.proc_swap(mode)
        self.proc_open(mode)

    def p_actuate(self, mode, hlp = 0):
        if mode == 'rnd':                                   # Random price change
            if (1.0001 ** self.P_act - self.reference_price) / self.reference_price * 100 > 100:
                x = -0.001
            elif (1.0001 ** self.P_act - self.reference_price) / self.reference_price * 100 < -50:
                x = 0.001
            else:
                x = 0                                   # hold movement in reality
            if hlp:                                     # hour or tick randomize
                y = 0.0001
            else:
                y = 0.005
            self.P_act_normal *= (1 + random.gauss(x, y))
            self.P_act = self.prc_norm(self.P_act_normal)
        elif mode == 'man':
            if hlp:
                self.P_act = self.P_max_tick
                self.P_act_normal = 1.0001 ** self.P_max_tick
            else:
                self.P_act = self.P_min_tick
                self.P_act_normal = 1.0001 ** self.P_min_tick

    def stat_put(self, time):
        self.prices_max.append(self.P_max)
        self.prices_min.append(self.P_min)
        self.prices.append(self.P_act_normal)
        self.balances.append((self.amm1 + self.amm0 * self.P_act_normal) + (self.amm1_lock + self.amm0_lock * self.P_act_normal))
        self.balances_alt.append((self.amm0 + self.amm1 / self.P_act_normal) + (self.amm0_lock + self.amm1_lock / self.P_act_normal))
        self.times.append(float(time))

    @staticmethod
    def prc_norm(P, x10 = 0, t = 1, lvl = ''):
        tick = math.log(P) / math.log(1.0001)
        if x10:
            tick = tick / 10
        if lvl == 'l':
            tick = math.floor(tick)
        elif lvl == 'h':
            tick = math.ceil(tick)
        else:
            tick = round(tick)
        if x10:
            tick = tick * 10
        if t:
            return tick
        else:
            return 1.0001 ** tick
    
    @staticmethod
    def clc_amm(P_min, P_max, P, ammount_in, target):
        if target:
            L = ammount_in / ((math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P)))
            ammount_out = L * (math.sqrt(P) - math.sqrt(P_min))
            return ammount_out
        else:
            L = ammount_in / (math.sqrt(P) - math.sqrt(P_min))
            ammount_out = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
            return ammount_out
    
    @staticmethod
    def clc_rng(P_border, P, ammount_0, ammount_1):
        if P_border > P:
            sqrt_P = math.sqrt(P)
            sqrt_P_max = math.sqrt(P_border)
            L = ammount_0 / ((sqrt_P_max - sqrt_P) / (sqrt_P_max * sqrt_P))
            P_min = (sqrt_P - ammount_1 / L) ** 2
            return P_min
        else:
            sqrt_P = math.sqrt(P)
            sqrt_P_min= math.sqrt(P_border)
            L = ammount_1 / (sqrt_P - sqrt_P_min)
            # ammount_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
            # ammount_0 / L = (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
            # math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P_max) - math.sqrt(P)
            # math.sqrt(P_max) - math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P)
            # math.sqrt(P_max) * (1 - math.sqrt(P) * (ammount_0 / L)) = math.sqrt(P)
            # math.sqrt(P_max) = math.sqrt(P) / (1 - math.sqrt(P) * (ammount_0 / L))
            P_max = (sqrt_P / (1 - sqrt_P * (ammount_0 / L))) ** 2
            return P_max
    
    @staticmethod
    def load_config(path='config/params.json'):
        with open(path, 'r') as f:
            return json.load(f)
