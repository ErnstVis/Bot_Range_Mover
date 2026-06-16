from package import BotPos, ChainLink
import time
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


""" 
Main working version 1.1 
One pair, dynamic range moving bot with uniswap v3, fee level auto selection, operation and pool data logging.
In this file - argument parse, mode select, strategy sequencers, some manual actions.
"""


def status_ok(proc, sleep_sec=30):
    """Run a procedural action and retry on non-success status."""
    if proc() != 1:
        print('\nSTATUS NOT OK!')
        time.sleep(sleep_sec)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Example script with arguments.")
    parser.add_argument(
        "--inst",
        type=str,
        default='arb_uni3_eth',
        help="bot mode, chain, proto, etc",
    )    
    parser.add_argument(
        "--mode",
        type=str,
        default='on',
        help="bot mode, what need to do",
    )
    args = parser.parse_args()
    if args.inst == 'arb_uni3_eth':
        ch = 'arbitrum'
        tok0 = 'weth'
        tok1 = 'usdc'
        proto = 'uniswap'
        desc = 1
        print('Running in arbitrum chain, uni3 proto, eth usdc... Descriptor 1')
    elif args.inst == 'pol_uni3_eth':
        ch = 'polygon'
        tok0 = 'weth'
        tok1 = 'usdt'
        proto = 'uniswap'
        desc = 2
        print('Running in polygon chain, uni3 proto, weth usdt... Descriptor 2')
    elif args.inst == 'pol_uni3_mai':
        ch = 'polygon'
        tok0 = 'frax'
        tok1 = 'mai'
        proto = 'uniswap'
        desc = 3
        print('Running in polygon chain, uni3 proto, eth sol... Descriptor 3')
    else:
        print('Unknown chain arg...')
        return
    
    chain = ChainLink(ch, tok0, tok1, proto)
    inst = BotPos(desc, chain)



    # =========================== ROUTINES ================================
    short_cycle = 120
    long_cycle = 120


    # Test one side drifting mode, trade_drift_up/down, IL free trand strategies
    # Test one side exit other side crawl closer, trade_find_up/down, IL free strategies

    def trade_on():                     # Warning... IL possible strategy
        count = 0
        inst.P_min = inst.range_min
        inst.P_max = inst.range_max
        inst.range_width = inst.P_max - inst.P_min
        inst.chain.L_fee = inst.L_fee
        while True:                             # MAIN TRADE LOOP
            if inst.step == "wait_open" or inst.step == "closed":
                inst.step = 'swap'
            if inst.step == 'swap':               # DO SWAP, prepare balances for create position
                if not status_ok(inst.proc_swap):
                    continue
                inst.step = 'open'                      # next step
            elif inst.step == 'open':               # OPEN POSITION
                if not status_ok(inst.proc_open):
                    continue
                inst.step = 'wait_close'
                config = inst.load_config(desc)
                config["range_width"] = inst.P_max - inst.P_min
                config["L_fee"] = inst.L_fee
                config["mint_time"] = inst.mint_time
                config["step"] = inst.step
                inst.save_config(config, desc)                  # update config
            elif inst.step == 'wait_close':                 # WAITING for rebalance needed
                if count >= long_cycle:                                # static collect if needed
                    inst.actuate_win_reg()
                    inst.collect_pool_state()
                    count = 0
                else:
                    inst.actuate_win_reg()                      # next step
                if inst.P_act > inst.P_max:
                    if inst.trade_dir != 'T':
                        inst.prev_trade_dir = inst.trade_dir
                    inst.trade_dir = 'U'
                    inst.step = 'close'
                    continue
                elif inst.P_act < inst.P_min:
                    if inst.trade_dir != 'T':
                        inst.prev_trade_dir = inst.trade_dir
                    inst.trade_dir = 'D'
                    inst.step = 'close'
                    continue
                elif (
                    inst.mint_time                                      # if opened 
                    and datetime.now() - inst.mint_time
                    > timedelta(hours=inst.dyn_period_scale())          # if time to reopen
                    and inst.test_range_mod()                           # if logic allows
                ):
                    if inst.trade_dir != 'T':
                        inst.prev_trade_dir = inst.trade_dir
                    inst.trade_dir = 'T'
                    inst.step = 'close'
                    continue
                time.sleep(short_cycle)
                count += 1
                
            elif inst.step == 'close':
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["prev_trade_dir"] = inst.prev_trade_dir
                config["trade_dir"] = inst.trade_dir
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.proc_modify()
                inst.chain.L_fee = inst.L_fee
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)


    def trade_close():                   # Just close position manually
        while True:
            if inst.step == 'opened' or inst.step == 'wait_close':
                inst.step = 'close'
            elif inst.step == 'close':
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
                break

    def trade_open():                   # Just prepare ammounts and open position manually
        inst.P_min = inst.range_min
        inst.P_max = inst.range_max
        inst.range_width = inst.P_max - inst.P_min
        inst.chain.L_fee = inst.L_fee
        while True:
            if inst.step == "wait_open" or inst.step == "closed":
                inst.step = 'swap'
            elif inst.step == 'swap':
                if not status_ok(inst.proc_swap):
                    continue
                inst.step = "open"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "open":
                if not status_ok(inst.proc_open):
                    continue
                inst.step = "opened"
                config = inst.load_config(desc)
                config["range_width"] = inst.P_max - inst.P_min
                config["L_fee"] = inst.L_fee
                config["mint_time"] = inst.mint_time
                config["step"] = inst.step
                inst.save_config(config, desc)
                break

    def trade_upper():                  # Just once exit, can be as pending order
        count = 0
        while True:
            if inst.step == 'opened':
                inst.step = 'wait_close'
            elif inst.step == 'wait_close':
                if count >= long_cycle:
                    inst.collect_pool_state()
                    count = 0
                inst.actuate_win_reg()
                if inst.P_act > inst.P_max:
                    inst.step = 'close'
                else:
                    time.sleep(short_cycle)
                    count += 1
            elif inst.step == "close":
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
                break


    def trade_lower():                  # Just once exit, can be as pending order
        count = 0
        while True:
            if inst.step == 'opened':
                inst.step = 'wait_close'
            elif inst.step == 'wait_close':
                if count >= long_cycle:
                    inst.collect_pool_state()
                    count = 0
                inst.actuate_win_reg()
                if inst.P_act < inst.P_min:
                    inst.step = 'close'
                else:
                    time.sleep(short_cycle)
                    count += 1
            elif inst.step == "close":
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
                break

    def trade_channel():                # IL free strategy by channel
        inst.P_min = inst.range_min
        inst.P_max = inst.range_max
        inst.range_width = inst.P_max - inst.P_min
        inst.chain.L_fee = inst.L_fee
        P_mn_mx = (inst.P_min + inst.P_max) / 2
        count = 0
        while True:
            if inst.step == "opened":
                inst.step = 'wait_close'
                print('Waiting for any breach and exit...', end='')
            elif inst.step == 'wait_close':
                if count >= long_cycle:
                    inst.collect_pool_state()
                    count = 0
                inst.actuate_win_reg()
                if inst.P_act < inst.P_min:
                    inst.prev_close = 'lo'
                elif inst.P_act > inst.P_max:
                    inst.prev_close = 'hi'
                else:
                    time.sleep(short_cycle)
                    count += 1
                    continue
                inst.step = 'close'
            elif inst.step == "close":
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                config["prev_close"] = inst.prev_close
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "closed":
                inst.step = 'wait_open'
                print('Waiting for price back and entry...', end='')
            elif inst.step == "wait_open":
                if count >= long_cycle:
                    inst.actuate_win_reg()
                    inst.collect_pool_state()
                    count = 0
                else:
                    inst.actuate_win_reg()
                if (inst.P_act > P_mn_mx and inst.prev_close == 'lo') or (inst.P_act < P_mn_mx and inst.prev_close == 'hi'):
                    inst.step = 'swap'
                else:
                    time.sleep(short_cycle)
                    count += 1
                    continue
            elif inst.step == 'swap':
                if not status_ok(inst.proc_swap):
                    continue
                inst.step = "open"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "open":
                if not status_ok(inst.proc_open):
                    continue
                inst.step = "opened"
                config = inst.load_config(desc)
                config["range_width"] = inst.P_max - inst.P_min
                config["L_fee"] = inst.L_fee
                config["mint_time"] = inst.mint_time
                config["step"] = inst.step
                inst.save_config(config, desc)                

    def trade_jumper():                 # IL free strategy by channel
        inst.P_min = inst.range_min
        inst.P_max = inst.range_max
        inst.range_width = inst.P_max - inst.P_min
        inst.chain.L_fee = inst.L_fee
        price_offset = 100
        count = 0
        while True:
            if inst.step == "opened":
                inst.step = 'wait_close'
                print('Waiting for breach and exit... Last entry:', inst.prev_close, end='')
            elif inst.step == 'wait_close':
                if count >= long_cycle:
                    inst.collect_pool_state()
                    count = 0
                inst.actuate_win_reg()
                if inst.P_act > inst.P_max and inst.prev_close == 'lo':
                    inst.P_min = inst.P_min - price_offset
                    inst.P_max = inst.P_max - price_offset
                    inst.prev_close = 'hi'
                elif inst.P_act < inst.P_min and inst.prev_close == 'hi':
                    inst.P_min = inst.P_min + price_offset
                    inst.P_max = inst.P_max + price_offset
                    inst.prev_close = 'lo'
                else:
                    time.sleep(short_cycle)
                    count += 1
                    continue
                inst.step = 'close'
            elif inst.step == "close":
                if not status_ok(inst.proc_remove):
                    continue
                inst.step = "liq_removed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                config["prev_close"] = inst.prev_close
                config["range_min"] = inst.P_min
                config["range_max"] = inst.P_max
                inst.save_config(config, desc)
            elif inst.step == "liq_removed":
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "closed"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "closed" or inst.step == 'wait_open':
                inst.step = 'open'
                print('Entry without swap...', end='')
            elif inst.step == "open":
                if not status_ok(inst.proc_open):
                    continue
                inst.step = "opened"
                config = inst.load_config(desc)
                config["range_width"] = inst.P_max - inst.P_min
                config["L_fee"] = inst.L_fee
                config["mint_time"] = inst.mint_time
                config["step"] = inst.step
                inst.save_config(config, desc)             


    def trade_collect():                # Collect fees, watch balances, increase working position ammounts
        while True:
            if inst.step == 'wait_close' or inst.step == 'opened':
                inst.step = 'collect'
            elif inst.step == 'collect':
                if not status_ok(inst.proc_collect):
                    continue
                inst.step = "swap"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == 'swap':
                if not status_ok(inst.proc_swap):
                    continue
                inst.step = "increase"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
            elif inst.step == "increase":
                if not status_ok(inst.proc_increase):
                    continue
                inst.step = "opened"
                config = inst.load_config(desc)
                config["step"] = inst.step
                inst.save_config(config, desc)
                break


    def trade_stat():                   # Collect stats only, no trading
        count = 0
        while True:
            if count >= 120:
                inst.collect_pool_state()
                count = 0
            else:
                inst.actuate_win_reg()
            time.sleep(short_cycle)
            count += 1


    # Chain level manual operations
    def approve():                      # Approve all for router and for manager
        inst.chain.approve_token(0, 0, 'r', wait=1)
        inst.chain.approve_token(0, 1, 'r', wait=1)
        inst.chain.approve_token(0, 0, 'm', wait=1)
        inst.chain.approve_token(0, 1, 'm', wait=1)

    def send_out():                      # Send tokens to other wallet
        inst.chain.send_token(inst.chain.get_balance_token(0) * 0.999999, 0)
        inst.chain.send_token(inst.chain.get_balance_token(1) * 0.999999, 1)

    def manual_swap_1to0():
        bal1 = inst.chain.get_balance_token(1)
        _, price = inst.chain.get_current_tick()
        lim0 = (bal1 / price) * (1 - inst.slippage)
        inst.chain.get_swap_ammount_router(bal1 * 0.999999, lim0, 0, 'I')        # Get token0 by Input value

    def manual_swap_0to1():
        bal0 = inst.chain.get_balance_token(0)
        _, price = inst.chain.get_current_tick()
        lim1 = (bal0 * price) * (1 - inst.slippage)
        inst.chain.get_swap_ammount_router(bal0 * 0.999999, lim1, 1, 'I')        # Get token1 by Input value
    


    if args.mode == 'on':
        print('Trading is in main mode')
        trade_on()
    elif args.mode == 'close':
        print('Closing positions manually')
        trade_close()
    elif args.mode == 'open':
        print('Opening positions manually')
        trade_open()
    elif args.mode == 'upper':
        print('Waiting for upper breach and exit')
        trade_upper()
    elif args.mode == 'lower':
        print('Waiting for lower breach and exit')
        trade_lower()
    elif args.mode == 'channel':
        print('Waiting for any breach and wait for reentry again')
        trade_channel()
    elif args.mode == 'jumper':
        print('Waiting for any breach and reopen with spread')
        trade_jumper()
    elif args.mode == 'collect':
        print('Collecting fees and opening with same range')
        trade_collect()
    elif args.mode == 'stat':
        print('Statistic collection only')
        trade_stat()
    elif args.mode == 'approve':
        print('Approve tokens for manager and for router')
        approve()
    elif args.mode == 'send':
        print('Send tokens to other wallet')
        send_out()
    elif args.mode == 'swap0to1':
        print('Manual swap token0 to token1')
        manual_swap_0to1()
    elif args.mode == 'swap1to0':
        print('Manual swap token1 to token0')
        manual_swap_1to0()
    else:
        print('Unknown mode arg...')
        return
    



if __name__ == "__main__":
    main()