from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import math

discr = 2

def sma_calc(prev_sma, new_value, period):
    if prev_sma is None:
        return new_value
    if period <= 1:
        period = 1
    alpha = 1 / period
    new_sma = (1 - alpha) * prev_sma + alpha * new_value
    return new_sma

def price_from_tick(tick, reversed, decimals0, decimals1):
    if reversed:
        P = (1 / (1.0001**tick)) * 10**(decimals0 - decimals1)
    else:
        P = (1.0001**tick) * 10**(decimals0 - decimals1)
    return(P)

def dyn_period_scale(min, max):
    var_times = 24 - 6
    var_width = 1397 - 96
    var_ratio = var_width / var_times
    var_aux = ((max - min) - 96) / var_ratio
    return 24 - var_aux

Base = declarative_base()
class Scan_window(Base):
    __tablename__ = "scan_window_" + str(discr)
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    price1 = Column(Float)
    price2 = Column(Float)
    price3 = Column(Float)
    liq1 = Column(Float)
    liq2 = Column(Float)
    liq3 = Column(Float)
    gross1 = Column(Float)
    gross2 = Column(Float)
    gross3 = Column(Float)
    actual_max = Column(Float)
    actual_min = Column(Float)
    search_max = Column(Float)
    search_min = Column(Float)


engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()


# Research liquidity changes after a specific time
target_time = datetime.strptime("2025-10-30 21:41:27.129074", "%Y-%m-%d %H:%M:%S.%f")



stmt = (
    session.query(Scan_window)
    .where(Scan_window.timestamp > target_time)
    .order_by(Scan_window.timestamp.asc())
    .first()
)
if stmt:
    print("Timestamp:", stmt.timestamp)
    print("Price:", stmt.price1)
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

price_ref = lasts[-1].price2
liq = 53394952765201.0

print("Tok0 Gross finish:", lasts[-1].search_max)
print("Tok0 Gross finish:", lasts[-1].search_min)
finish_tok0 = lasts[-1].search_max
finish_tok1 = lasts[-1].search_min
print('\nTotal Tok0 Gross:', finish_tok0 - start_tok0)
print('Total Tok1 Gross:', finish_tok1 - start_tok1, '\n')
print('Abs Tok0 gross $:', (finish_tok0 - start_tok0) * liq * price_ref)
print('Abs Tok1 gross:', (finish_tok1 - start_tok1) * liq)



# =================================================================================== INDICATORS CALCULATION AREA
price_1_list = []
price_2_list = []
price_3_list = []
liq_1_list = []
liq_2_list = []
liq_3_list = []
gross_1_list = []
gross_2_list = []
gross_3_list = []

prev_price = lasts[0].price3
gross_0_prev = lasts[0].search_max * price_ref
gross_1_prev = lasts[0].search_min
aux_time = lasts[0].timestamp



# SMA1 area                 Short term sma, volatily indicator
IND_sma1 = prev_price
IND_sma1_prev = IND_sma1
IND_sma1_vola = 0.0001      # Init
IND_sma1_alpha = 0.1
IND_sma1_vola_alpha = 0.01
IND_sma1_list = []
IND_sma1_vola_list = []
# SMA2 area                 Medium term sma, not used
IND_sma2 = prev_price
IND_sma2_alpha = 0.01
IND_sma2_list = []
# SMA3 area                 Long term sma, trend indicator  
IND_sma3 = prev_price
IND_sma3_prev = IND_sma3
IND_sma3_alpha = 0.001
IND_sma3_list = []
IND_sma3_delta_list = []

'''                     VOLATILITY INDICATORS AREA Not used
# VOL12 area                Volatility indicator, base sma1, reference sma2
IND_vol12 = 0.0001
IND_vol12_delta_prev = IND_vol12
IND_vol12_alpha = 0.01
IND_vol12_list = []
# VOL13 area                Volatility indicator, base sma1, reference sma3
IND_vol13 = 0.00001
IND_vol13_delta_prev = IND_vol13
IND_vol13_alpha = 1
IND_vol13_list = []
# VOL23 area                Volatility indicator, base sma2, reference sma3
IND_vol23 = 0.00001
IND_vol23_delta_prev = IND_vol23
IND_vol23_alpha = 0.01
IND_vol23_list = []
# MACD23 area               Trend indicator, base sma2, reference sma3
IND_macd23 = 0
IND_macd23_alpha = 1
IND_macd23_list = []
'''

# Gross indicators area
gross_alpha = 0.025
gross_01_d_sma = 0.1e-16    # Init
gross_0_d_sma = 0
gross_1_d_sma = 0
gross_01_ind_list = []
gross_0_ind_list = []
gross_1_ind_list = []


sma_price = prev_price
sma_price_prev = sma_price
d_sma_price = 0
price_d_m = []
sma_prices = []
d_sma_prices = []

for pos in lasts:
    # PUT directly, without calculations
    price_1_list.append(pos.price1)
    price_2_list.append(pos.price2)
    price_3_list.append(pos.price3)
    liq_1_list.append(pos.liq1)
    liq_2_list.append(pos.liq2)
    liq_3_list.append(pos.liq3)
    gross_1_list.append(pos.gross1)
    gross_2_list.append(pos.gross2)
    gross_3_list.append(pos.gross3)

    print(pos.gross2)

    # Volumes from fee gross changes
    if pos.search_max <= 0 or pos.search_min <= 0:
        print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.search_max, pos.search_min)
        gross_0_d = 0
        gross_1_d = 0
    else:
        gross_0_d = pos.search_max * price_ref - gross_0_prev
        gross_1_d = pos.search_min - gross_1_prev
        gross_0_prev = pos.search_max * price_ref
        gross_1_prev = pos.search_min
    gross_01_d = gross_0_d + gross_1_d
    # Volumes SMAs
    gross_01_d_sma = (1 - gross_alpha) * gross_01_d_sma + gross_alpha * gross_01_d 
    gross_01_ind_list.append(gross_01_d_sma)
    gross_0_d_sma = (1 - gross_alpha) * gross_0_d_sma + gross_alpha * gross_0_d 
    gross_0_ind_list.append(gross_0_d_sma)
    gross_1_d_sma = (1 - gross_alpha) * gross_1_d_sma + gross_alpha * gross_1_d 
    gross_1_ind_list.append(gross_1_d_sma)

    '''                 TIME CORRECTION DISABLED
        if aux_time is None or aux_time == 0 or aux_time == pos.timestamp:
            kd_time = 1
        else:
            kd_time = 60 / (pos.timestamp - aux_time).total_seconds()
        d_gross_corrected = gross_01_d * kd_time
    '''
    # # SMA1 area
    # IND_sma1 = (1 - IND_sma1_alpha) * IND_sma1 + IND_sma1_alpha * pos.price
    # IND_sma1_delta = abs(IND_sma1 - IND_sma1_prev) / IND_sma1_prev
    # IND_sma1_vola = (1 - IND_sma1_vola_alpha) * IND_sma1_vola + IND_sma1_vola_alpha * IND_sma1_delta
    # IND_sma1_list.append(IND_sma1)
    # IND_sma1_vola_list.append(IND_sma1_vola)
    # # SMA2 area
    # IND_sma2 = (1 - IND_sma2_alpha) * IND_sma2 + IND_sma2_alpha * pos.price
    # IND_sma2_list.append(IND_sma2)
    # # SMA3 area
    # IND_sma3 = (1 - IND_sma3_alpha) * IND_sma3 + IND_sma3_alpha * pos.price
    # IND_sma3_delta = abs((IND_sma3 - IND_sma3_prev) / IND_sma3_prev)
    # IND_sma3_list.append(IND_sma3)
    # IND_sma3_delta_list.append(IND_sma3_delta)

    '''                 VOLATILITY INDICATORS AREA Not used
    # VOL12 area
    IND_vol12_delta = IND_sma1 - IND_sma2
    IND_vol12_delta_t = abs(IND_vol12_delta - IND_vol12_delta_prev) / pos.price
    IND_vol12 = (1 - IND_vol12_alpha) * IND_vol12 + IND_vol12_alpha * IND_vol12_delta_t
    IND_vol12_list.append(IND_vol12)
    # VOL13 area
    IND_vol13_delta = IND_sma1 - IND_sma3
    IND_vol13_delta_t = abs(IND_vol13_delta - IND_vol13_delta_prev) / pos.price
    IND_vol13 = (1 - IND_vol13_alpha) * IND_vol13 + IND_vol13_alpha * IND_vol13_delta_t
    IND_vol13_list.append(IND_vol13)
    # VOL23 area
    IND_vol23_delta = IND_sma2 - IND_sma3
    IND_vol23_delta_t = abs(IND_vol23_delta - IND_vol23_delta_prev) / pos.price
    IND_vol23 = (1 - IND_vol23_alpha) * IND_vol23 + IND_vol23_alpha * IND_vol23_delta_t
    IND_vol23_list.append(IND_vol23)
    # MACD23 area
    IND_macd23_delta = (IND_sma2 - IND_sma3) / IND_sma3
    IND_macd23 = (1 - IND_macd23_alpha) * IND_macd23 + IND_macd23_alpha * IND_macd23_delta
    IND_macd23_list.append(IND_macd23)
    '''


    # Update aux variables
    aux_time = pos.timestamp
    prev_price = pos.price3
    # Previous indicators update
    IND_sma1_prev = IND_sma1
    IND_sma3_prev = IND_sma3
    ''' VOLATILITY INDICATORS AREA Not used
    IND_vol12_delta_prev = IND_vol12_delta
    IND_vol13_delta_prev = IND_vol13_delta
    IND_vol23_delta_prev = IND_vol23_delta
    '''


# Modify indicators for plotting
# gross_01_ind_list = np.sqrt(gross_01_ind_list) * 10**4 * 5     # volaty units, pool koef 0.05%
''' Fees mining, but trend suppression '''
# gross_0_ind_list = gross_01_ind_list - IND_sma3_delta_list
# gross_1_ind_list = np.sqrt(gross_1_ind_list)
# IND_my1 = np.sqrt(gross_01_ind_list) # / (np.array(d_sma_prices) * 10 + 1)


# =================================================================================== PLOTTING
plt.style.use('dark_background')
x = np.arange(len(lasts))
fig, ax1 = plt.subplots(figsize=(18, 12))
# ax1.plot(x, price_3_list, color="#CBDB389E", linewidth=1)
ax1.plot(x, price_2_list, color="#E68E1C9E", linewidth=1)
# ax1.plot(x, price_3_list, color="#E4E673B5", linewidth=1)
# =================================================================================== SIMPLE INDICATORS
# ax1.plot(x, IND_sma1_list, color="#FFFB23", linewidth=1)
# ax1.plot(x, IND_sma3_list, color="#FFA500", linewidth=1)
# =================================================================================== COMPLEX INDICATORS
ax2 = ax1.twinx()
# ax2.plot(x, gross_3_list, color="#70D3009E", linewidth=1)
ax2.plot(x, gross_2_list, color="#00B6469D", linewidth=1)
# ax2.plot(x, liq_3_list, color="#00BADB61", linewidth=1)
# ax2.plot(x, gross_0_ind_list, color="#FFFFFF97", linewidth=1)
plt.grid(True, linestyle="--", alpha=0.5)
fig.tight_layout()
plt.savefig('pictures/window_lines_' + str(discr) + '.png', dpi=200)
plt.close()





