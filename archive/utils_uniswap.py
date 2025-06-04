from web3 import Web3
import time

def get_pool_teo_price(pool_ctr):
    start_time = time.time()
    slot0 = pool_ctr.functions.slot0().call()
    price96 = slot0[0]
    price = (price96 / 2**96)**2
    price_corrected = price * 10**(18-6)
    #print('Teory price:', price_corrected)
    end_time = time.time()
    delta_t = end_time - start_time
    return price_corrected, delta_t


def get_pool_teo_price_inv(pool_ctr):
    start_time = time.time()
    slot0 = pool_ctr.functions.slot0().call()
    price96 = slot0[0]
    price = (price96 / 2**96)**2
    price_inverted = 1/price
    price_corrected = price_inverted * 10**(18-6)
    #print('Slot0:', slot0[0])
    end_time = time.time()
    delta_t = end_time - start_time
    return price_corrected, delta_t


def get_pool_price_usdtoeth(amount, quoter, tokenA, tokenB, fee):
    start_time = time.time()
    #amount_in = web3.to_wei(act_volume, "ether")
    amount_in = amount * (10 ** 6)
    raw_price = quoter.functions.quoteExactInputSingle(
        tokenA, tokenB, fee, amount_in, 0
    ).call()

    # scale_factor = 10 ** 6
    # scaled_price = raw_price / scale_factor
    # price_quoter = scaled_price / act_volume
    scaled_price = raw_price / (10 ** 18)
    price_quoter = scaled_price / amount
    #print("Quoter price - buy:", 1/price_quoter)
    end_time = time.time()
    delta_t = end_time - start_time
    return 1/price_quoter, delta_t


def get_pool_price_ethtousd(amount, quoter, connection, tokenA, tokenB, fee):
    start_time = time.time()
    amount_in = connection.to_wei(amount, "ether")
    raw_price = quoter.functions.quoteExactInputSingle(
        tokenA, tokenB, fee, amount_in, 0
    ).call()
    scaled_price = raw_price / (10 ** 6)
    price_quoter = scaled_price / amount
    #print("Quoter price - sell:", price_quoter)
    end_time = time.time()
    delta_t = end_time - start_time
    return price_quoter, delta_t

def get_analyse_data(pool_contract):
    current_liquidity = pool_contract.functions.liquidity().call()
    slot0 = pool_contract.functions.slot0().call()
    liqid_from_proto = current_liquidity**0.5
    # token0calc = (liqid_from_proto**0.5) / (price_corrected**0.5)
    # token1calc = (liqid_from_proto**0.5) * (price_corrected**0.5)
    if slot0[1]%10 < 5:
        index = slot0[1]-(slot0[1]%10)
    else:
        index = slot0[1]-(slot0[1]%10)+10
    tick_data = pool_contract.functions.ticks(index).call()
    liquidity_net = tick_data[0]**0.5
    return slot0[1], liqid_from_proto**0.5, liquidity_net**0.5



def swap_token_router(amount, connection, amount_out_min, deadline, router_contract, tokenA, tokenB, fee, tokenA_cont, tokenB_cont, wallet, private_key):
    decimalsA = tokenA_cont.functions.decimals().call()
    amount_scaled = int(amount * 10**decimalsA)
    decimalsB = tokenB_cont.functions.decimals().call()
    amount_out_scaled = int(amount_out_min * 10**decimalsB)
    nonce = connection.eth.get_transaction_count(wallet)
    params = {
    "tokenIn": tokenA,
    "tokenOut": tokenB,
    "fee": fee,
    "recipient": wallet,
    "deadline": int(time.time()) + deadline,
    "amountIn": amount_scaled,
    "amountOutMinimum": amount_out_scaled,
    "sqrtPriceLimitX96": 0,
    }
    tx = router_contract.functions.exactInputSingle(params).build_transaction({
        'chainId': 137,
        'gas': 300000,
        'gasPrice': int(connection.eth.gas_price * 1.1),
        'nonce': nonce
    })
    signed_tx = connection.eth.account.sign_transaction(tx, private_key)
    tx_hash = connection.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Swap sended: {connection.to_hex(tx_hash)}")
    return connection.to_hex(tx_hash)


# =============================================================--NOT-TESTED--=============================================================
def swap_token(amount, connection, price, pool_contract, token0_cont, token1_cont, wallet, private_key):
    decimalsA = token0_cont.functions.decimals().call()
    amount_scaled = int(amount * 10**decimalsA)
    print(amount_scaled)
    nonce = connection.eth.get_transaction_count(wallet)
    tx = pool_contract.functions.swap({
        wallet,
        False,
        amount_scaled,
        price,
        bytes()
    }).build_transaction({
        'chainId': 137,
        'gas': 310000,
        'gasPrice': int(connection.eth.gas_price * 1.1),
        'nonce': nonce
    })
    # ).call()
    signed_tx = connection.eth.account.sign_transaction(tx, private_key)
    tx_hash = connection.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Swap sended: {connection.to_hex(tx_hash)}")
    return connection.to_hex(tx_hash)