from dotenv import load_dotenv
import time
import os
import math
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import random
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")


Base: DeclarativeMeta = declarative_base()
class Positions(Base):
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

def make_scan_class(suffix):
    fast_table = "scan_fast_" + str(suffix)
    slow_table = "scan_slow_" + str(suffix)
    fast_cls = None
    if fast_table in Base.metadata.tables:
        for cls in Base._decl_class_registry.values():
            if hasattr(cls, "__tablename__") and cls.__tablename__ == fast_table:
                fast_cls = cls
                break
    slow_cls = None
    if slow_table in Base.metadata.tables:
        for cls in Base._decl_class_registry.values():
            if hasattr(cls, "__tablename__") and cls.__tablename__ == slow_table:
                slow_cls = cls
                break
    if fast_cls is None:
        class Scan_fast(Base):
            __tablename__ = fast_table
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
        fast_cls = Scan_fast
    if slow_cls is None:
        class Scan_slow(Base):
            __tablename__ = slow_table
            id = Column(Integer, primary_key=True)
            timestamp = Column(DateTime)
            proto = Column(String)
            fee = Column(Integer)
            price = Column(Float)
            gross = Column(Float)
            liq = Column(Float)
        slow_cls = Scan_slow
    return fast_cls, slow_cls


# =============================================== Bot operations
class BotPos:
    def __init__(self, descriptor, sim, inst_main):
        self.chain = inst_main
        self.sim = sim
        self.descriptor = descriptor
        self.params = self.load_config(self.descriptor)
        for key, value in self.params.items():
            setattr(self, key, value)
        self.amm0 = self.chain.get_balance_token(0)
        self.amm1 = self.chain.get_balance_token(1)
        self.native = self.chain.get_balance_native()
        res = self.chain.get_current_tick()
        if res is not None:
            self.P_act_tick, self.P_act = res
        self.P_min = self.init_min
        self.P_max = self.init_max
        self.rangemod_not_needed = False
        self.ScanFast, self.ScanSlow = make_scan_class(self.descriptor)
        load_dotenv("private/secrets.env")

        engine = create_engine(os.getenv("SQL"), pool_pre_ping=True, pool_recycle=1800)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.Session = Session

        # engine = create_engine(os.getenv("SQL"))
        # Base.metadata.create_all(engine)
        # Session = sessionmaker(bind=engine)
        # self.session = Session()

        self.db_check()
        self.L_fee = self.chain.L_fee
        for fee, pool in self.chain.pools.items():
            res = self.chain.get_liquidity(fee=fee)
            if res is not None:
                pool["liquidity"], pool["gross0"], pool["gross1"] = res
        print('-'*25, '\nInit bot layer completed\n')



    def db_check(self):
        with self.Session() as session:
            pos = (
                session.query(Positions)
                .filter(Positions.descriptor == self.descriptor)
                .order_by(Positions.id.desc())
                .first()
            )
            if pos is None or pos.step in (0, 5):
                pos = Positions(descriptor=self.descriptor, step=0)
                session.add(pos)
                session.commit()
                session.refresh(pos)   # получаем id
                print('Added')
            elif pos.step != 1:
                self.id = pos.position
                self.P_max = pos.range_MAX
                self.P_min = pos.range_MIN
                print('Last position ID:', self.id)
            else:
                print('Debug: incompleted position detected, step == 1, setting step to 0')
                self.rangemod_not_needed = True
                pos.step = 0
                session.commit()
            self.db_pos_id = pos.id
            self.step = pos.step
            if pos.timestamp_IN:
                self.timestamp_IN = pos.timestamp_IN
            else:
                self.timestamp_IN = datetime.now()
            print(
                'Complecting of last position:',
                self.step,
                'desc:',
                self.descriptor
            )


    # def db_check(self):
    #     session = self.Session()
    #     try:
    #         self.pos_data = (
    #             session.query(Positions)
    #             .filter(Positions.descriptor == self.descriptor)
    #             .order_by(Positions.id.desc())
    #             .first()
    #         )
    #     finally:
    #         session.close()
    #     # self.pos_data = self.session.query(Positions).filter(Positions.descriptor == self.descriptor).order_by(Positions.id.desc()).first()
    #     print(self.pos_data.id, self.pos_data.step, self.pos_data.position, self.pos_data.timestamp_IN, self.pos_data.descriptor)
    #     if self.pos_data is None:
    #         print('Debug: first line with current descriptor')
    #         self.db_add()
    #     if self.pos_data.step == 5 or self.pos_data.step == 0:
    #         print('Debug: step 0 or 5 detected, creating new DB entry')
    #         self.db_add()
    #     elif self.pos_data.step != 1:
    #         self.id = self.pos_data.position
    #         self.P_max = self.pos_data.range_MAX
    #         self.P_min = self.pos_data.range_MIN
    #         print('Last position ID:', self.id)
    #     else:
    #         self.pos_data.step = 0
    #         print('Debug: incompleted position detected, setting step to 0')
    #     self.step = self.pos_data.step
    #     print('Complecting of last position:', self.step, 'desc:', self.descriptor)
    
    # def db_add(self):
    #     self.pos_data = Positions(descriptor = self.descriptor, step = 0)
    #     session = self.Session()
    #     try:
    #         session.add(self.pos_data)
    #         session.commit()
    #     finally:
    #         session.close()
    #     # self.session.add(self.pos_data)
    #     # self.session.commit()

    # def db_add(self):
    #     with self.Session() as session:
    #         pos = Positions(descriptor=self.descriptor, step=0)
    #         session.add(pos)
    #         session.commit()
    #         session.refresh(pos)   # ← получаем id
    #         self.pos_id = pos.id



    def proc_shift(self):
        print('\n\n\n', '=' * 25, 'Shifting')
        if self.rangemod_not_needed == True:
            print('Range modification not needed, skipping...')
            self.step = 10
            return
        print('Old TEO range:', self.P_min, self.P_max)
        if self.prev_mode == 'D' and self.mode == 'U':
            self.P_max = self.P_min + self.range_width
        elif self.prev_mode == 'U' and self.mode == 'D':
            self.P_min = self.P_max - self.range_width
        elif self.prev_mode == 'U' and self.mode == 'U':
            self.P_min += self.range_width * self.range_shifter
            self.P_max = self.P_min + self.range_width
        elif self.prev_mode == 'D' and self.mode == 'D':
            self.P_max -= self.range_width * self.range_shifter
            self.P_min = self.P_max - self.range_width
        elif self.mode == 'T':
            top_k = (self.P_max - self.P_act) / (self.P_max - self.P_min)
            bottom_k = (self.P_act - self.P_min) / (self.P_max - self.P_min)
            self.P_max = self.P_act + self.range_width * top_k
            self.P_min = self.P_act - self.range_width * bottom_k
        self.step = 10
        print('New TEO range:', self.P_min, self.P_max, '\n')

    def proc_swap(self):
        print('\n', '=' * 25, 'Swaping')
        self.actuate_win_reg()
        print('Current price:', self.P_act, 'Range:', self.P_min, self.P_max)
        print('Balances:', self.amm0, self.amm1)
        check_U = (self.P_act - self.P_min) / (self.P_max - self.P_min) > 0.5
        if self.mode == 'D' or (self.mode == 'T' and not check_U):                                                # mode == 'UT' or mode == 'UF':
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
                self.chain.S_fee = self.scan_swap(self.amm0_get, 0, 'Q')
                x, x0, x1 = self.chain.get_swap_ammount_router(self.amm0_get, self.amm1_limitation, 0, 'Q')
            else:
                self.amm1_limitation = -self.amm0_get * self.P_act * (1 - self.slippage)
                print('Limit1:', self.amm1_limitation)
                # self.chain.approve_token(-self.amm0_get, 0, 'r', wait=1)
                # self.chain.approve_token(0, 0, 'r', wait=1)
                self.chain.S_fee = self.scan_swap(-self.amm0_get, 1, 'I')
                x, x0, x1 = self.chain.get_swap_ammount_router(-self.amm0_get, self.amm1_limitation, 1, 'I')
            # self.amm1 -= self.amm0_get * self.P_act
            # self.amm0 += self.amm0_get
            # am0new = k * am1 / (1 + k * p)
        elif self.mode == 'U' or (self.mode == 'T' and check_U):                                              # mode == 'DT' or mode == 'DF':
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
                self.chain.S_fee = self.scan_swap(self.amm1_get, 1, 'Q')
                x, x0, x1 = self.chain.get_swap_ammount_router(self.amm1_get, self.amm0_limitation, 1, 'Q')
            else:
                self.amm0_limitation = -self.amm1_get / self.P_act * (1 - self.slippage)
                print('Limit0:', self.amm0_limitation)
                # self.chain.approve_token(-self.amm1_get, 1, 'r', wait=1)
                # self.chain.approve_token(0, 1, 'r', wait=1)
                self.chain.S_fee = self.scan_swap(-self.amm1_get, 0, 'I')
                x, x0, x1 = self.chain.get_swap_ammount_router(-self.amm1_get, self.amm0_limitation, 0, 'I')
            # self.amm0 -= self.amm1_get / self.P_act
            # self.amm1 += self.amm1_get  
            # am1new = (k * am0 * p) / (k + p)

        if x == 1:
            self.db_check()
            self.step = 1
            session = self.Session()
            try:
                pos = session.get(Positions, self.db_pos_id)
                pos.token0_swap = x0
                pos.token1_swap = x1
                pos.step = self.step
                session.commit()
            finally:
                session.close()
        else:
            print('Debug: swap failed')
        return x



    def proc_open(self):
        print('\n', '=' * 25, 'Opening')
        print('Price prev:', self.P_act)
        self.chain.L_fee = self.L_fee
        res = self.chain.get_current_tick()
        if res is not None:
            self.P_act_tick, self.P_act = res
        print('\nTeo opening position assets:')
        self.amm0 = self.chain.get_balance_token(0)
        self.amm1 = self.chain.get_balance_token(1)
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
        x, x0, x1, self.id, self.L = self.chain.liq_add(self.P_min_tick, self.P_max_tick, self.amm0, self.amm1, wait=1)
        print('Pos id:', self.id)
        print('Not used tokens:')
        if x == 1:
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.step = 2
            session = self.Session()
            try:            
                pos = session.get(Positions, self.db_pos_id)
                pos.timestamp_IN = datetime.now()
                pos.token0_IN = x0
                pos.token1_IN = x1
                pos.position = self.id
                pos.liq = self.L
                pos.range_MIN = self.P_min = self.chain.price_from_tick(self.P_min_tick)
                pos.range_MAX = self.P_max = self.chain.price_from_tick(self.P_max_tick)
                pos.step = self.step
                session.commit()
            finally:
                session.close()
            # self.session.commit()

            # print teo min exit
            # print teo max exit
        else:
            print('Debug: add failed')
        return x

    def proc_close(self):
        if self.step == 2:
            time.sleep(1)
            x, x0, x1 = self.chain.liq_remove(self.id)
            if x == 1:
                self.step = 3
                session = self.Session()
                try:
                    pos = session.get(Positions, self.db_pos_id)
                    pos.token0_OUT = x0
                    pos.token1_OUT = x1
                    pos.price = self.P_act
                    pos.step = self.step
                    session.commit()
                finally:
                    session.close()
                # self.session.commit()
            else:
                print('Debug: remove failed')

            return x
        if self.step == 3:
            time.sleep(1)
            x, x0, x1 = self.chain.collect(self.id)
            if x == 1:
                self.step = 4
                session = self.Session()
                try:
                    pos = session.get(Positions, self.db_pos_id)
                    pos.timestamp_OUT = datetime.now()
                    pos.token0_fee = x0 - pos.token0_OUT
                    pos.token1_fee = x1 - pos.token1_OUT
                    pos.step = self.step
                    session.commit()
                finally:
                    session.close()
                # self.session.commit()
            else:
                print('Debug: collect failed')
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
                session = self.Session()
                try:
                    pos = session.get(Positions, self.db_pos_id)
                    pos.balance_0 = self.amm0
                    pos.balance_1 = self.amm1
                    pos.native = self.native
                    pos.step = self.step
                    session.commit()
                finally:
                    session.close()
                # self.session.commit()
            else:
                print('Debug: burn failed')

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
        print('\n\n\n', '=' * 25, 'Range modifying')
        if self.rangemod_not_needed == True:
            print('Range modification not needed, skipping...')
            self.rangemod_not_needed = False        # block modifications for auto mode. reset flag
            return
        print('Old TEO width:', self.range_width)
        if self.mode == 'T':
            self.range_width /= self.range_modifyer
        else:
            self.range_width *= self.range_modifyer
        if self.range_width > self.range_width_max:
            self.range_width = self.range_width_max
        if self.range_width < self.range_width_min:
            self.range_width = self.range_width_min
        print('New TEO width:', self.range_width, '\n')

    def scan_swap(self, amm, token, by):
        results = {}
        for fee in self.chain.pools:
            amount = self.chain.get_swap_ammount_quoter(amm, token, by, fee=fee)
            results[fee] = amount
        if by == 'I':
            best_fee = min(results, key=results.get)
        elif by == 'Q':
            best_fee = max(results, key=results.get)
        else:
            raise ValueError("Arg [by] must be 'I' or 'Q'")
        print(f"{by} mode. Best pool: {best_fee} result={results[best_fee]}")
        return best_fee

    def actuate_win_slow(self):
        print('Slow data parse...')
        results = {}
        for fee, pool in self.chain.pools.items():
            prev0 = pool["gross0"]
            prev1 = pool["gross1"]
            res = self.chain.get_liquidity(fee=fee)
            if res is not None:
                pool["liquidity"], pool["gross0"], pool["gross1"] = res
            d0 = pool["gross0"] - prev0
            d1 = pool["gross1"] - prev1
            if pool['reversed']:
                gross = d0 + d1 * self.P_act
            else:
                gross = d0 * self.P_act + d1
            res = self.chain.get_current_tick(fee=fee)
            if res is not None:
                tick, pool["price"] = res
            if fee == self.chain.L_fee:
                self.P_act_tick, self.P_act = tick, pool["price"]
                print('|--Lfee', fee, pool["price"], '--|', end='')
            results[fee] = {"liq": pool["liquidity"], "gross": gross, "price": pool["price"]}
            print('add result:', fee, results[fee])
        valid = {fee: data for fee, data in results.items() if data.get("gross", 0) > 0}
        if valid:
            self.L_fee = max(valid, key=lambda f: valid[f]["gross"])
        print(f"Gross best {self.L_fee} pool", results[self.L_fee]["gross"])
        now = datetime.now()
        # for fee, data in results.items():
        #     new_row = self.ScanSlow(
        #         timestamp = now,
        #         proto = 'uni3',
        #         fee = fee,
        #         price = data.get("price"),
        #         gross = data.get("gross"),
        #         liq = data.get("liq"))
        #     self.session.add(new_row)
        # self.session.commit()

        session = self.Session()
        try:
            for fee, data in results.items():
                new_row = self.ScanSlow(
                    timestamp = now,
                    proto = 'uni3',
                    fee = fee,
                    price = data.get("price"),
                    gross = data.get("gross"),
                    liq = data.get("liq")
                )
                session.add(new_row)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


    def actuate_win_reg(self):
        res = self.chain.get_current_tick()
        if res is not None:
            self.P_act_tick, self.P_act = res
        # animation (price level in range area)
        print(datetime.now(), end=' ')
        rng = self.P_max - self.P_min
        if rng <= 0:
            z1 = z2 = 15
        else:
            z1 = int(30 * (self.P_act - self.P_min) / (self.P_max - self.P_min))
            z1 = max(0, min(z1, 30))
            z2 = 30 - z1
        print('\t|', '.' * z1, '|', '.' * z2, '|', sep='')
        new_pos = self.ScanFast(
            timestamp = datetime.now(),
            price_dex = self.P_act,
            price_cex = math.nan,
            vola = math.nan,
            sma = math.nan,
            macd = math.nan,
            actual_max = self.P_max,
            actual_min = self.P_min,
            teo_new_max = math.nan,
            teo_new_min = math.nan)
        
        session = self.Session()
        try:
            session.add(new_pos)
            session.commit()
        finally:
            session.close()

        # self.session.add(new_pos)
        # self.session.commit()
        self.params = self.load_config(self.descriptor)
        self.params["teo_max"] = self.teo_max
        self.params["teo_min"] = self.teo_min
        self.save_config(self.params, self.descriptor)
        for key, value in self.params.items():
            setattr(self, key, value)


    def dyn_period_scale(self):
        var_times = self.dyn_period_max - self.dyn_period_min
        var_width = self.range_width_max - self.range_width_min
        var_ratio = var_width / var_times
        var_aux = (self.range_width - self.range_width_min) / var_ratio
        return self.dyn_period_max - var_aux
    
    def test_range_mod(self):
        min_check = self.range_width * ((1 / self.range_modifyer + 1) / 2) > self.range_width_min
        near_check = (
            (self.P_max - self.P_act) / (self.P_max - self.P_min) > self.range_limiter
            and (self.P_act - self.P_min) / (self.P_max - self.P_min) > self.range_limiter
        )
        return min_check and near_check

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
    def load_config(desc, path='config/params'):
        with open(path + str(desc) + '.json', 'r', encoding='utf-8') as f:
            return json.load(f)
        
    @staticmethod    
    def save_config(config, desc, path='config/params'):
        with open(path + str(desc) + '.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
