# version 0.0.1
from botcore import BotPos, ChainLink
import matplotlib.pyplot as plt
from datetime import datetime
import time

manual_prices = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]


test_option = 1


# cycle params
avrg_time = 0
avrg_bal_change0 = 0
avrg_bal_change1 = 0
avrg_i = 30
ii = 50

if test_option == 2:
    avrg_i = 1
for i in range(avrg_i):                                     # Repeat for collect average loss
    count_deals = 0
    count_time = 0
    last_dir = 1
    pos1 = BotPos(0, 2500, test_option)                     # reinit
    start_bal_tok0 = pos1.amm0 + pos1.amm1 / pos1.P_act_normal
    start_bal_tok1 = pos1.amm1 + pos1.amm0 * pos1.P_act_normal
    pos1.proc_shift("UT")
    pos1.proc_swap("UT")
    pos1.proc_open("UT")
    pos1.stat_put(count_time)
    while (count_deals < ii and test_option == 1) or (test_option == 2 and count_time < len(manual_prices)):
        if test_option == 1:
            pos1.p_actuate('rnd')
        else:
            pos1.p_actuate('man', manual_prices[count_time])
        count_time += 1
        if pos1.P_act >= pos1.P_max_tick:                           # Control price to upper limit
            if last_dir: 
                pos1.proc_cycle("UT")
            else:
                pos1.proc_cycle("UF")
            last_dir = 1
        elif pos1.P_act <= pos1.P_min_tick:                         # Control price to lower limit
            if last_dir:
                pos1.proc_cycle("DF")
            else:
                pos1.proc_cycle("DT")
            last_dir = 0
        else:
            continue                                                # Repeat if price in range
        if avrg_i == i + 1:
            pos1.stat_put(count_time)    
        count_deals += 1 
        print('Interation:', count_deals, 'Epoch:', i + 1, 'Time:', count_time)
    total_bal_tok0 = (pos1.amm0 + pos1.amm1 / pos1.P_act_normal) + (pos1.amm0_lock + pos1.amm1_lock / pos1.P_act_normal)
    total_bal_tok1 = (pos1.amm1 + pos1.amm0 * pos1.P_act_normal) + (pos1.amm1_lock + pos1.amm0_lock * pos1.P_act_normal)
    bal_change0 = (total_bal_tok0 - start_bal_tok0) / start_bal_tok0 * 100
    bal_change1 = (total_bal_tok1 - start_bal_tok1) / start_bal_tok1 * 100
    P_change = (pos1.P_act_normal - pos1.reference_price) / pos1.reference_price * 100
    avrg_bal_change0 += bal_change0
    avrg_bal_change1 += bal_change1
    avrg_time += count_time
    print('Balance change %:', bal_change1, '| P change %:', P_change)



# Printing curves

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(pos1.prices_max, 'o', label="Max", color='blue')
ax1.plot(pos1.prices_min, 'o', label="Min", color='orange')
ax1.plot(pos1.prices, label="P", color='green')
ax1.set_xlabel("Iterations")
ax1.set_ylabel("Price", color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True)
ax1.legend(loc="upper left")

ax2 = ax1.twinx()
ax2.plot(pos1.balances, label="Balance", color='red', linestyle='--')
ax2.plot([t * (max(pos1.balances) / max(pos1.balances_alt)) for t in pos1.balances_alt], label="Balance alt", color='red', linestyle=':')
ax2.plot([t * (max(pos1.balances) / max(pos1.times)) for t in pos1.times], label="Time", color='black', linestyle='--')
ax2.set_ylabel("Balance", color='red')
ax2.tick_params(axis='y', labelcolor='red')
ax2.legend(loc="upper right")

plt.title('Simulation. Avrgs. Loss: ' + str(round(avrg_bal_change1 / avrg_i)) + '% Time: ' + str(round(avrg_time / avrg_i / 24)) + 'days. Change per day: ' + str(round(((avrg_bal_change0 / avrg_i) / (avrg_time / avrg_i / 24)) * 100) / 100) + '%. Pars. RngScTr: ' + str(pos1.range_scale_trend) + ' RngMvTr: ' + str(pos1.range_move_trend) + ' RngScFl: ' + str(pos1.range_scale_float) + ' RngMvFl: ' + str(pos1.range_move_float))
plt.savefig('pictures/pool_sim_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.png')


