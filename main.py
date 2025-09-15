from utils.botcore import BotPos, ChainLink
import time



chain = ChainLink('polygon', 'weth', 'usdc', 'uniswap', 'test', 500)


# chain.send_token(0.002, 1)

print('-'*25)
pos = BotPos(0, 0, chain)
print('-'*25)




#pos.proc_shift("UT")
# pos.proc_swap("UT")

#pos.proc_open("UT")




# tick_max = chain.tick_normalize(chain.tick_from_price(price * 1.05), 'smx')
# tick_min = chain.tick_normalize(chain.tick_from_price(price * 0.95), 'smn')
# print('high:', tick_max, chain.price_from_tick(tick_max))
# print('low:', tick_min, chain.price_from_tick(tick_min))

# print(chain.decimals0, chain.decimals1)

# chain.approve_token(0.000533227808106748, 0, 'm', wait=1)
# chain.get_swap_ammount_router(0.000533227808106748, 0.000533227808106748 * price * (1-pos.slippage), 1)

# chain.approve_token(0, 1, 'm', wait=1)
# print("Allowance0:", allowance0)

# print(chain.allowance(1, 'm'))

# print(chain.liq_add(tick_min, tick_max, 1, 0.00025, wait=1))

# id = 2667007
# chain.liq_remove(id)
# chain.collect(id)
# chain.burn(id)