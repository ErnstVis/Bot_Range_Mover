from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import math

def dyn_period_scale(min, max):
    var_times = 24 - 6
    var_width = 1397 - 96
    var_ratio = var_width / var_times
    var_aux = ((max - min) - 96) / var_ratio
    return 24 - var_aux

def moving_average_same(x, window):
    x = np.asarray(x, dtype=float)
    return np.convolve(x, np.ones(window)/window, mode='same')


Base = declarative_base()
class Scan_window(Base):
    __tablename__ = "scan_window"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    price = Column(Float)
    search_max = Column(Float)
    search_min = Column(Float)
    actual_max = Column(Float)
    actual_min = Column(Float)


engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()



# Research liquidity changes after a specific time
target_time = datetime.strptime("2025-10-30 15:02:56.409922", "%Y-%m-%d %H:%M:%S.%f")




stmt = (
    session.query(Scan_window)
    .where(Scan_window.timestamp > target_time)
    .order_by(Scan_window.timestamp.asc())
    .first()
)
if stmt:
    print("Timestamp:", stmt.timestamp)
    print("Price:", stmt.price)
    print("Min:", stmt.actual_min)
    print("Max:", stmt.actual_max)
    print("Tok0 Gross start:", stmt.search_max)
    print("Tok1 Gross start:", stmt.search_min)
    start_tok0 = stmt.search_max
    start_tok1 = stmt.search_min

lasts = (
    session.query(Scan_window)
    .order_by(Scan_window.id.asc())
    .all()
)

print()
print(lasts[-1].actual_min)
print(lasts[-1].actual_max)
print(dyn_period_scale(lasts[-1].actual_min, lasts[-1].actual_max))
print(timedelta(hours=dyn_period_scale(lasts[-1].actual_min, lasts[-1].actual_max)))
print(target_time)
print(target_time + timedelta(hours=dyn_period_scale(lasts[-1].actual_min, lasts[-1].actual_max)))
print()

price_ref = lasts[-1].price
liq = 53394952765201.0

print("Tok0 Gross finish:", lasts[-1].search_max)
print("Tok0 Gross finish:", lasts[-1].search_min)
finish_tok0 = lasts[-1].search_max
finish_tok1 = lasts[-1].search_min
print('\nTotal Tok0 Gross:', finish_tok0 - start_tok0)
print('Total Tok1 Gross:', finish_tok1 - start_tok1, '\n')
print('Abs Tok0 gross $:', (finish_tok0 - start_tok0) * liq * price_ref)
print('Abs Tok1 gross:', (finish_tok1 - start_tok1) * liq)


prices = []
prices_act_min = []
prices_act_max = []

aux_price = lasts[0].price
aux_gross_0 = lasts[0].search_max * price_ref
aux_gross_1 = lasts[0].search_min
aux_time = lasts[0].timestamp


alpha = 0.01
ema_price_change = 0.1

d_gross_indicate = []
ema_price_changes = []

for pos in lasts:
    prices.append(pos.price)
    prices_act_min.append(pos.actual_min)
    prices_act_max.append(pos.actual_max)

    d_gross_0 = pos.search_max * price_ref - aux_gross_0
    d_gross_1 = pos.search_min - aux_gross_1
    d_gross = d_gross_0 + d_gross_1

    if aux_time is None or aux_time == 0 or aux_time == pos.timestamp:
        d_time = 60
    else:
        d_time = (pos.timestamp - aux_time).total_seconds()

    d_gross_corrected = d_gross / d_time * 60
    d_gross_indicate.append(d_gross_corrected)


    # change = (pos.price - aux_price) / aux_price
    # ema_price_change = (1 - alpha) * ema_price_change + alpha * (change ** 2)
    # volatility = math.sqrt(ema_sq)

    change = abs(pos.price - aux_price)
    change_c = change / d_time * 60
    change_p = change_c / aux_price
    # ema_price_change = (1 - alpha) * ema_price_change + alpha * change_p
    ema_price_changes.append(change_p)

    aux_gross_0 = pos.search_max * price_ref
    aux_gross_1 = pos.search_min
    aux_time = pos.timestamp
    aux_price = pos.price

d_gross_sma = moving_average_same(d_gross_indicate, window=150)
ema_price_changes_sma = moving_average_same(ema_price_changes, window=15)
helper = np.array(d_gross_sma) / np.array(ema_price_changes_sma)

# d_gross_sma_n = np.array(d_gross_sma) / 0.0005
# ema_price_changes_n = np.array(d_gross_sma) / np.array(ema_price_changes)

# ema_price_changes_n = np.array(ema_price_changes) / 0.0005
# print(np.max(d_gross_sma))
# print(np.max(ema_price_changes))



ema_price_changes_n = ema_price_changes_sma
# d_gross_sma_n = d_gross_sma / np.max(d_gross_sma)
# ema_price_changes_n = ema_price_changes_sma / np.max(ema_price_changes_sma)
# helper_n = helper / np.max(helper)

x = np.arange(len(lasts))
fig, ax1 = plt.subplots(figsize=(18, 12))
# --- Левая ось (доллары) ---
ax1.set_xlabel("Profits")
ax1.set_ylabel("Dollars", color="black")
ax1.plot(x, prices, color="red", linewidth=2)
ax1.plot(x, prices_act_min, color="magenta", linewidth=2)
ax1.plot(x, prices_act_max, color="magenta", linewidth=2)
ax1.tick_params(axis="y", labelcolor="black")
# --- Правая ось (проценты) ---
ax2 = ax1.twinx()
ax2.set_ylabel("Percent", color="grey")
# ax2.plot(x, d_gross_sma_n, color="green", linewidth=1, alpha=0.5)
ax2.plot(x, ema_price_changes_n, color="blue", linewidth=1, alpha=0.5)
# ax2.plot(x, helper_n, color="orange", linewidth=1, alpha=0.5)
ax2.tick_params(axis="y", labelcolor="grey")
# --- Общие настройки ---
plt.grid(True, linestyle="--", alpha=0.5)
plt.xticks(x, [])  # скрыть метки по оси X
fig.tight_layout()
# Легенду можно объединить (чтобы обе оси показывались в одном месте)
lines_1, labels_1 = ax1.get_legend_handles_labels()
# lines_2, labels_2 = ax2.get_legend_handles_labels()
# ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", ncol=2)
plt.savefig('pictures/window_lines.png', dpi=200)
plt.close()





