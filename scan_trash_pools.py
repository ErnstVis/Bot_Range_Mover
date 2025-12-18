from package import BotPos, ChainLink
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")



chain = ChainLink('polygon', 'frax', 'mai', 'uniswap', 'test')
# pos = BotPos(3, 0, chain)


test_pool = '0xF5D085c669F63D9983Dc57b629b235793d009B0E'

TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "FRAX": "0x45c32fA6DF82ead1e2EF74d17b76547EDdFaFF89",
    "MAI": "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1",
    "CRV": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
    "PAXG": "0x553d3D295e0f695B9228246232eDF400ed3560B5",
    "GMT": "0x714DB550b574b3E927af3D93E26127D15721D4C2",
    "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",    
}
FEE_TIERS = [100, 500, 3000, 10000]

def build_pool_index():
    pools = {}

    token_list = list(TOKENS.keys())

    print("Scanning Uniswap v3 pools in Polygon...\n")

    for i in range(len(token_list)):
        for j in range(i + 1, len(token_list)):
            tokenA = token_list[i]
            tokenB = token_list[j]
            t0 = TOKENS[tokenA]
            t1 = TOKENS[tokenB]

            for fee in FEE_TIERS:
                pool = chain.contract_factory.functions.getPool(t0, t1, fee).call()

                if pool != "0x0000000000000000000000000000000000000000":
                    pool_contract = chain.connection.eth.contract(address=pool, abi=chain.abi_pool)
                    liquidity = pool_contract.functions.liquidity().call()
                    if liquidity > 1_000_000 and liquidity < 1000_000_000:
                        key = (tokenA, tokenB, fee)
                        pools[key] = pool
                        print('OK--- ', end='')
                    elif liquidity >= 1_000_000_000:
                        print('hi... ', end='')
                    else:
                        print('lo... ', end='')
                    print(
                        f" | {tokenA:<6} / {tokenB:<6} | "
                        f"Fee: {fee:<5} | "
                        f"Pool: {pool} | "
                        f"Liquidity: {liquidity:<15}"
                    )

    print(f"\nTotal pools found: {len(pools)}\n")
    return pools


# build_pool_index()

chain.get_current_tick(fee=500)
print()
print(chain.get_swap_ammount_quoter(1, 0, 'I', fee=500))
print(chain.get_swap_ammount_quoter(1, 1, 'I', fee=500))
# print(chain.get_swap_ammount_quoter(0.5, 0, 'Q', fee=500))
# print(chain.get_swap_ammount_quoter(0.5, 1, 'Q', fee=500))