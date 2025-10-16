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
    step = Column(Integer)

engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()

lasts = (
    session.query(Position)
    .filter(Position.descriptor == 1)
    .filter(Position.id >= 16)
    .order_by(Position.id.desc())
    .limit(20)
    .all()
)
print(lasts[0].timestamp_IN, '\n', lasts[0].position,'\n', -lasts[0].token0_swap, -lasts[0].token1_swap, '\n')
lasts = list(reversed(lasts))

sum_total_0 = 0
sum_total_1 = 0
for row in lasts[:-1]:
    avrg_p = (row.range_MIN + row.range_MAX) / 2
    print('|Pos:', row.position, row.range_MIN, row.range_MAX, row.descriptor, row.id)
    print('|IN:', -row.token0_IN, -row.token1_IN)
    print('|OUT:', row.token0_OUT, row.token1_OUT)
    if row.token0_OUT * avrg_p < row.token1_OUT:
        alt_out0 = clc_amm(row.range_MIN, row.range_MAX, row.token1_OUT, 0)
        alt_out1 = 0
    else:
        alt_out0 = 0
        alt_out1 = clc_amm(row.range_MIN, row.range_MAX, row.token0_OUT, 1)
    print('|ALT_OUT:', alt_out0, alt_out1)
    print('|Fee:', row.token0_fee, row.token1_fee)
    print('|Swap:', -row.token0_swap, -row.token1_swap)
    avrg_p = (row.range_MIN + row.range_MAX) / 2
    sum_0 = -row.token0_IN + row.token0_OUT + row.token0_fee + -row.token0_swap
    sum_1 = -row.token1_IN + row.token1_OUT + row.token1_fee + -row.token1_swap
    print('|Balance:', row.balance_0, row.balance_1, row.native * avrg_p)
    sum_total_0 += sum_0
    sum_total_1 += sum_1
    course = -sum_1/sum_0
    print('|Change:', sum_0, sum_1, course)
    if sum_0 < 0 and sum_1 > 0:
        print('sell')
        if course > row.range_MAX:
            print('good')
        elif course < row.range_MIN:
            print('bad')
        else:
            print('neutral')
    elif sum_0 > 0 and sum_1 < 0:
        print('buy')
        if course < row.range_MIN:
            print('good')
        elif course > row.range_MAX:
            print('bad')
        else:
            print('neutral')
    elif sum_0 < 0 and sum_1 < 0:
        print('loss')
    elif sum_0 > 0 and sum_1 > 0:
        print('profit')
    print('-'*40)

print('\nTotal:', sum_total_0, sum_total_1, -sum_total_1/sum_total_0)




timestamps = [pos.timestamp_IN for pos in lasts]
prices_min = [pos.range_MIN for pos in lasts]
prices_max = [pos.range_MAX for pos in lasts]
prices_emit = []
price_aux = None
for pos in lasts:
    if pos.range_MIN is None:
        avrg_p = -pos.token1_swap/pos.token0_swap
    else:
        avrg_p = (pos.range_MIN + pos.range_MAX) / 2
    if pos.timestamp_OUT is None:
        prices_emit.append(price_aux)
        continue
    if price_aux is None:
        prices_emit.append(avrg_p)
    else:
        prices_emit.append(price_aux)
    if pos.token0_OUT * avrg_p > pos.token1_OUT:
        price_aux = pos.range_MIN
    else:
        price_aux = pos.range_MAX


plt.figure(figsize=(18,12))
plt.scatter(timestamps, prices_min, marker="o", color="black", s=60)
plt.scatter(timestamps, prices_max, marker="o", color="black", s=60)
plt.plot(timestamps, prices_emit, linestyle="-", color="teal", linewidth=3)
plt.title("Ranges")
plt.grid(True)
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig('pictures/ranges_by_time.png')

price_dif = []
for pos in lasts:
    if pos.range_MIN is None:
        price_dif.append(0)
    else:
        price_dif.append(pos.range_MAX - pos.range_MIN)
native_bal = [pos.native for pos in lasts]
gas_costs = []
gas_aux = None
for pos in lasts:
    if gas_aux is None:
        gas_costs.append(0)
        gas_aux = pos.native
    elif pos.native is None:
        gas_costs.append(0)
    else:
        if gas_aux - pos.native < 0:
            gas_costs.append(0)
        else:
            gas_costs.append((gas_aux - pos.native) * avrg_p)
        gas_aux = pos.native
amm_proc = []
profit_var = []
pos_testpar = []
hidden_loss = []
for pos in lasts:
    if pos.range_MIN is None:
        avrg_p = -pos.token1_swap/pos.token0_swap
    else:
        avrg_p = (pos.range_MIN + pos.range_MAX) / 2
    if pos.timestamp_OUT is not None:
        sum_0 = -pos.token0_IN + pos.token0_OUT + pos.token0_fee + -pos.token0_swap
        sum_1 = -pos.token1_IN + pos.token1_OUT + pos.token1_fee + -pos.token1_swap
        if pos.token0_OUT * avrg_p > pos.token1_OUT:
            sum_total = sum_0 * pos.range_MIN + sum_1
            sum_amm = pos.balance_0 * pos.range_MIN + pos.balance_1
        else:
            sum_total = sum_0 * pos.range_MAX + sum_1   
            sum_amm = pos.balance_0 * pos.range_MAX + pos.balance_1 
        proc_calc = sum_total / sum_amm * 100
        if sum_total < 0:
            loss_aux = -sum_total
            sum_total_aux = 0
        else:
            loss_aux = 0
            sum_total_aux = sum_total
        dur_cur = (pos.timestamp_OUT - pos.timestamp_IN).total_seconds() / 3600 / 24
        if dur_cur < 1:
            dur_cur = 1
        apr = proc_calc/dur_cur*365
        testpar = apr/(avrg_p/(pos.range_MAX - pos.range_MIN))
        print(sum_total, sum_amm, proc_calc, apr, testpar, dur_cur)
    else:
        sum_total = 0
        sum_amm = 0
        proc_calc = 0
        testpar = 0
        apr = 0
        loss_aux = 0
        if pos.timestamp_IN is None:
            dur_cur = 0
        else:
            dur_cur = (datetime.now() - pos.timestamp_IN).total_seconds() / 3600 / 24
    profit_var.append(sum_total_aux)
    amm_proc.append(apr)
    pos_testpar.append(testpar)
    hidden_loss.append(loss_aux)



x = np.arange(len(lasts))
width = 0.3
fig, ax1 = plt.subplots(figsize=(18,12))
ax1.set_xlabel("Profits")
ax1.set_ylabel("Dollars", color="black")
ax1.bar(x - width, hidden_loss, width=width, alpha=0.6, edgecolor="black", color="gold")
ax1.bar(x - width/2, gas_costs, width=width, alpha=0.6, edgecolor="black", color="red")
ax1.bar(x + width/2, profit_var, width=width, alpha=0.6, edgecolor="black", color="green")
ax1.tick_params(axis="y", labelcolor="black")
ax2 = ax1.twinx()
ax2.set_ylabel("Precent", color="grey")
# ax2.bar(x, pos_testpar, width=width, alpha=0.6, edgecolor="black", color="olive")
# ax2.bar(x + width/2, amm_proc, width=width, alpha=0.6, edgecolor="black", color="black")
# ax2.bar(x + width/4, price_dif, width=width, alpha=0.6, edgecolor="black", color="grey")
ax2.tick_params(axis="y", labelcolor="grey")
plt.grid(True)
plt.xticks([])
plt.tight_layout()
plt.savefig('pictures/profit.png')








