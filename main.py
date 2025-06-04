from utils.botcore import LiqPos, ChainLink



chain = ChainLink('arbitrum', 'weth', 'usdc', 'uniswap', 'test', 500)
chain.get_balance_native()
chain.get_balance_token(0)
chain.get_balance_token(1)