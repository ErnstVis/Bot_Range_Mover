from package import ChainLink2
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


chain = ChainLink2('polygon', 'uni3')
cycles = 1
test_mode = True

chain.scan_tokens(short=test_mode)
chain.scan_pools()

if not test_mode:
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

else:
    chain.scan_pool_statistic(2)
    while True:
        pass





