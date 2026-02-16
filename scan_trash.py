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


    chain = ChainLink2('polygon', 'uni3')
    cycles = 1

    chain.scan_tokens(short=bot_mode)
    chain.scan_pools()

    if not bot_mode:
        while True:
            print_flag = cycles % 12 == 0
            print('\nScan', cycles, 'starts', datetime.now())
            if cycles == 1:
                chain.scan_pool_statistic(2)
            else:
                chain.scan_pool_statistic(2, print_flag, use='Dust')
                print()
                chain.scan_pool_statistic(2, print_flag, use='Work')
            chain.check_arbitrage_possibilities()
            time.sleep(7200)
            cycles += 1

    elif bot_mode == 1:
        chain.scan_pool_statistic(2)
    
    elif bot_mode == 2:
        chain.manual_swap_1()

    else:
        return

    async def main_async():
        tasks = []

        for base, quote, fee in [
            ('ETH', 'wETH', 3000),
            ('ETH', 'wETH', 500),
            ('wETH', 'USDT', 3000),
            ('wETH', 'DAI', 3000),
        ]:
        
            key, value = chain.resolve_pool_key(chain.pools_data, base, quote, fee)
            tasks.append(chain.listener(key, value))

        await asyncio.gather(*tasks)

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
