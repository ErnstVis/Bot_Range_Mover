from package import BotPos, ChainLink
import time



chain = ChainLink('arbitrum', 'weth', 'usdc', 'uniswap', 'test', 500)
pos = BotPos(1, 0, chain)



# =========================== ROUTINE ================================
while True:
    # Check step
    if pos.step == 0 or pos.step == 1:      # Begined
        pos.proc_shift()
        if pos.proc_swap() != 1:
            break
        if pos.proc_open() != 1:
            break
    elif pos.step == 2:                     # Opened
        if pos.P_act > pos.P_max:
            if pos.proc_close() != 1:
                break
            pos.prev_mode = pos.mode
            pos.mode = 'U'
            continue
        elif pos.P_act < pos.P_min:
            if pos.proc_close() != 1:
                break
            pos.prev_mode = pos.mode
            pos.mode = 'D'
            continue
        time.sleep(20)
        pos.actuate()
    elif pos.step == 3 or pos.step == 4:
        if pos.proc_close() != 1:
            break
    elif pos.step == 5:
        pos.proc_modify()
        pos.step = 0

print('Emergency exit...')






