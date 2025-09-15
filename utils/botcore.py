from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TimeExhausted
import time
import os
import math
import random
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import random

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
        self.token0_name = token0
        self.token1_name = token1
        with open("config/abi/token.json", "r") as f:
            self.abi_token = json.load(f)
        if proto == 'uniswap':                                              # set protocol addresses and abi
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
        print('Address my:', self.address_wallet)
        self.fee = fee                                                      # set contracts
        self.contract_token0 = self.connection.eth.contract(address=self.address_token0, abi=self.abi_token)
        self.contract_token1 = self.connection.eth.contract(address=self.address_token1, abi=self.abi_token)
        self.contract_factory = self.connection.eth.contract(address=self.address_factory, abi=self.abi_factory)
        self.contract_router = self.connection.eth.contract(address=self.address_router, abi=self.abi_router)
        self.contract_quoter = self.connection.eth.contract(address=self.address_quoter, abi=self.abi_quoter)
        self.contract_manager = self.connection.eth.contract(address=self.address_manager, abi=self.abi_manager)
        self.address_pool = self.contract_factory.functions.getPool(self.address_token0, self.address_token1, fee).call()
        print('Address pool:', self.address_pool)
        self.contract_pool = self.connection.eth.contract(address=self.address_pool, abi=self.abi_pool)
        self.address_token0_pool = self.contract_pool.functions.token0().call()                 # set additional parameters
        self.address_token1_pool = self.contract_pool.functions.token1().call()
        self.decimals0 = self.contract_token0.functions.decimals().call()
        self.decimals1 = self.contract_token1.functions.decimals().call()
        if self.address_token0_pool.lower() == self.address_token0.lower() and self.address_token1_pool.lower() == self.address_token1.lower():
            self.reversed = 0
        else:
            self.reversed = 1
        self.chain_id = self.connection.eth.chain_id
        self.tick_spacing = self.contract_pool.functions.tickSpacing().call()

    def get_balance_native(self):
        balance = self.connection.eth.get_balance(self.address_wallet)
        self.balance_native = self.connection.from_wei(balance, 'ether')
        print('Balance native :', self.balance_native)

    def get_balance_token(self, token):
        if token == 0:
            address = self.address_token0
            contract = self.contract_token0
            decimals = self.decimals0
        elif token == 1:
            address = self.address_token1
            contract = self.contract_token1
            decimals = self.decimals1
        balance = contract.functions.balanceOf(self.address_wallet).call()
        balance_token = balance / 10**decimals
        print("Balance", address, ':', balance_token)
        if token == 0:
            self.balance_token0 = balance_token
        elif token == 1:
            self.balance_token1 = balance_token
        return balance_token

    def send_native(self, amount, wait=1):
        amount_in_wei = self.connection.to_wei(amount, "ether")
        nonce, gas_price = self.pre_transaction()
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
        nonce, gas_price = self.pre_transaction()
        transaction = contract_token.functions.transfer(self.address_withdraw, amount_scaled).build_transaction({
        "gas": 210000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,})
        return self.post_transaction(transaction, wait)

    def approve_token(self, amount, token, target, wait=1):
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
        nonce, gas_price = self.pre_transaction()
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
    
    def price_from_tick(self, tick):
        if self.reversed:
            P = (1 / (1.0001**tick)) * 10**(self.decimals0 - self.decimals1)
        else:
            P = (1.0001**tick) * 10**(self.decimals0 - self.decimals1)
        return(P)

    def tick_from_price(self, P):
        if self.reversed:
            tick = math.log(1 / P * 10**(self.decimals0 - self.decimals1)) / math.log(1.0001)
        else:
            tick = math.log(P * 10**(self.decimals1 - self.decimals0)) / math.log(1.0001)
        return(tick)
    
    def get_current_tick(self):
        slot0 = self.contract_pool.functions.slot0().call()
        self.current_tick = slot0[1]
        sqrtPriceX96 = slot0[0]
        price = (sqrtPriceX96 / 2**96) ** 2
        if self.reversed:
            self.current_price = (1 / price) * 10**(self.decimals0 - self.decimals1)
        else:
            self.current_price = price * 10**(self.decimals0 - self.decimals1)
        print('Current price:', self.current_price)
        return self.current_tick, self.current_price

    def get_liquidity(self, tick=None):
        if tick is None:
            self.liquidity = self.contract_pool.functions.liquidity().call()
            return self.liquidity
        else:
            tick_data = self.contract_pool.functions.ticks(tick).call()
            liquidity_net = tick_data[0]
            liquidity_gross = tick_data[1]
            return liquidity_net, liquidity_gross            

    def tick_normalize(self, tick, direction=''):
        if self.reversed:
            if direction == 'smx':
                tick_corrected = tick - tick % self.tick_spacing
            elif direction == 'smn':
                tick_corrected = tick - tick % self.tick_spacing + self.tick_spacing
            elif direction == 'mx':
                tick_corrected = math.floor(tick)
            elif direction == 'mn':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % self.tick_spacing >= self.tick_spacing / 2:
                    tick_corrected = tick - tick % self.tick_spacing + self.tick_spacing
                else:
                    tick_corrected = tick - tick % self.tick_spacing
            else:
                tick_corrected = round(tick)
        else:
            if direction == 'smn':
                tick_corrected = tick - tick % self.tick_spacing
            elif direction == 'smx':
                tick_corrected = tick - tick % self.tick_spacing + self.tick_spacing
            elif direction == 'mn':
                tick_corrected = math.floor(tick)
            elif direction == 'mx':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % self.tick_spacing >= self.tick_spacing / 2:
                    tick_corrected = tick - tick % self.tick_spacing + self.tick_spacing
                else:
                    tick_corrected = tick - tick % self.tick_spacing
            else:
                tick_corrected = round(tick)
        return int(tick_corrected)

    def get_swap_ammount_quoter(self, amount, token, by='I'):
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
            tokenIn, tokenOut, self.fee, amount_scaled, 0
            ).call()
        elif by == 'Q':
            amount_row = self.contract_quoter.functions.quoteExactOutputSingle(
            tokenIn, tokenOut, self.fee, amount_scaled, 0
            ).call()
        if (token == 0 and by == 'I') or (token == 1 and by == 'Q'):
            ammount_norm = amount_row / (10 ** self.decimals0)
        elif (token == 0 and by == 'Q') or (token == 1 and by == 'I'):
            ammount_norm = amount_row / (10 ** self.decimals1)
        return ammount_norm

    def get_swap_ammount_router(self, amount, amount_lim, token, by='I', deadline=60, wait=1):
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
        nonce, gas_price = self.pre_transaction()
        if by == 'I':
            params = {
            "tokenIn": tokenIn,
            "tokenOut": tokenOut,
            "fee": self.fee,
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
            "fee": self.fee,
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
        return self.post_transaction(transaction, wait)

    def liq_add(self, range_min, range_max, amount0, amount1, deadline=60, wait=1):
        amount0_scaled = int(amount0 * (10**self.decimals0))
        amount1_scaled = int(amount1 * (10**self.decimals1))
        if self.reversed:
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
        nonce, gas_price = self.pre_transaction()
        params = {
        "token0": address_token0_corrected,
        "token1": address_token1_corrected,
        "fee": self.fee,
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
            logs = self.contract_manager.events.Transfer().process_receipt(receipt)
            token_id = logs[0]['args']['tokenId']
        else:
            token_id = 0
        return status, token_id
    
    def liq_remove(self, token_id, deadline=60, wait=1):
        position = self.contract_manager.functions.positions(token_id).call()
        current_liquidity = position[7]
        nonce, gas_price = self.pre_transaction()
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
        return self.post_transaction(transaction, wait)

    def collect(self, token_id, wait=1):
        nonce, gas_price = self.pre_transaction()
        params = {
        "tokenId": token_id,
        "recipient": self.address_wallet,
        "amount0Max": 2**128 - 1,
        "amount1Max": 2**128 - 1,
        }
        transaction = self.contract_manager.functions.collect(params).build_transaction({
        "from": self.address_wallet,
        "gas": 200000,
        "gasPrice": int(gas_price * 1.05),
        "nonce": nonce,
        "chainId": self.chain_id,
        })
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            logs = self.contract_manager.events.Collect().process_receipt(receipt)
            for log in logs:
                print("Collected:", log.args.amount0, log.args.amount1)
        return status, receipt

    def burn(self, token_id, wait=1):
        nonce, gas_price = self.pre_transaction()
        transaction = self.contract_manager.functions.burn(token_id).build_transaction({
            "from": self.address_wallet,
            "gas": 200000,
            "gasPrice": int(gas_price * 1.05),
            "nonce": nonce,
            "chainId": self.chain_id,
        })
        return self.post_transaction(transaction, wait)

    def pre_transaction(self, gas_price_limit=1000000000000):
        nonce = self.connection.eth.get_transaction_count(self.address_wallet)
        gas_price = self.connection.eth.gas_price
        print(f"Recomended gas price: {self.connection.from_wei(gas_price, 'gwei')} Gwei")
        if gas_price > gas_price_limit:
            print('Gas price very high')
            gas_price = gas_price_limit
        return nonce, gas_price

    def post_transaction(self, transaction, wait=0):
        signed_transaction = self.connection.eth.account.sign_transaction(transaction, self.key_wallet)
        transaction_hash = self.connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
        print(f"Transaction sent! Hash: {self.connection.to_hex(transaction_hash)}")
        if wait:
            try:
                print("Waiting for transaction receipt...")
                receipt = self.connection.eth.wait_for_transaction_receipt(transaction_hash, timeout=120, poll_latency=2)
                if receipt and receipt.get("status") == 1:
                    print("Done!", receipt.get("blockNumber"))
                    return 1, receipt
                else:
                    print("Rejected!")
                    return 0, 0
            except TimeExhausted:
                print("Transaction timed out!")
                return 9, 0
        else:
            return -1, 0

















# ===================================================================================== Operations with bot, simulation
class BotPos:
    def __init__(self, descriptor, sim, inst_main):        # chain argument
        self.chain = inst_main
        self.sim = sim
        params = BotPos.load_config()           # MUST DO REWRITEBLE WITH RUNING
        for key, value in params.items():
            setattr(self, key, value)
        # if not sim
        self.amm0 = self.chain.get_balance_token(0)
        self.amm1 = self.chain.get_balance_token(1)
        self.P_act_tick, self.P_act = self.chain.get_current_tick()
        #
        self.range_width = self.range_width_init
        # else can be done later
        self.slippage = 0.02
        # Is it needed? Calc with prices, ticks in level down
        # self.range_width_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_act + 0.5 * self.range_width_init) - self.chain.tick_from_price(self.P_act - 0.5 * self.range_width_init))
        # self.range_width_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_act + 0.5 * self.range_width_max) - self.chain.tick_from_price(self.P_act - 0.5 * self.range_width_max))
        # self.range_width_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_act + 0.5 * self.range_width_min) - self.chain.tick_from_price(self.P_act - 0.5 * self.range_width_min))

        self.prices_max = []
        self.prices_min = []
        self.prices = []
        self.balances = []
        self.balances_alt = []
        self.times = []

        engine = create_engine("sqlite:///data/positions.db")
        Base = declarative_base()
        Session = sessionmaker(bind=engine)
        class Position(Base):
            __tablename__ = "positions"
            id = Column(Integer, primary_key=True)
            descriptor = Column(Integer)
            position = Column(Integer)
            range_MIN = Column(Float)
            range_MAX = Column(Float)
            timestamp_IN = Column(DateTime)
            timestamp_OUT = Column(DateTime)
            token0_IN = Column(Float)
            token1_IN = Column(Float)
            token0_OUT = Column(Float)
            token1_OUT = Column(Float)
            token0_fee = Column(Float)
            token1_fee = Column(Float)
            token0_swap = Column(Float)
            token1_swap = Column(Float)
        # Base.metadata.create_all(engine)        # Once!
        session = Session()

        # pos1 = Position(token0_IN = 1000, token1_IN = 0.4, position = random.randint(100000, 999999), timestamp_IN = datetime.now())
        # session.add(pos1)
        # session.commit()

        # print('-'*20)
        # positions = session.query(Position).all()
        # for p in positions:
        #     print(p.id, p.token0_IN, p.token1_IN, p.position, p.timestamp_IN, p.timestamp_OUT)


        last_pos = (
            session.query(Position)
            .filter(Position.descriptor == descriptor)            # условие
            .order_by(Position.id.desc())                # сортировка по id убыв.
            .first()                                     # берём первую (т.е. последнюю по id)
        )
        if last_pos.timestamp_OUT:
            self.opened = 0
        else:
            self.opened = 1

        # last_pos.token0_IN = 1111
        # session.commit()

        # session.delete(last_pos)
        # session.commit()


    def proc_shift(self, mode):
        # new range.                                                            # need to price upd, after close
        if mode == 'UT':
            self.P_max = self.P_act + self.range_width * self.range_move_trend
            self.P_min = self.P_act - self.range_width * (1 - self.range_move_trend)
        elif mode == 'DT':
            self.P_min = self.P_act - self.range_width * self.range_move_trend
            self.P_max = self.P_act + self.range_width * (1 - self.range_move_trend)
        elif mode == 'UF':
            self.P_max = self.P_act + self.range_width * self.range_move_float
            self.P_min = self.P_act - self.range_width * (1 - self.range_move_float)
        elif mode == 'DF':
            self.P_min = self.P_act - self.range_width * self.range_move_float
            self.P_max = self.P_act + self.range_width * (1 - self.range_move_float)
        print('New range:', self.P_min, self.P_max, 'Width:', self.range_width)

    def proc_swap(self, mode):
        # do swap.
        if mode == 'UT' or mode == 'UF':                                        # need to check amm1
            self.k0 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 0)
            self.amm0_get = (self.k0 * self.amm1) / (1 + self.k0 * self.P_act)
            print("Needed to get per one token:", self.k0)
            print('Limit:', self.amm0_get * self.P_act * (1 + self.slippage))
            print('Need to output token:', self.amm0_get)
            self.chain.get_swap_ammount_router(self.amm0_get, self.amm0_get * self.P_act * (1 + self.slippage), 0, by='Q')

            # self.amm1 -= self.amm0_get * self.P_act
            # self.amm0 += self.amm0_get
            # am0new = k * am1 / (1 + k * p)                swap!
        elif mode == 'DT' or mode == 'DF':                                      # need to check amm0
            self.k1 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 1)
            self.amm1_get = (self.k1 * self.amm0 * self.P_act) / (self.k1 + self.P_act)
            self.chain.get_swap_ammount_router(self.amm1_get, self.amm1_get / self.P_act * (1 - self.slippage), 1, by='Q')
            # self.amm0 -= self.amm1_get / self.P_act
            # self.amm1 += self.amm1_get  
            # am1new = (k * am0 * p) / (k + p)              swap!
        self.amm0 = self.chain.get_balance_token(0)
        self.amm1 = self.chain.get_balance_token(1)

    def proc_open(self, mode):
        if mode == 'UT' or mode == 'UF':
            self.P_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_min), direction='s')
            self.bruto_max = BotPos.clc_rng(self.chain.price_from_tick(self.P_min_tick), self.chain.price_from_tick(self.P_act_tick), self.amm0, self.amm1)
            self.P_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.bruto_max), direction='s')
            # self.amm1_lock = self.amm1
            # self.amm0_lock = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, self.amm1_lock, 0)
            # self.L = self.amm1_lock / (math.sqrt(self.P_act) - math.sqrt(self.P_min))
            # self.L2 = self.amm0_lock / ((math.sqrt(self.P_max) - math.sqrt(self.P_act)) / (math.sqrt(self.P_max) * math.sqrt(self.P_act)))
        elif mode == 'DT' or mode == 'DF':
            self.P_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_max), direction='s')
            self.bruto_min = BotPos.clc_rng(self.chain.price_from_tick(self.P_max_tick), self.chain.price_from_tick(self.P_act_tick), self.amm0, self.amm1)
            self.P_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.bruto_min), direction='s')
            # self.bruto_min = BotPos.clc_rng(self.P_max, self.P_act, self.amm0, self.amm1)
            # self.P_min_tick = BotPos.prc_norm(self.bruto_min, 1, 1, 'l')
            # self.amm0_lock = self.amm0
            # self.amm1_lock = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, self.amm0_lock, 1)
            # self.L = self.amm1_lock / (math.sqrt(self.P_act) - math.sqrt(self.P_min))
            # self.L2 = self.amm0_lock / ((math.sqrt(self.P_max) - math.sqrt(self.P_act)) / (math.sqrt(self.P_max) * math.sqrt(self.P_act)))
        # entry po position. Get position liquidity
        self.chain.approve_token(self.amm0, 0, 'm', wait=1)
        self.chain.approve_token(self.amm1, 1, 'm', wait=1)
        self.status, self.id = self.chain.liq_add(self.P_min_tick, self.P_max_tick, self.amm0 * 0.99, self.amm1 * 0.99, wait=1)
        self.opened = 1
        # self.amm0 -= self.amm0_lock
        # self.amm1 -= self.amm1_lock
        # self.P_max = 1.0001 ** self.P_max_tick
        # self.P_min = 1.0001 ** self.P_min_tick

    def proc_close(self, mode):
        self.chain.liq_remove(self.id)
        self.chain.collect(self.id)
        self.chain.burn(self.id)
        # exit position. Return position liquidity
        # if mode == 'UT' or mode == 'UF':
        #     self.amm0_lock = 0
        #     self.amm1_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min))
        # elif mode == 'DT' or mode == 'DF':
        #     self.amm0_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min)) / (math.sqrt(self.P_max) * math.sqrt(self.P_min))
        #     self.amm1_lock = 0
        # calc statuses
        self.opened = 0
        # self.L = 0
        # self.amm0 += self.amm0_lock
        # self.amm1 += self.amm1_lock
        # self.amm0_lock = 0
        # self.amm1_lock = 0

    def proc_modify(self, mode):
        # new range width
        if mode == 'UT' or mode == 'DT':
            self.range_width *= self.range_scale_trend
        elif mode == 'UF' or mode == 'DF':
            self.range_width *= self.range_scale_float
        if self.range_width > self.range_width_max:
            self.range_width = self.range_width_max
        if self.range_width_tick < self.range_width_min:
            self.range_width = self.range_width_min
    
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
        else:
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.P_act_tick, self.P_act = self.chain.get_current_tick()

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
