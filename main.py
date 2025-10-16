from package import BotPos, ChainLink
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")



chain = ChainLink('arbitrum', 'weth', 'usdc', 'uniswap', 'test', 500)
pos = BotPos(1, 0, chain)



# =========================== ROUTINE ================================
while True:
    # Check step
    if pos.step == 0 or pos.step == 1:      # Begined
        pos.proc_shift()
        if pos.proc_swap() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(300)
            continue
        if pos.proc_open() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(300)
            continue
    elif pos.step == 2:                     # Opened
        pos.actuate_short(0)
        if pos.P_act > pos.P_max:
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(300)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'U'
            continue
        elif pos.P_act < pos.P_min:
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(300)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'D'
            continue
        if pos.pos_data.timestamp_IN and datetime.now() - pos.pos_data.timestamp_IN > timedelta(hours=24):
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(300)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'T'
            continue
        time.sleep(120)
    elif pos.step == 3 or pos.step == 4:
        if pos.proc_close() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(300)
            continue
    elif pos.step == 5:
        pos.proc_modify()
        pos.step = 0








