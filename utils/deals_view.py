from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math


def clc_amm(P_min, P_max, ammount_in, target):
    if target:
        L = ammount_in / ((math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min)))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min))
    else:
        L = ammount_in / (math.sqrt(P_max) - math.sqrt(P_min))
        ammount_out = L * (math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min))
    return ammount_out


Base = declarative_base()
class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    descriptor = Column(Integer)
    position = Column(Integer)
    range_MIN = Column(Float)
    range_MAX = Column(Float)
    timestamp_IN = Column(DateTime)
    timestamp_OUT = Column(DateTime)
    token0_IN = Column(Float)
    token1_IN = Column(Float)
    token0_OUT = Column(Float)
    token1_OUT = Column(Float)
    token0_fee = Column(Float)
    token1_fee = Column(Float)
    token0_swap = Column(Float)
    token1_swap = Column(Float)
    balance_0 = Column(Float)
    balance_1 = Column(Float)
    native = Column(Float)
    price = Column(Float)
    liq = Column(Float)
    step = Column(Integer)

engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()

lasts = (
    session.query(Position)
    .filter(Position.descriptor == 1)
    .filter(Position.id >= 17)
    .order_by(Position.id.desc())
    .limit(20)
    .all()
)
print(lasts[0].timestamp_IN)
print('Position:', lasts[0].position)
print('Swaped:', -lasts[0].token1_swap, -lasts[0].token0_swap)
print('Tab id:', lasts[0].id)
print('Liq:', lasts[0].liq, '\n')
lasts = list(reversed(lasts))

dur_tot = (lasts[-2].timestamp_OUT - lasts[0].timestamp_IN).total_seconds() / 3600


sum_total_0 = 0
sum_total_1 = 0
for row in lasts[:-1]:                                                                                  # Part with positions text description
    print('|', row.id, ':\t', round(row.range_MIN, 2), '\r\t\t\t', round(row.range_MAX, 2), end='\r\t\t\t\t\t\t')
    print(round(row.price, 2))
    print('|Swap:\t', round(-row.token1_swap, 2), '\r\t\t\t', round(-row.token0_swap, 6))
    print('|IN:\t', round(-row.token1_IN, 2), '\r\t\t\t', round(-row.token0_IN, 6))
    print('|OUT:\t', round(row.token1_OUT, 2), '\r\t\t\t', round(row.token0_OUT, 6))
    print('|Fee:\t', round(row.token1_fee, 2), '\r\t\t\t', round(row.token0_fee, 6))
    sum_0 = -row.token0_IN + row.token0_OUT + row.token0_fee + -row.token0_swap
    sum_1 = -row.token1_IN + row.token1_OUT + row.token1_fee + -row.token1_swap
    print('|Balns:\t', round(row.balance_1, 2), '\r\t\t\t', round(row.balance_0, 6), end='\r\t\t\t\t\t\t')
    print(round(row.balance_0 * row.price + row.balance_1, 2))
    sum_total_0 += sum_0
    sum_total_1 += sum_1
    course = -sum_1/sum_0
    print('|Chng:\t', round(sum_1, 2), '\r\t\t\t', round(sum_0, 6), end='\r'+'\t'*6)
    print(round(sum_0 * row.price + sum_1, 2))
    print('|Koef:\t', round(course, 2), end='\r\t\t\t')
    if sum_0 < 0 and sum_1 > 0:
        print('sell', end=' ')
        if course > row.range_MAX:
            print('good')
        elif course < row.range_MIN:
            print('bad')
        else:
            print('neutral')
    elif sum_0 >= 0 and sum_1 <= 0:
        print('buy', end=' ')
        if course < row.range_MIN:
            print('good')
        elif course > row.range_MAX:
            print('bad')
        else:
            print('neutral')
    elif sum_0 <= 0 and sum_1 <= 0:
        print('loss')
    elif sum_0 > 0 and sum_1 > 0:
        print('profit')
    print('|Gas:\t', round(row.native * row.price, 2))
    print('-'*60)


sum_0_1_tot = sum_total_1 + sum_total_0 * lasts[-2].price
bal_0_1_tot = lasts[-2].balance_0 * lasts[-2].price + lasts[-2].balance_1
proc_tot_calc = sum_0_1_tot / (bal_0_1_tot - sum_0_1_tot) * 100
apr_tot_usd = proc_tot_calc/dur_tot * 365 * 24
print('\nTotal Chngs:\t', round(sum_total_1, 2), '\tusd\t', round(sum_total_0, 6), '\teth', end='\t')
print('\tK:', round(-sum_total_1/sum_total_0, 2), '\t\t\tSum:', round(sum_0_1_tot, 2), '\tusd', end='\t')
print('\tSum:', round(sum_total_1 / lasts[-2].price + sum_total_0, 6), '\teth', end='\t')
print('\tChng:', round(proc_tot_calc, 2), '\t%', end='\t')
print('\tAPR:', round(apr_tot_usd, 2), '\t%')
print('='*220+'\n')


# ================================================================================================================


timestamps = [pos.timestamp_IN for pos in lasts]
prices_min = [pos.range_MIN for pos in lasts]
prices_max = [pos.range_MAX for pos in lasts]
prices_emit = []
price_aux = None
for pos in lasts:                                       # Range collection with times
    if price_aux is None:
        prices_emit.append((pos.range_MIN + pos.range_MAX) / 2)    
    else:
        prices_emit.append(price_aux)
    if pos.price is not None:
        price_aux = pos.price

plt.figure(figsize=(18,12))
plt.scatter(timestamps, prices_min, marker="o", color="black", s=60)
plt.scatter(timestamps, prices_max, marker="o", color="black", s=60)
plt.plot(timestamps, prices_emit, linestyle="-", color="teal", linewidth=3)
plt.title("Ranges")
plt.grid(True)
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig('pictures/ranges.png')
plt.close()

# ================================================================================================================


# Parameters for universal calculations
tok0_k = 1
tok1_k = 1
nat_vs_0 = 1
nat_vs_1 = 3800


gas_aux = None
gas_costs_m = []
gas_costs_alt_m = []

sum_fee_m = []
sum_fee_alt_m = []

profit_var_m = []
loss_var_m = []
profit_var_alt_m = []
loss_var_alt_m = []

# amm_proc = []
# amm_proc_alt = []
# pos_testpar = []


# ================================================================================================

for pos in lasts:                               # Collect native balance losses for fee
    if gas_aux is None:
        gas_costs = 0
        gas_costs_alt = 0
        gas_aux = pos.native
    elif pos.native is None:
        gas_costs = 0
        gas_costs_alt = 0
    else:
        if gas_aux - pos.native < 0:
            gas_costs = 0
            gas_costs_alt = 0
        else:
            gas_costs = (gas_aux - pos.native) * nat_vs_1
            gas_costs_alt = (gas_aux - pos.native) * nat_vs_0
        gas_aux = pos.native

    if pos.range_MIN is None:
        avrg_p = -pos.token1_swap/pos.token0_swap
    else:
        avrg_p = (pos.range_MIN + pos.range_MAX) / 2
    if pos.timestamp_OUT is not None:                   # Tokens dif after cycle
        sum_0 = -pos.token0_IN + pos.token0_OUT + pos.token0_fee + -pos.token0_swap
        sum_1 = -pos.token1_IN + pos.token1_OUT + pos.token1_fee + -pos.token1_swap

        sum_total = sum_0 * pos.price + sum_1                           # Sum dif after cycle
        sum_total_alt = sum_0 + sum_1 / pos.price
        sum_fee = pos.token0_fee * pos.price + pos.token1_fee
        sum_fee_alt = pos.token0_fee + pos.token1_fee / pos.price
        sum_amm = pos.balance_0 * pos.price + pos.balance_1             # Sum ammounts in work
        sum_amm_alt = pos.balance_0 + pos.balance_1 / pos.price

        proc_calc = sum_total / (sum_amm - sum_total) * 100                                   # Percent calculation for cycle
        proc_calc_alt = sum_total_alt / (sum_amm_alt - sum_total_alt) * 100

        if sum_total - sum_fee < 0:
            loss_var = - sum_total + gas_costs + sum_fee
            profit_var = 0
        else:
            loss_var = 0
            profit_var = sum_total

        if sum_total_alt - sum_fee_alt < 0:
            loss_var_alt = - sum_total_alt + gas_costs_alt + sum_fee_alt
            profit_var_alt = 0
        else:
            loss_var_alt = 0
            profit_var_alt = sum_total_alt

        dur_cur = (pos.timestamp_OUT - pos.timestamp_IN).total_seconds() / 3600 / 24        # Duration calc
        if dur_cur < 1:
            dur_cur = 1
        apr = proc_calc/dur_cur * 365                                                 # Annual percent rate
        # testpar = apr/(avrg_p/(pos.range_MAX - pos.range_MIN))                      # Test metric  
        print('Chng:', round(sum_total, 2), end=' ')
        print('\tusd\t\tChng:', round(sum_total_alt, 6), end=' ')
        print('\teth\t\tBal:', round(sum_amm, 2), end=' ')
        print('\tusd\t\tBal:', round(sum_amm_alt, 6), end=' ')
        print('\teth\t\tPrice:', round(pos.price, 2), end=' ')
        print('\t\t\tChng:', round(proc_calc, 2), end=' ')
        print('\t%\t\tAPR:', round(apr, 2), '\t%')
    else:
        sum_total = 0
        sum_total_alt = 0
        sum_fee = 0
        sum_fee_alt = 0
        sum_amm = 0
        sum_amm_alt = 0
        proc_calc = 0
        # testpar = 0
        apr = 0
        profit_var = 0
        loss_var = 0
        profit_var_alt = 0
        loss_var_alt = 0
        if pos.timestamp_IN is None:
            dur_cur = 0
        else:
            dur_cur = (datetime.now() - pos.timestamp_IN).total_seconds() / 3600 / 24
    

    gas_costs_m.append(gas_costs)
    gas_costs_alt_m.append(gas_costs_alt)

    sum_fee_m.append(sum_fee)
    sum_fee_alt_m.append(sum_fee_alt)

    profit_var_m.append(profit_var)
    loss_var_m.append(loss_var)
    profit_var_alt_m.append(profit_var_alt)
    loss_var_alt_m.append(loss_var_alt)

    # amm_proc.append(apr)
    # pos_testpar.append(testpar)



x = np.arange(len(lasts))
width = 0.3
fig, ax1 = plt.subplots(figsize=(18,12))
ax1.set_xlabel("Profits")
ax1.set_ylabel("Dollars", color="black")
ax1.bar(x - width/2, loss_var_m, width=width/2, edgecolor="black", color="orange")
ax1.bar(x - width/2, gas_costs_m, width=width/2, edgecolor="black", color="red")
ax1.bar(x + width/2, profit_var_m, width=width/2, edgecolor="black", color="cyan")
ax1.bar(x + width/2, sum_fee_m, width=width/2, edgecolor="black", color="green")
ax1.tick_params(axis="y", labelcolor="black")
ax2 = ax1.twinx()
ax2.set_ylabel("Precent", color="grey")
ax2.bar(x, loss_var_alt_m, width=width/2, edgecolor="black", color="orange")
ax2.bar(x, gas_costs_alt_m, width=width/2, edgecolor="black", color="red")
ax2.bar(x + width, profit_var_alt_m, width=width/2, edgecolor="black", color="cyan")
ax2.bar(x + width, sum_fee_alt_m, width=width/2, edgecolor="black", color="green")
ax2.tick_params(axis="y", labelcolor="grey")
plt.grid(True)
plt.xticks([])
plt.tight_layout()
plt.savefig('pictures/profit.png')
plt.close()







