import utils_chain


ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
POLYGON_RPC = "https://polygon-rpc.com/"
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



# ========================================================== POLYGON ==========================================================
chain_conn = utils_chain.init_chain(POLYGON_RPC)

eth_token = weth_token_polygon
usd_token = usdc_token_polygon
token_abi = utils_chain.load_abi("polygon/weth.json")
eth_contract = chain_conn.eth.contract(address=eth_token, abi=token_abi)
usd_contract = chain_conn.eth.contract(address=usd_token, abi=token_abi)

quoter_abi = utils_chain.load_abi("com/uniswap_quoter.json")
quoter_address = quoter_uniswap_polygon
quoter_contract = chain_conn.eth.contract(address=quoter_address, abi=quoter_abi)
factory_abi = utils_chain.load_abi("com/uniswap_factory.json")
factory_address = factory_uniswap_polygon
factory_contract = chain_conn.eth.contract(address=factory_address, abi=factory_abi)
router_abi = utils_chain.load_abi("com/uniswap_router.json")
router_address = router_uniswap_polygon
router_contract = chain_conn.eth.contract(address=router_address, abi=router_abi)

pool_3_address = factory_contract.functions.getPool(eth_token, usd_token, 3000).call()
pool_5_address = factory_contract.functions.getPool(eth_token, usd_token, 500).call()
print(f"Address 0.3%: {pool_3_address}")
print(f"Address 0.05%: {pool_5_address}")
pool_abi = utils_chain.load_abi("com/uniswap_pool.json")
pool_3_contract = chain_conn.eth.contract(address=pool_3_address, abi=pool_abi)
pool_5_contract = chain_conn.eth.contract(address=pool_5_address, abi=pool_abi)
# ========================================================== POLYGON ==========================================================


# ========================================================== ARMITRUM ==========================================================
# # Preparing for main routine - ARBITRUM
# chain_conn = utils_chain.init_chain(ARBITRUM_RPC)

# weth_token = weth_token_arbitrum
# usdc_token = usdc_token_arbitrum

# pool_3_address = wethusdc03_uniswap_arbitrum
# pool_3_abi = utils_chain.load_abi("arbitrum/uniswap_wethusdc03.json")
# pool_3_contract = chain_conn.eth.contract(address=pool_3_address, abi=pool_3_abi)

# pool_5_address = wethusdc005_uniswap_arbitrum
# pool_5_abi = utils_chain.load_abi("arbitrum/uniswap_wethusdc005.json")
# pool_5_contract = chain_conn.eth.contract(address=pool_5_address, abi=pool_5_abi)

# quoter_address = quoter_uniswap_polygon
# quoter_abi = utils_chain.load_abi("arbitrum/uniswap_quoter.json")
# quoter_contract = chain_conn.eth.contract(address=quoter_address, abi=quoter_abi)


# ========================================================== OPTIMISM ==========================================================
# chain, tokens
# chain_conn = utils_chain.init_chain(OPTIMISM_RPC)
# weth_token = weth_token_optimism
# usdc_token = usdc_token_optimism

# # uniswap aux contracts
# quoter_abi = utils_chain.load_abi("com/uniswap_quoter.json")
# quoter_address = quoter_uniswap_optimism
# quoter_contract = chain_conn.eth.contract(address=quoter_address, abi=quoter_abi)
# factory_abi = utils_chain.load_abi("com/uniswap_factory.json")
# factory_address = factory_uniswap_optimism
# factory_contract = chain_conn.eth.contract(address=factory_address, abi=factory_abi)

# # pools dynamic get
# pool_address_3 = factory_contract.functions.getPool(weth_token, usdc_token, 3000).call()
# print(f"Address 0.3%: {pool_address_3}")
# pool_address_5 = factory_contract.functions.getPool(weth_token, usdc_token, 500).call()
# print(f"Address 0.05%: {pool_address_5}")

# # pools contracts
# pool_abi = utils_chain.load_abi("com/uniswap_pool.json")
# pool_3_address = pool_address_3
# pool_3_contract = chain_conn.eth.contract(address=pool_3_address, abi=pool_abi)
# pool_5_address = pool_address_5
# pool_5_contract = chain_conn.eth.contract(address=pool_5_address, abi=pool_abi)
