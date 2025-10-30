from package import BotPos, ChainLink
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")



chain = ChainLink('arbitrum', 'weth', 'usdc', 'uniswap', 'test')
pos = BotPos(1, 0, chain)



# =========================== ROUTINE ================================
while True:
    # Check step
    if pos.step == 0:      # Begined
        pos.proc_shift()
        if pos.proc_swap() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(30)
            continue
    elif pos.step == 1:
        if pos.proc_open() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(30)
            continue
    elif pos.step == 2:                     # Opened
        pos.actuate_short()
        if pos.P_act > pos.P_max:
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(30)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'U'
            pos.params["prev_mode"] = pos.prev_mode
            pos.params["mode"] = pos.mode
            pos.save_config(pos.params)
            continue
        elif pos.P_act < pos.P_min:
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(30)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'D'
            pos.params["prev_mode"] = pos.prev_mode
            pos.params["mode"] = pos.mode
            pos.save_config(pos.params)
            continue
        elif pos.pos_data.timestamp_IN and datetime.now() - pos.pos_data.timestamp_IN > timedelta(hours=pos.dyn_period_scale()) and pos.test_min_width():
            if pos.proc_close() != 1:
                print('\nSTATUS NOT 1...')
                time.sleep(30)
                continue
            pos.prev_mode = pos.mode
            pos.mode = 'T'
            pos.params["prev_mode"] = pos.prev_mode
            pos.params["mode"] = pos.mode
            pos.save_config(pos.params)
            continue
        time.sleep(60)
    elif pos.step == 3 or pos.step == 4:
        if pos.proc_close() != 1:
            print('\nSTATUS NOT 1...')
            time.sleep(30)
            continue
    elif pos.step == 5:
        pos.proc_modify()
        pos.params["range_width"] = pos.range_width
        pos.save_config(pos.params)
        pos.step = 0








