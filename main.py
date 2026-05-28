from package import BotPos, ChainLink
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


""" 
Main working version 1.0 
One pair, dynamic range moving bot with uniswap v3, fee level auto selection
"""

def main():
    parser = argparse.ArgumentParser(description="Example script with arguments.")
    parser.add_argument(
        "--mode",
        type=str,
        default='arb_uni3_eth',
        help="bot mode, chain, proto, etc",
    )    
    parser.add_argument(
        "--trade",
        type=str,
        default='on',
        help="bot mode, chain, proto, etc",
    )
    args = parser.parse_args()
    if args.mode == 'arb_uni3_eth':
        ch = 'arbitrum'
        tok0 = 'weth'
        tok1 = 'usdc'
        proto = 'uniswap'
        desc = 1
        print('Running in arbitrum chain, uni3 proto, eth usdc... Descriptor 1')
    elif args.mode == 'pol_uni3_eth':
        ch = 'polygon'
        tok0 = 'weth'
        tok1 = 'usdt'
        proto = 'uniswap'
        desc = 2
        print('Running in polygon chain, uni3 proto, weth usdt... Descriptor 2')
    elif args.mode == 'pol_uni3_mai':
        ch = 'polygon'
        tok0 = 'frax'
        tok1 = 'mai'
        proto = 'uniswap'
        desc = 3
        print('Running in polygon chain, uni3 proto, eth sol... Descriptor 3')
    else:
        print('Unknown mode arg...')
        return
    if args.trade == 'on':
        trade_on = 1
        print('Trading is ON')
    elif args.trade == 'once':
        trade_on = 2
        print('Manualy swift')
    else:
        trade_on = 0
        print('Trading is OFF')

    chain = ChainLink(ch, tok0, tok1, proto, 'test')
    inst = BotPos(desc, 0, chain)

    # =========================== ROUTINE ================================
    count = 0
    while True:
        # JOB PROCESSING OR JUST DATA COLLECTION
        if trade_on == 1:
            if inst.step == 0:      # Begined
                inst.proc_shift()
            elif inst.step == 10:
                if inst.proc_swap() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
            elif inst.step == 1:
                if inst.proc_open() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
                inst.params = inst.load_config(desc)
                inst.params["range_width"] = inst.P_max - inst.P_min
                inst.params["L_fee"] = inst.L_fee
                inst.save_config(inst.params, desc)
            elif inst.step == 2:                     # Opened
                if count >= 120:
                    inst.actuate_win_slow()
                    count = 0
                else:
                    inst.actuate_win_reg()
                if inst.P_act > inst.P_max:
                    if inst.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if inst.mode != 'T':
                        inst.prev_mode = inst.mode
                    inst.mode = 'U'
                    inst.params = inst.load_config(desc)
                    inst.params["prev_mode"] = inst.prev_mode
                    inst.params["mode"] = inst.mode
                    inst.save_config(inst.params, desc)
                    continue
                elif inst.P_act < inst.P_min:
                    if inst.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if inst.mode != 'T':
                        inst.prev_mode = inst.mode
                    inst.mode = 'D'
                    inst.params = inst.load_config(desc)
                    inst.params["prev_mode"] = inst.prev_mode
                    inst.params["mode"] = inst.mode
                    inst.save_config(inst.params, desc)
                    continue
                elif (
                    inst.timestamp_IN                       # if opened 
                    and datetime.now() - inst.timestamp_IN
                    > timedelta(hours=inst.dyn_period_scale())       # if time to reopen
                    and inst.test_range_mod()                        # if logic allows
                ):
                    if inst.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if inst.mode != 'T':
                        inst.prev_mode = inst.mode
                    inst.mode = 'T'
                    inst.params = inst.load_config(desc)
                    inst.params["prev_mode"] = inst.prev_mode
                    inst.params["mode"] = inst.mode
                    inst.save_config(inst.params, desc)
                    continue
                time.sleep(120)
            elif inst.step == 3 or inst.step == 4:
                if inst.proc_close() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
            elif inst.step == 5:
                inst.proc_modify()
                inst.chain.L_fee = inst.L_fee         # Put best pool of last hour to new position
                inst.step = 0

        elif trade_on == 2:
            if inst.step == 2 or inst.step == 3 or inst.step == 4:
                print('\nManual close triggered...')
                if inst.proc_close() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
                break
            elif inst.step == 5:
                inst.step = 10
                inst.P_min = inst.init_min
                inst.P_max = inst.init_max
                inst.range_width = inst.P_max - inst.P_min
                inst.chain.L_fee = inst.L_fee
            elif inst.step == 10:
                print('\nManual swap triggered...')
                if inst.proc_swap() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
                break
            elif inst.step == 1:
                print('\nManual open triggered...')
                if inst.proc_open() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
                inst.params = inst.load_config(desc)
                inst.params["range_width"] = inst.P_max - inst.P_min
                inst.params["L_fee"] = inst.L_fee
                inst.save_config(inst.params, desc)
                break

        else:
            if count >= 120:
                inst.actuate_win_slow()
                count = 0
            else:
                inst.actuate_win_reg()
            time.sleep(120)
        count += 1

if __name__ == "__main__":
    main()