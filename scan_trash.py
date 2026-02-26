from package import ChainLink2
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")

import asyncio
import json


def main():
    parser = argparse.ArgumentParser(description="Mode switcher for bot.")
    parser.add_argument(
        "--mode",
        type=str,
        default='scanner',
        help="bot mode, pools scanner or watchdog",
    )
    parser.add_argument(
        "--chain",
        type=str,
        default='mainnet',
        help="bot operating blockchain",
    )
    args = parser.parse_args()
    if args.mode == 'scanner':
        bot_mode = 0
    elif args.mode == 'watchdog':
        bot_mode = 1
    elif args.mode == 'operate':
        bot_mode = 2
    else:
        print('Unknown mode arg...')
        return


    chain = ChainLink2(args.chain, 'uni3')
    cycles = 0

    chain.scan_tokens(short=bot_mode)
    chain.scan_pools()
    chain.scan_pool_statistic(1)

    if not bot_mode:
        while True:
            print_flag = cycles % 24 == 0
            print('\nScan', cycles, 'starts', datetime.now())
            chain.scan_pool_statistic(1, print_flag, use='Dust')
            print()
            chain.scan_pool_statistic(1, print_flag, use='Work')
            # chain.check_arbitrage_possibilities()
            time.sleep(3600)
            cycles += 1

    elif bot_mode == 1:
        chain.scan_pool_statistic(1)
    
    elif bot_mode == 2:
        chain.manual_swap_1()
        return

    else:
        return

    async def main_async():
        tasks = []

        for base, quote, fee in [
            ('ETH', 'weETH', 100),
            ('ETH', 'weETH', 500),
            ('ETH', 'weETH', 3000),
            ('ETH', 'rETH', 100),
            ('ETH', 'rETH', 500),
            ('ETH', 'rETH', 3000),
        ]:
        
            key, value = chain.resolve_pool_key(chain.pools_data, base, quote, fee)
            tasks.append(chain.listener(key, value))

        await asyncio.gather(*tasks)

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
