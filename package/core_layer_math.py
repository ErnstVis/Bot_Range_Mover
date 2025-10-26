import time
import os
import math
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import random
import sys
sys.stdout.reconfigure(encoding="utf-8")


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
    step = Column(Integer)

class Scan_window(Base):
    __tablename__ = "scan_window"
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    search_max = Column(Float)
    search_min = Column(Float)
    actual_max = Column(Float)
    actual_min = Column(Float)


# ===================================================================================== Bot operations
class BotPos:
    def __init__(self, descriptor, sim, inst_main):
        self.chain = inst_main
        self.sim = sim
        self.descriptor = descriptor
        self.params = BotPos.load_config()
        for key, value in self.params.items():
            setattr(self, key, value)
        self.actuate()
        engine = create_engine("sqlite:///data/positions.db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.db_check()
        self.teo_max = 0
        self.teo_min = 0
        print('-'*25, '\nInit bot layer completed\n')

    def db_check(self):
        self.pos_data = self.session.query(Position).filter(Position.descriptor == self.descriptor).order_by(Position.id.desc()).first()
        if self.pos_data is None:
            self.db_add()
        if self.pos_data.step == 5 or self.pos_data.step == 0:
            self.db_add()
        elif self.pos_data.step != 1:
            self.id = self.pos_data.position
            self.P_max = self.pos_data.range_MAX
            self.P_min = self.pos_data.range_MIN
            print('Last position ID:', self.id)
        self.step = self.pos_data.step
        print('Complecting of last position:', self.step)
    
    def db_add(self):
        self.pos_data = Position(descriptor = self.descriptor, step = 0)
        self.session.add(self.pos_data)
        self.session.commit()

    def proc_shift(self):
        range_move_unknown = (self.range_move_trend + self.range_move_float) / 2
        if self.mode == 'U' and self.prev_mode == 'U':
            self.P_max = self.P_act + self.range_width * self.range_move_trend
            self.P_min = self.P_act - self.range_width * (1 - self.range_move_trend)
        elif self.mode == 'D' and self.prev_mode == 'D':
            self.P_min = self.P_act - self.range_width * self.range_move_trend
            self.P_max = self.P_act + self.range_width * (1 - self.range_move_trend)
        elif self.mode == 'U' and self.prev_mode == 'D':
            self.P_max = self.P_act + self.range_width * self.range_move_float
            self.P_min = self.P_act - self.range_width * (1 - self.range_move_float)
        elif self.mode == 'D' and self.prev_mode == 'U':
            self.P_min = self.P_act - self.range_width * self.range_move_float
            self.P_max = self.P_act + self.range_width * (1 - self.range_move_float)
        elif self.mode == 'U' and self.prev_mode == 'T':
            self.P_max = self.P_act + self.range_width * range_move_unknown
            self.P_min = self.P_act - self.range_width * (1 - range_move_unknown)
        elif self.mode == 'D' and self.prev_mode == 'T':
            self.P_min = self.P_act - self.range_width * range_move_unknown
            self.P_max = self.P_act + self.range_width * (1 - range_move_unknown)
        elif self.mode == 'T':
            self.P_min = self.P_act - self.range_width * 0.5
            self.P_max = self.P_act + self.range_width * 0.5
        print('\n\n\n', '=' * 25, 'Shifting, bot layer')
        print('New TEO range:', self.P_min, self.P_max, 'Width:', self.range_width, '\n')

    def proc_swap(self):
        print('\n\n\n', '=' * 25, 'Swaping, bot layer')
        self.fee = 100
        self.chain.dyn_pool_swich()
        print('Current price:', self.P_act, 'Range:', self.P_min, self.P_max)
        print('Balances:', self.amm0, self.amm1)
        if self.mode == 'U' or self.mode == 'D' or self.mode == 'T':                                                # mode == 'UT' or mode == 'UF':
            self.amm1_teo_full = self.amm1 + self.amm0 * self.P_act
            self.k0 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 0)
            self.amm0_get_full = (self.k0 * self.amm1_teo_full) / (1 + self.k0 * self.P_act)
            self.amm0_get = self.amm0_get_full - self.amm0
            print("Buy operation. K0:", self.k0)
            print('Token1 full:', self.amm1_teo_full, 'Token0 get full:', self.amm0_get_full, 'Token0 get:', self.amm0_get)
            if self.amm0_get > 0:
                self.amm1_limitation = self.amm0_get * self.P_act * (1 + self.slippage)
                print('Limit1:', self.amm1_limitation)
                # self.chain.approve_token(self.amm1_limitation, 1, 'r', wait=1)
                # self.chain.approve_token(0, 1, 'r', wait=1)
                x, x0, x1 = self.chain.get_swap_ammount_router(self.amm0_get, self.amm1_limitation, 0, by='Q')
            else:
                self.amm1_limitation = -self.amm0_get * self.P_act * (1 - self.slippage)
                print('Limit1:', self.amm1_limitation)
                # self.chain.approve_token(-self.amm0_get, 0, 'r', wait=1)
                # self.chain.approve_token(0, 0, 'r', wait=1)
                x, x0, x1 = self.chain.get_swap_ammount_router(-self.amm0_get, self.amm1_limitation, 1, by='I')
            # self.amm1 -= self.amm0_get * self.P_act
            # self.amm0 += self.amm0_get
            # am0new = k * am1 / (1 + k * p)
        elif self.mode == 'TESTME':                                              # mode == 'DT' or mode == 'DF':
            self.amm0_teo_full = self.amm0 + self.amm1 / self.P_act
            self.k1 = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, 1, 1)
            self.amm1_get_full = (self.k1 * self.amm0_teo_full * self.P_act) / (self.k1 + self.P_act)
            self.amm1_get = self.amm1_get_full - self.amm1
            print("Sell operation. K1:", self.k1)
            print('Token0 full:', self.amm0_teo_full, 'Token1 get full:', self.amm1_get_full, 'Token1 get:', self.amm1_get)
            if self.amm1_get > 0:
                self.amm0_limitation = self.amm1_get / self.P_act * (1 + self.slippage)
                print('Limit0:', self.amm0_limitation)
                # self.chain.approve_token(self.amm0_limitation, 0, 'r', wait=1)
                # self.chain.approve_token(0, 0, 'r', wait=1)
                x, x0, x1 = self.chain.get_swap_ammount_router(self.amm1_get, self.amm0_limitation, 1, by='Q')
            else:
                self.amm0_limitation = -self.amm1_get / self.P_act * (1 - self.slippage)
                print('Limit0:', self.amm0_limitation)
                # self.chain.approve_token(-self.amm1_get, 1, 'r', wait=1)
                # self.chain.approve_token(0, 1, 'r', wait=1)
                x, x0, x1 = self.chain.get_swap_ammount_router(-self.amm1_get, self.amm0_limitation, 0, by='I')
            # self.amm0 -= self.amm1_get / self.P_act
            # self.amm1 += self.amm1_get  
            # am1new = (k * am0 * p) / (k + p)
        if x == 1:
            self.db_check()
            self.step = 1
            self.pos_data.token0_swap = x0
            self.pos_data.token1_swap = x1
            self.pos_data.step = self.step
            self.session.commit()
        return x

    def proc_open(self):
        print('\n\n\n', '=' * 25, 'Opening, bot layer')
        self.fee = 500
        self.chain.dyn_pool_swich()
        print('Price prev:', self.P_act)
        self.P_act_tick, self.P_act = self.chain.get_current_tick()
        x00 = self.P_act
        print('\nTeo opening position assets:')
        x01 = self.amm0 = self.chain.get_balance_token(0)
        x02 = self.amm1 = self.chain.get_balance_token(1)
        print('='*25)
        if self.mode == 'U':                                                # mode == 'UT' or mode == 'UF':
            print('Act:', self.P_act_tick, self.chain.price_from_tick(self.P_act_tick))
            self.P_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_min), direction='s')
            print('Min:', self.P_min, self.P_min_tick, self.chain.price_from_tick(self.P_min_tick))
            self.bruto_max = BotPos.clc_rng(self.chain.price_from_tick(self.P_min_tick), self.chain.price_from_tick(self.P_act_tick), self.amm0, self.amm1)
            print('Recalc max:', self.bruto_max)
            self.P_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.bruto_max), direction='s')
            print('Max:', self.P_max_tick, self.chain.price_from_tick(self.P_max_tick))
            # self.amm1_lock = self.amm1
            # self.amm0_lock = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, self.amm1_lock, 0)
            # self.L = self.amm1_lock / (math.sqrt(self.P_act) - math.sqrt(self.P_min))
            # self.L2 = self.amm0_lock / ((math.sqrt(self.P_max) - math.sqrt(self.P_act)) / (math.sqrt(self.P_max) * math.sqrt(self.P_act)))
        elif self.mode == 'D':                                              # mode == 'DT' or mode == 'DF':
            print('Act:', self.P_act_tick, self.chain.price_from_tick(self.P_act_tick))
            self.P_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_max), direction='s')
            print('Max:', self.P_max, self.P_max_tick, self.chain.price_from_tick(self.P_max_tick))
            self.bruto_min = BotPos.clc_rng(self.chain.price_from_tick(self.P_max_tick), self.chain.price_from_tick(self.P_act_tick), self.amm0, self.amm1)
            print('Recalc min:', self.bruto_min)
            self.P_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.bruto_min), direction='s')
            print('Min:', self.P_min_tick, self.chain.price_from_tick(self.P_min_tick))
            # self.amm0_lock = self.amm0
            # self.amm1_lock = BotPos.clc_amm(self.P_min, self.P_max, self.P_act, self.amm0_lock, 1)
            # self.L = self.amm1_lock / (math.sqrt(self.P_act) - math.sqrt(self.P_min))
            # self.L2 = self.amm0_lock / ((math.sqrt(self.P_max) - math.sqrt(self.P_act)) / (math.sqrt(self.P_max) * math.sqrt(self.P_act)))
        else:
            print('Act:', self.P_act_tick, self.chain.price_from_tick(self.P_act_tick))
            self.P_min_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_min), direction='s')
            print('Min:', self.P_min, self.P_min_tick, self.chain.price_from_tick(self.P_min_tick))
            self.P_max_tick = self.chain.tick_normalize(self.chain.tick_from_price(self.P_max), direction='s')
            print('Max:', self.P_max, self.P_max_tick, self.chain.price_from_tick(self.P_max_tick))
        #==========================================================Approve dont needed==========================
        # self.chain.approve_token(self.amm0, 0, 'm', wait=1)
        # self.chain.approve_token(self.amm1, 1, 'm', wait=1)
        # self.chain.approve_token(0, 0, 'm', wait=1)
        # self.chain.approve_token(0, 1, 'm', wait=1)
        x, x0, x1, self.id = self.chain.liq_add(self.P_min_tick, self.P_max_tick, self.amm0, self.amm1, wait=1)
        print('Pos id:', self.id)
        if x == 1:
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.step = 2
            self.pos_data.timestamp_IN = datetime.now()
            print('=' * 10, 'To pool gone:', x0, x1)
            self.pos_data.token0_IN = x0
            self.pos_data.token1_IN = x1
            self.pos_data.position = self.id
            self.pos_data.range_MIN = self.chain.price_from_tick(self.P_min_tick)
            self.pos_data.range_MAX = self.chain.price_from_tick(self.P_max_tick)
            self.pos_data.step = self.step
            self.session.commit()
            # print teo min exit
            # print teo max exit
        return x

    def proc_close(self):
        if self.step == 2:
            time.sleep(1)
            x, x0, x1 = self.chain.liq_remove(self.id)
            if x == 1:
                self.step = 3
                self.pos_data.token0_OUT = x0
                self.pos_data.token1_OUT = x1
                self.pos_data.price = self.P_act
                self.pos_data.step = self.step
                self.session.commit()
            return x
        if self.step == 3:
            time.sleep(1)
            x, x0, x1 = self.chain.collect(self.id)
            if x == 1:
                self.step = 4
                self.pos_data.timestamp_OUT = datetime.now()
                self.pos_data.token0_fee = x0 - self.pos_data.token0_OUT
                self.pos_data.token1_fee = x1 - self.pos_data.token1_OUT
                self.pos_data.step = self.step
                self.session.commit()
            return x
        if self.step == 4:
            time.sleep(1)
            # x, _ = self.chain.burn(self.id)
            x = 1
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.native = self.chain.get_balance_native()
            if x == 1:
                self.step = 5
                self.pos_data.balance_0 = self.amm0
                self.pos_data.balance_1 = self.amm1
                self.pos_data.native = self.native
                self.pos_data.step = self.step
                self.session.commit()
            return x
        return 0
        # if mode == 'UT' or mode == 'UF':
        #     self.amm0_lock = 0
        #     self.amm1_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min))
        # elif mode == 'DT' or mode == 'DF':
        #     self.amm0_lock = self.L * (math.sqrt(self.P_max) - math.sqrt(self.P_min)) / (math.sqrt(self.P_max) * math.sqrt(self.P_min))
        #     self.amm1_lock = 0
        # self.L = 0

    def proc_modify(self):
        if self.mode == 'T':
            self.range_width *= self.range_scale_stable
        else:
            self.range_width *= self.range_scale_fluctuate
        if self.range_width > self.range_width_max:
            self.range_width = self.range_width_max
        if self.range_width < self.range_width_min:
            self.range_width = self.range_width_min

    def actuate(self, show=1):
        if show:
            print('Refresh values =================')
        self.amm0 = self.chain.get_balance_token(0, show)
        self.amm1 = self.chain.get_balance_token(1, show)
        self.native = self.chain.get_balance_native(show)
        self.P_act_tick, self.P_act = self.chain.get_current_tick(show)
        print('\n')

    def actuate_short(self, show=1):
        if show:
            print(datetime.now(), end=' ')
        self.P_act_tick, self.P_act = self.chain.get_current_tick(show)
        z1 = int(30 * (self.P_act - self.P_min) / (self.P_max - self.P_min))
        z1 = max(0, min(z1, 30))
        z2 = 30 - z1
        if show:
            print('\t|', '.' * z1, '|', '.' * z2, '|', sep='')
        
        if self.teo_max < self.P_act:
            self.teo_max = self.P_act
        else:
            dif_max = self.teo_max - self.P_act
            self.teo_max -= dif_max * 0.001
        if self.teo_min > self.P_act or self.teo_min == 0:
            self.teo_min = self.P_act
        else:
            dif_min = self.P_act - self.teo_min
            self.teo_max += dif_min * 0.001
        
        new_pos = Scan_window(
            price = self.P_act,
            search_max = self.teo_max,
            search_min = self.teo_min,
            actual_max = self.P_max,
            actual_min = self.P_min
        )
        self.session.add(new_pos)
        self.session.commit()


    def dyn_period_scale(self):
        var_times = self.dyn_period_max - self.dyn_period_min
        var_width = self.range_width_max - self.range_width_min
        var_ratio = var_width / var_times
        var_aux = (self.range_width - self.range_width_min) / var_ratio
        return self.dyn_period_max - var_aux
    
    def test_min_width(self):
        return self.range_width * ((self.range_scale_stable + 1) / 2) > self.range_width_min



    @staticmethod
    def clc_amm(P_min, P_max, P, ammount_in, target):
        if target:
            L = ammount_in / ((math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P)))
            ammount_out = L * (math.sqrt(P) - math.sqrt(P_min))
        else:
            L = ammount_in / (math.sqrt(P) - math.sqrt(P_min))
            ammount_out = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
        return ammount_out
    
    @staticmethod
    def clc_rng(P_border, P, ammount_0, ammount_1):
        if P_border > P:
            sqrt_P = math.sqrt(P)
            sqrt_P_max = math.sqrt(P_border)
            L = ammount_0 / ((sqrt_P_max - sqrt_P) / (sqrt_P_max * sqrt_P))
            P_min = (sqrt_P - ammount_1 / L) ** 2
            return P_min
        else:
            sqrt_P = math.sqrt(P)
            sqrt_P_min= math.sqrt(P_border)
            L = ammount_1 / (sqrt_P - sqrt_P_min)
            # ammount_0 = L * (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
            # ammount_0 / L = (math.sqrt(P_max) - math.sqrt(P)) / (math.sqrt(P_max) * math.sqrt(P))
            # math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P_max) - math.sqrt(P)
            # math.sqrt(P_max) - math.sqrt(P_max) * math.sqrt(P) * (ammount_0 / L) = math.sqrt(P)
            # math.sqrt(P_max) * (1 - math.sqrt(P) * (ammount_0 / L)) = math.sqrt(P)
            # math.sqrt(P_max) = math.sqrt(P) / (1 - math.sqrt(P) * (ammount_0 / L))
            P_max = (sqrt_P / (1 - sqrt_P * (ammount_0 / L))) ** 2
            return P_max
    
    @staticmethod
    def load_config(path='config/params.json'):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    @staticmethod    
    def save_config(config, path='config/params.json'):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
