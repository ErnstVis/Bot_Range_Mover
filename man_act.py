from package import BotPos, ChainLink
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


chain = ChainLink('arbitrum', 'weth', 'usdc', 'uniswap', 'test', 500)
pos = BotPos(1, 0, chain)

# pos.step = 2
# pos.id = 4921445
# pos.proc_close()



# pos.proc_shift("UT")
# pos.proc_swap("UT")
# pos.proc_open("UT")

# pos.chain.send_token(2.377, 1)
# pos.chain.send_native(9.824)