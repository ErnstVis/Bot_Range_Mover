import utils_chain
import time


ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
POLYGON_RPC = "https://polygon-rpc.com"
OPTIMISM_RPC = "https://mainnet.optimism.io"


# Protocol adresses
quoter_uniswap_polygon = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6'
router_uniswap_polygon = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
factory_uniswap_polygon = '0x1F98431c8aD98523631AE4a59f267346ea31F984'
quoter_uniswap_arbitrum = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6'
factory_uniswap_optimism = '0x1F98431c8aD98523631AE4a59f267346ea31F984'
quoter_uniswap_optimism = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6'

# Token addresses
usdc_token_polygon = '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359'
usdt_token_polygon = '0xc2132D05D31c914a87C6611C10748AEb04B58e8F'
weth_token_polygon = '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
weth_token_arbitrum = '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
usdc_token_arbitrum = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'
weth_token_optimism = '0x4200000000000000000000000000000000000006'
usdc_token_optimism = '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85'

# Pool addresses
wethusdt03_uniswap_polygon = '0x4CcD010148379ea531D6C587CfDd60180196F9b1'
wethusdt005_uniswap_polygon = '0xBB98B3D2b18aeF63a3178023A920971cf5F29bE4'
wethusdc03_uniswap_arbitrum = '0xc473e2aEE3441BF9240Be85eb122aBB059A3B57c'
wethusdc005_uniswap_arbitrum = '0xC6962004f452bE9203591991D15f6b388e09E8D0'




# # ========================================================== OPTIMISM ==========================================================
# # chain, tokens
# chain_conn = utils_chain.init_chain(OPTIMISM_RPC)
# weth_token = weth_token_optimism
# usdc_token = usdc_token_optimism
# token_abi = utils_chain.load_abi("optimism/weth.json")
# weth_contract = chain_conn.eth.contract(address=weth_token, abi=token_abi)
# usdc_contract = chain_conn.eth.contract(address=usdc_token, abi=token_abi)

# # uniswap aux contracts
# quoter_abi = utils_chain.load_abi("com/uniswap_quoter.json")
# quoter_address = quoter_uniswap_optimism
# quoter_contract = chain_conn.eth.contract(address=quoter_address, abi=quoter_abi)
# factory_abi = utils_chain.load_abi("com/uniswap_factory.json")
# factory_address = factory_uniswap_optimism
# factory_contract = chain_conn.eth.contract(address=factory_address, abi=factory_abi)
# # ========================================================== OPTIMISM ==========================================================

# ========================================================== POLYGON ==========================================================
# chain, tokens
chain_conn = utils_chain.init_chain(POLYGON_RPC)
eth_token = weth_token_polygon
usd_token = usdt_token_polygon
token_abi = utils_chain.load_abi("polygon/weth.json")
eth_contract = chain_conn.eth.contract(address=eth_token, abi=token_abi)
usd_contract = chain_conn.eth.contract(address=usd_token, abi=token_abi)

# uniswap aux contracts
quoter_abi = utils_chain.load_abi("com/uniswap_quoter.json")
quoter_address = quoter_uniswap_polygon
quoter_contract = chain_conn.eth.contract(address=quoter_address, abi=quoter_abi)
factory_abi = utils_chain.load_abi("com/uniswap_factory.json")
factory_address = factory_uniswap_polygon
factory_contract = chain_conn.eth.contract(address=factory_address, abi=factory_abi)
# ========================================================== POLYGON ==========================================================




# pools dynamic get
pool_3_address = factory_contract.functions.getPool(eth_token, usd_token, 3000).call()
pool_5_address = factory_contract.functions.getPool(eth_token, usd_token, 500).call()
print(f"Address 0.3%: {pool_3_address}")
print(f"Address 0.05%: {pool_5_address}")

# pools contracts
pool_abi = utils_chain.load_abi("com/uniswap_pool.json")
pool_3_contract = chain_conn.eth.contract(address=pool_3_address, abi=pool_abi)
pool_5_contract = chain_conn.eth.contract(address=pool_5_address, abi=pool_abi)

# current_liquidity_3 = pool_3_contract.functions.liquidity().call()

# slot0_3 = pool_3_contract.functions.slot0().call()
# print(f"Liquid for 0.3% pool: {current_liquidity_3}")
# print(f"Price 0.3% pool: {slot0_3}")

current_liquidity = pool_5_contract.functions.liquidity().call()
slot0 = pool_5_contract.functions.slot0().call()

# print('Liquidity:', current_liquidity)
# print('Price:', slot0[0])
# print('Tick:', slot0[1])


# ================================================================================================== AMOUNTS


sqrt_price = slot0[0] / 2**96
price = sqrt_price**2
price_inverted = 1/price # depend of tokens positions
price_corrected = price * 10**(18-6)
print('Price from slot0:', price_corrected)

print(slot0[1])
# optimism bug on 193470, return 1
print('Price from tick:', 1.0001**slot0[1]*10**12) # depend of tokens positions
print()
print('From contract balance:')


balance0 = utils_chain.get_balance_token(eth_contract, pool_5_address)
balance1 = utils_chain.get_balance_token(usd_contract, pool_5_address)
print()
liqid_from_proto = current_liquidity**0.5
print('Avrage sqrt:', (balance0 * balance1)**0.5, ', Liquidity from pool calculation:', liqid_from_proto**0.5)
print()

token0calc = (liqid_from_proto**0.5) / (price_corrected**0.5)
token1calc = (liqid_from_proto**0.5) * (price_corrected**0.5)

print('From liquidity calculation balances:')
print(token0calc)
print(token1calc)




# ================================================================================================== TICKS
print()
print(current_liquidity)
print(slot0[1])
print()
start_scan = slot0[1]-200-(slot0[1]%10)
for i in range(41):
    # time.sleep(1)
    tick_data = pool_5_contract.functions.ticks(start_scan+i*10).call()
    print(1.0001**(start_scan+i*10)*10**12)
    liquidity_net = tick_data[0]
    liquidity_gross = tick_data[1]
    print(f"Net liquidity: {(liquidity_net**0.5)**0.5}")
    print(f"Cummulative liquidity: {(abs(liquidity_gross)**0.5)**0.5}")
    print()

# tick_data2 = pool_5_contract.functions.ticks(193470).call()
# print(193470)
# print(f"Net liquidity: {tick_data2[0]}")
# print(f"Cummulative liquidity: {tick_data2[1]}")

# ================================================================================================== TICK MAP

# print()
# word_index = (slot0[1] // 256) // 10 - 10
# print(slot0[1] // 256)
# for i in range(25):
#     tick_bitmap = pool_5_contract.functions.tickBitmap(word_index+i).call()
#     print(i-10, ':', tick_bitmap)
#     #time.sleep(0.5)
