from utils.botcore import LiqPos, ChainLink
import time



chain = ChainLink('polygon', 'usdc', 'weth', 'uniswap', 'test', 500)
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




print('-'*25)
tick, price = chain.get_current_tick()
print('current:', tick, price)


tick_max = chain.tick_normalize(chain.tick_from_price(price * 1.05), 'smx')
tick_min = chain.tick_normalize(chain.tick_from_price(price * 0.95), 'smn')
print('high:', tick_max, chain.price_from_tick(tick_max))
print('low:', tick_min, chain.price_from_tick(tick_min))

# print(chain.decimals0, chain.decimals1)

# chain.approve_token(0, 0, 'm', wait=1)
# chain.approve_token(0, 1, 'm', wait=1)
# print("Allowance0:", allowance0)

print(chain.allowance(1, 'm'))

# print(chain.liq_add(tick_min, tick_max, 1, 0.00025, wait=1))

id = 2667007
# chain.liq_remove(id)
# chain.collect(id)
# chain.burn(id)