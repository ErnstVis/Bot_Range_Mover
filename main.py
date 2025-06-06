from utils.botcore import LiqPos, ChainLink
import time



chain = ChainLink('polygon', 'weth', 'usdc', 'uniswap', 'test', 500)
chain.get_balance_native()
chain.get_balance_token(0)
chain.get_balance_token(1)

# i = 0
# while True:
#     result = chain.send_native(0.1, wait=1)
#     if result == 1:
#         break
#     elif result == 0:
#         time.sleep(60)
#     i += 1
#     print('not ok, trying again', i)



# chain.send_token(0.1, 1, wait=1)

# chain.approve_token(0.1, 1, wait=1)

print(chain.get_pool_teo_price())
print(chain.decimals0, chain.decimals1)

chain.scan_liquidity()



