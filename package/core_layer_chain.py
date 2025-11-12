from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TimeExhausted
from web3.providers.persistent import WebSocketProvider
from web3.exceptions import Web3Exception, TimeExhausted, BadResponseFormat
import time
import os
import math
import json
from datetime import datetime
import random
import sys
sys.stdout.reconfigure(encoding="utf-8")

# ===================================================================================== Blockchain operations
class ChainLink:
    def __init__(self, blockchain, token0, token1, proto, wallet):
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
        self.key_rpc = os.getenv("INFURA_API")
        self.connection = Web3(Web3.HTTPProvider(self.rpc + self.key_rpc))                 # connect to node
        if self.connection.is_connected():
            print("Connected!")
        else:
            print("Not connected!")
        print('Address my:', self.address_wallet)
        self.address_pool = ''
        self.contract_token0 = self.connection.eth.contract(address=self.address_token0, abi=self.abi_token)
        self.contract_token1 = self.connection.eth.contract(address=self.address_token1, abi=self.abi_token)
        self.contract_factory = self.connection.eth.contract(address=self.address_factory, abi=self.abi_factory)
        self.contract_router = self.connection.eth.contract(address=self.address_router, abi=self.abi_router)
        self.contract_quoter = self.connection.eth.contract(address=self.address_quoter, abi=self.abi_quoter)
        self.contract_manager = self.connection.eth.contract(address=self.address_manager, abi=self.abi_manager)
        self.decimals0 = self.contract_token0.functions.decimals().call()
        self.name0 = self.contract_token0.functions.name().call()
        self.symbol0 = self.contract_token0.functions.symbol().call()
        self.decimals1 = self.contract_token1.functions.decimals().call()
        self.name1 = self.contract_token1.functions.name().call()
        self.symbol1 = self.contract_token1.functions.symbol().call()
        self.chain_id = self.connection.eth.chain_id
        self.address_pool_100 = self.contract_factory.functions.getPool(self.address_token0, self.address_token1, 100).call()
        self.address_pool_500 = self.contract_factory.functions.getPool(self.address_token0, self.address_token1, 500).call()
        self.address_pool_3000 = self.contract_factory.functions.getPool(self.address_token0, self.address_token1, 3000).call()
        self.contract_pool_100 = self.connection.eth.contract(address=self.address_pool_100, abi=self.abi_pool)
        self.contract_pool_500 = self.connection.eth.contract(address=self.address_pool_500, abi=self.abi_pool)
        self.contract_pool_3000 = self.connection.eth.contract(address=self.address_pool_3000, abi=self.abi_pool)
        self.tick_spacing_100 = self.contract_pool_100.functions.tickSpacing().call()
        self.tick_spacing_500 = self.contract_pool_500.functions.tickSpacing().call()
        self.tick_spacing_3000 = self.contract_pool_3000.functions.tickSpacing().call()
        self.reversed_100 = self.is_reversed(self.contract_pool_100, self.address_token0, self.address_token1)
        self.reversed_500 = self.is_reversed(self.contract_pool_500, self.address_token0, self.address_token1)
        self.reversed_3000 = self.is_reversed(self.contract_pool_3000, self.address_token0, self.address_token1)

        # self.dyn_pool_swich()
        print('-'*25, '\nInit chain layer completed\n')
        
    @staticmethod    
    def is_reversed(cont, ad_tok0, ad_tok1):
        addr0 = cont.functions.token0().call() 
        addr1 = cont.functions.token1().call()
        if addr0.lower() == ad_tok0.lower() and addr1.lower() == ad_tok1.lower():
            return 0
        else:
            return 1

    def get_balance_native(self, show=1):
        try:
            balance = self.connection.eth.get_balance(self.address_wallet)
        except (BadResponseFormat, Web3Exception) as e:
            print(f"Web3 error while fetching balance: {e}")
            time.sleep(300)
        except Exception as e:
            print(f"Unexpected error while fetching balance: {e}")
            time.sleep(300)
        else:
            self.balance_native = native = self.connection.from_wei(balance, 'ether')
        if show:
            print('Balance native :', self.balance_native)
        return native

    def get_balance_token(self, token, show=1):
        if token == 0:
            address = self.address_token0
            contract = self.contract_token0
            decimals = self.decimals0
            name = self.name0
            symbol = self.symbol0
        elif token == 1:
            address = self.address_token1
            contract = self.contract_token1
            decimals = self.decimals1
            name = self.name1
            symbol = self.symbol1
        try:
            balance = contract.functions.balanceOf(self.address_wallet).call()
        except (BadResponseFormat, Web3Exception) as e:
            print(f"Web3 error on call: {e}")
            time.sleep(30)
        except Exception as e:
            print(f"Unexpected error on call: {e}")
            time.sleep(30)
        else:
            balance_token = balance / 10**decimals
            if token == 0:
                self.balance_token0 = balance_token
            else:
                self.balance_token1 = balance_token
            if show:
                print("Balance", address, name, symbol, ':', balance_token)
            return balance_token
        if token == 0:
            return self.balance_token0
        else:
            return self.balance_token1

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
    
    def price_from_tick(self, tick, fee):
        if fee == 100:
            reversed = self.reversed_100
        elif fee == 500:
            reversed = self.reversed_500
        elif fee == 3000:
            reversed = self.reversed_3000
        if reversed:
            P = (1 / (1.0001**tick)) * 10**(self.decimals0 - self.decimals1)
        else:
            P = (1.0001**tick) * 10**(self.decimals0 - self.decimals1)
        return(P)

    def tick_from_price(self, P, fee):
        if fee == 100:
            reversed = self.reversed_100
        elif fee == 500:
            reversed = self.reversed_500
        elif fee == 3000:
            reversed = self.reversed_3000
        if reversed:
            tick = math.log(1 / P * 10**(self.decimals0 - self.decimals1)) / math.log(1.0001)
        else:
            tick = math.log(P * 10**(self.decimals1 - self.decimals0)) / math.log(1.0001)
        return(tick)
    
    def get_current_tick(self, fee, show=1):
        if fee == 100:
            cont = self.contract_pool_100
            reversed = self.reversed_100
        elif fee == 500:
            cont = self.contract_pool_500
            reversed = self.reversed_500
        elif fee == 3000:
            cont = self.contract_pool_3000
            reversed = self.reversed_3000
        try:
            slot0 = cont.functions.slot0().call()
        except (BadResponseFormat, Web3Exception) as e:
            print(f"Web3 error on call (price data parse): {e}")
            time.sleep(30)
            return self.current_tick, self.current_price
        except Exception as e:
            time.sleep(30)
            print(f"Unexpected error on call (price data parse): {e}")
            return self.current_tick, self.current_price
        self.current_tick = slot0[1]
        sqrtPriceX96 = slot0[0]
        price = (sqrtPriceX96 / 2**96) ** 2
        if reversed:
            self.current_price = (1 / price) * 10**(self.decimals0 - self.decimals1)
        else:
            self.current_price = price * 10**(self.decimals0 - self.decimals1)
        if show:
            print('Cur price:', round(self.current_price, 3), end=' ')
        return self.current_tick, self.current_price

    def get_liquidity(self, fee, tick=None):
        if fee == 100:
            cont = self.contract_pool_100
            reversed = self.reversed_100
        elif fee == 500:
            cont = self.contract_pool_500
            reversed = self.reversed_500
        elif fee == 3000:
            cont = self.contract_pool_3000
            reversed = self.reversed_3000
        if tick is None:
            try:
                l_row = cont.functions.liquidity().call()
                row_fee0 = cont.functions.feeGrowthGlobal0X128().call()
                row_fee1 = cont.functions.feeGrowthGlobal1X128().call()
            except Exception as e:
                print(f"Unexpected error on call (pool aux data parse): {e}")
                time.sleep(30)
                return 0, 0, 0
            # print(row_fee0, row_fee1)        
            fee0_real = row_fee0 / 2**128
            fee1_real = row_fee1 / 2**128
            # print(self.decimals0, self.decimals1)
            # print(l_row)
            if reversed:
                fee0 = fee1_real / 10**self.decimals1
                fee1 = fee0_real / 10**self.decimals0
            else:
                fee0 = fee0_real / 10**self.decimals0
                fee1 = fee1_real / 10**self.decimals1
            liquidity = l_row**2 / 10**(self.decimals0 + self.decimals1)
            # print(liquidity)
            # print(fee0, fee1)
            return liquidity, fee0, fee1
        else:
            tick_data = cont.functions.ticks(tick).call()
            liquidity_net = tick_data[0]
            liquidity_gross = tick_data[1]
            return liquidity_net, liquidity_gross            

    def tick_normalize(self, tick, fee, direction=''):
        if fee == 100:
            reversed = self.reversed_100
            spacing = self.tick_spacing_100
        elif fee == 500:
            reversed = self.reversed_500
            spacing = self.tick_spacing_500
        elif fee == 3000:
            reversed = self.reversed_3000
            spacing = self.tick_spacing_3000
        if reversed:
            if direction == 'smx':
                tick_corrected = tick - tick % spacing
            elif direction == 'smn':
                tick_corrected = tick - tick % spacing + spacing
            elif direction == 'mx':
                tick_corrected = math.floor(tick)
            elif direction == 'mn':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % spacing >= spacing / 2:
                    tick_corrected = tick - tick % spacing + spacing
                else:
                    tick_corrected = tick - tick % spacing
            else:
                tick_corrected = round(tick)
        else:
            if direction == 'smn':
                tick_corrected = tick - tick % spacing
            elif direction == 'smx':
                tick_corrected = tick - tick % spacing + spacing
            elif direction == 'mn':
                tick_corrected = math.floor(tick)
            elif direction == 'mx':
                tick_corrected = math.ceil(tick)
            elif direction == 's':
                if tick % spacing >= spacing / 2:
                    tick_corrected = tick - tick % spacing + spacing
                else:
                    tick_corrected = tick - tick % spacing
            else:
                tick_corrected = round(tick)
        return int(tick_corrected)

    def get_swap_ammount_quoter(self, amount, token, fee, by='I'):
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

    def get_swap_ammount_router(self, amount, amount_lim, token, fee, by='I', deadline=60, wait=1):
        print('\n!SWP!', end=' ')
        if fee == 100:
            cont = self.contract_pool_100
            reversed = self.reversed_100
        elif fee == 500:
            cont = self.contract_pool_500
            reversed = self.reversed_500
        elif fee == 3000:
            cont = self.contract_pool_3000
            reversed = self.reversed_3000
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
            events = cont.events.Swap().process_receipt(receipt)
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if reversed:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
        else:
            amm0_ok = 0
            amm1_ok = 0
        return status, amm0_ok, amm1_ok

    def liq_add(self, range_min, range_max, amount0, amount1, fee, deadline=60, wait=1):
        print('\n!ADD!', end=' ')
        if fee == 100:
            reversed = self.reversed_100
        elif fee == 500:
            reversed = self.reversed_500
        elif fee == 3000:
            reversed = self.reversed_3000
        amount0_scaled = int(amount0 * (10**self.decimals0))
        amount1_scaled = int(amount1 * (10**self.decimals1))
        if reversed:
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
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=0.17)
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
                if reversed:
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
    
    def liq_remove(self, token_id, fee, deadline=60, wait=1):
        print('\n!REM!', end=' ')
        if fee == 100:
            reversed = self.reversed_100
        elif fee == 500:
            reversed = self.reversed_500
        elif fee == 3000:
            reversed = self.reversed_3000
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
        status, receipt = self.post_transaction(transaction, wait)
        if status == 1:
            events = self.contract_manager.events.DecreaseLiquidity().process_receipt(receipt)
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if reversed:
                    amm0_ok = amm1 / (10**self.decimals0)
                    amm1_ok = amm0 / (10**self.decimals1)
                else:
                    amm0_ok = amm0 / (10**self.decimals0)
                    amm1_ok = amm1 / (10**self.decimals1)
        else:
            amm0_ok = 0
            amm1_ok = 0
        return status, amm0_ok, amm1_ok

    def collect(self, token_id, fee, wait=1):
        print('\n!COL!', end=' ')
        if fee == 100:
            reversed = self.reversed_100
        elif fee == 500:
            reversed = self.reversed_500
        elif fee == 3000:
            reversed = self.reversed_3000
        nonce, gas_price = self.pre_transaction(gas_price_limit_gwei=0.17)
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
            for e in events:
                amm0 = e["args"]["amount0"]
                amm1 = e["args"]["amount1"]
                if reversed:
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
        nonce, gas_price = self.pre_transaction()
        transaction = self.contract_manager.functions.burn(token_id).build_transaction({
            "from": self.address_wallet,
            "gas": 200000,
            "gasPrice": int(gas_price * 1.05),
            "nonce": nonce,
            "chainId": self.chain_id,
        })
        return self.post_transaction(transaction, wait)

    def pre_transaction(self, gas_price_limit_gwei=0.15):
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
