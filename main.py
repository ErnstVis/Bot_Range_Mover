from package import BotPos, ChainLink
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")

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
        trade_on = True
        print('Trading is ON')
    else:
        trade_on = False
        print('Trading is OFF')

    chain = ChainLink(ch, tok0, tok1, proto, 'test')
    pos = BotPos(desc, 0, chain)

    # =========================== ROUTINE ================================
    count = 0
    while True:
        # JOB PROCESSING OR JUST DATA COLLECTION
        if trade_on:
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
                if count >= 120:
                    pos.actuate_win_slow()
                    count = 0
                else:
                    pos.actuate_win_reg()
                if pos.P_act > pos.P_max:
                    if pos.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if pos.mode != 'T':
                        pos.prev_mode = pos.mode
                    pos.mode = 'U'
                    pos.params = pos.load_config(desc)
                    pos.params["prev_mode"] = pos.prev_mode
                    pos.params["mode"] = pos.mode
                    pos.save_config(pos.params, desc)
                    continue
                elif pos.P_act < pos.P_min:
                    if pos.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if pos.mode != 'T':
                        pos.prev_mode = pos.mode
                    pos.mode = 'D'
                    pos.params = pos.load_config(desc)
                    pos.params["prev_mode"] = pos.prev_mode
                    pos.params["mode"] = pos.mode
                    pos.save_config(pos.params, desc)
                    continue
                elif (
                    pos.pos_data.timestamp_IN                       # if opened 
                    and datetime.now() - pos.pos_data.timestamp_IN
                    > timedelta(hours=pos.dyn_period_scale())       # if time to reopen
                    and pos.test_range_mod()                        # if logic allows
                ):
                    if pos.proc_close() != 1:
                        print('\nSTATUS NOT 1...')
                        time.sleep(30)
                        continue
                    if pos.mode != 'T':
                        pos.prev_mode = pos.mode
                    pos.mode = 'T'
                    pos.params = pos.load_config(desc)
                    pos.params["prev_mode"] = pos.prev_mode
                    pos.params["mode"] = pos.mode
                    pos.save_config(pos.params, desc)
                    continue
                time.sleep(60)
            elif pos.step == 3 or pos.step == 4:
                if pos.proc_close() != 1:
                    print('\nSTATUS NOT 1...')
                    time.sleep(30)
                    continue
            elif pos.step == 5:
                pos.proc_modify()
                pos.params = pos.load_config(desc)
                pos.params["range_width"] = pos.range_width
                pos.params["L_fee"] = pos.L_fee
                pos.save_config(pos.params, desc)
                pos.chain.L_fee = pos.L_fee         # Put best pool of last hour to new position
                pos.step = 0
        else:
            if count >= 120:
                pos.actuate_win_slow()
                count = 0
            else:
                pos.actuate_win_reg()
            time.sleep(60)
        count += 1

if __name__ == "__main__":
    main()