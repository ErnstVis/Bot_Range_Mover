from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import math



def make_avg(window_size):
    values = []
    def add(x):
        values.append(x)
        if len(values) > window_size:
            values.pop(0)
        return sum(values) / len(values)
    return add


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



discr = [2]              # refresh needed pairs
gross_sma_prd = 30
fees = [100, 500, 3000, 10000]

for val in discr:
    Base = declarative_base()
    class Scan_fast(Base):
        __tablename__ = "scan_fast_" + str(val)
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime)
        price_dex = Column(Float)
        price_cex = Column(Float)
        vola = Column(Float)
        sma = Column(Float)
        macd = Column(Float)
        actual_max = Column(Float)
        actual_min = Column(Float)
        teo_new_max = Column(Float)
        teo_new_min = Column(Float)
    class Scan_slow(Base):
        __tablename__ = "scan_slow_" + str(val)
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime)
        proto = Column(String)
        fee = Column(Integer)
        gross = Column(Float)
        liq = Column(Float)

    load_dotenv("private/secrets.env")
    engine = create_engine(os.getenv("SQL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    print('============', val)

    '''
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
    '''

    lasts_fast = (
        session.query(Scan_fast)
        .where(Scan_fast.id > 0)
        .order_by(Scan_fast.id.asc())
        .all())
    
    lasts_slow = (
        session.query(Scan_slow)
        .where(Scan_slow.id > 0)
        .where(Scan_slow.fee == 3000)
        .order_by(Scan_slow.id.asc())
        .all())

    # print()
    # print(lasts_fast[-1].actual_min)
    # print(lasts_fast[-1].actual_max)
    # print(dyn_period_scale(lasts_fast[-1].actual_min, lasts_fast[-1].actual_max))
    # print(timedelta(hours=dyn_period_scale(lasts_fast[-1].actual_min, lasts_fast[-1].actual_max)))
    # print(target_time)
    # print(target_time + timedelta(hours=dyn_period_scale(lasts[-1].actual_min, lasts[-1].actual_max)))
    print()

    price_ref = lasts_fast[-1].price_dex
    # liq = 53394952765201.0
    # print("Tok0 Gross finish:", lasts[-1].search_max)
    # print("Tok0 Gross finish:", lasts[-1].search_min)
    # finish_tok0 = lasts[-1].search_max
    # finish_tok1 = lasts[-1].search_min
    # print('\nTotal Tok0 Gross:', finish_tok0 - start_tok0)
    # print('Total Tok1 Gross:', finish_tok1 - start_tok1, '\n')
    # print('Abs Tok0 gross $:', (finish_tok0 - start_tok0) * liq * price_ref)
    # print('Abs Tok1 gross:', (finish_tok1 - start_tok1) * liq)



    # =================================================================================== INDICATORS CALCULATION AREA



    '''
    gross1_avr = make_avg(60)
    gross2_avr = make_avg(60)
    gross3_avr = make_avg(60)
    gross4_avr = make_avg(60)
    # ================== Prepare new part



    prev_price = lasts[0].price2
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



    # Gross indicators area
    gross_alpha = 0.025
    gross_01_d_sma = 0.1e-16    # Init
    gross_0_d_sma = 0
    gross_1_d_sma = 0
    gross_01_ind_list = []
    gross_0_ind_list = []
    gross_1_ind_list = []
    '''

    # sma_price = prev_price
    # sma_price_prev = sma_price
    d_sma_price = 0
    price_d_m = []
    sma_prices = []
    d_sma_prices = []


    price_dex_list = []
    timestamp_list_fast = []
    prices_act_min_list = []
    prices_act_max_list = []
    for pos in lasts_fast:
        timestamp_list_fast.append(pos.timestamp)
        price_dex_list.append(pos.price_dex)
        # print('DEBUG:', pos.timestamp, 'Price DEX:, ', pos.price_dex)
        # prices_act_min_list.append(pos.actual_min)
        # prices_act_max_list.append(pos.actual_max)
        # liq_4_list.append(pos.liq4)
        # if pos.gross1 < 0 or pos.gross1 > 1e-14:
        #     print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.gross1)
        #     gross_1_list.append(gross1_avr(0))
        # else:
        #     gross_1_list.append(gross1_avr(pos.gross1))
        # if pos.gross2 < 0 or pos.gross2 > 1e-14:
        #     print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.gross2)
        #     gross_2_list.append(gross2_avr(0))
        # else:
        #     gross_2_list.append(gross2_avr(pos.gross2))
        # if pos.gross3 < 0 or pos.gross3 > 1e-14:
        #     print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.gross3)
        #     gross_3_list.append(gross3_avr(0))
        # else:
        #     gross_3_list.append(gross3_avr(pos.gross3))
        # if pos.gross4 < 0 or pos.gross4 > 1e-14:
        #     print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.gross4)
        #     gross_4_list.append(gross4_avr(0))
        # else:
        #     gross_4_list.append(gross4_avr(pos.gross4))


        # Volumes from fee gross changes
        # if pos.search_max <= 0 or pos.search_min <= 0:
        #     print('DEBUG:', pos.timestamp, 'D_grosses:, ', pos.search_max, pos.search_min)
        #     gross_0_d = 0
        #     gross_1_d = 0
        # else:
        #     gross_0_d = pos.search_max * price_ref - gross_0_prev
        #     gross_1_d = pos.search_min - gross_1_prev
        #     gross_0_prev = pos.search_max * price_ref
        #     gross_1_prev = pos.search_min
        # gross_01_d = gross_0_d + gross_1_d
        # # Volumes SMAs
        # gross_01_d_sma = (1 - gross_alpha) * gross_01_d_sma + gross_alpha * gross_01_d 
        # gross_01_ind_list.append(gross_01_d_sma)
        # gross_0_d_sma = (1 - gross_alpha) * gross_0_d_sma + gross_alpha * gross_0_d 
        # gross_0_ind_list.append(gross_0_d_sma)
        # gross_1_d_sma = (1 - gross_alpha) * gross_1_d_sma + gross_alpha * gross_1_d 
        # gross_1_ind_list.append(gross_1_d_sma)


        # # Update aux variables
        # aux_time = pos.timestamp
        # prev_price = pos.price3
        # # Previous indicators update
        # IND_sma1_prev = IND_sma1
        # IND_sma3_prev = IND_sma3
    
    timestamp_list_slow = []
    gross_list = []
    liq_list = []
    for pos in lasts_slow:
        timestamp_list_slow.append(pos.timestamp)
        gross_list.append(pos.gross)
        liq_list.append(pos.liq)


    # ============================================================= PLOTTING
    plt.style.use('dark_background')
    # x = np.arange(len(lasts))
    fig, ax1 = plt.subplots(figsize=(18, 12))
    ax1.plot(timestamp_list_fast, price_dex_list, color="#FF008CFF", linewidth=1)
    # ax1.plot(timestamp_list, price_2_list, color="#77E61C9E", linewidth=1)
    # ax1.plot(timestamp_list, price_3_list, color="#E4E673B5", linewidth=1)
    # ax1.plot(timestamp_list, price_4_list, color="#DB965DB5", linewidth=1)
    # ax1.plot(timestamp_list, prices_act_min_list, color="magenta", linewidth=1)
    # ax1.plot(timestamp_list, prices_act_max_list, color="magenta", linewidth=1)
    # ============================================================= SIMPLE INDICATORS
    # ax1.plot(x, IND_sma1_list, color="#FFFB23", linewidth=1)
    # ax1.plot(x, IND_sma3_list, color="#FFA500", linewidth=1)
    # ============================================================= COMPLEX INDICATORS
    ax2 = ax1.twinx()
    ax2.plot(timestamp_list_slow, gross_list, color="#88FF00FF", linewidth=1)
    # ax2.plot(timestamp_list, gross_3_list, color="#0083DB9B", linewidth=1)
    # ax2.plot(timestamp_list, gross_4_list, color="#003ADB89", linewidth=1)

    # ax2.plot(x, liq_1_list, color="#5DAF00AB", linewidth=1)
    # ax2.plot(x, liq_2_list, color="#B600989D", linewidth=1)
    # ax2.plot(x, liq_3_list, color="#003ADB89", linewidth=1)
    ax3 = ax1.twinx()
    # ax3.get_yaxis().set_visible(False)
    ax3.tick_params(labelleft=False, labelright=False)
    ax3.plot(timestamp_list_slow, liq_list, color="#0066FFFF", linewidth=1)


    plt.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    plt.savefig('pictures/window_lines_' + str(val) + '.png', dpi=200)
    plt.close()





