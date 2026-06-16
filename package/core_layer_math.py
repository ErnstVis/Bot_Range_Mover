from dotenv import load_dotenv
import time
import os
import math
import json
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import random
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")

'''
In this file - bot math level, main logic functions, data base operations.
'''

Base: DeclarativeMeta = declarative_base()
class Positions(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)

    chain = Column(String)
    proto = Column(String)
    fee = Column(Integer)
    token0 = Column(String)
    token1 = Column(String)

    operation = Column(String)
    timestamp = Column(DateTime)
    delta0 = Column(Float)
    delta1 = Column(Float)
    delta_native = Column(Float)

    fees0 = Column(Float)
    fees1 = Column(Float)
    range_lo = Column(Float)
    range_hi = Column(Float)
    price = Column(Float)
    liq = Column(Float)
    nft = Column(Integer)
    tx_hash = Column(String(66))

    balance_0 = Column(Float)
    balance_1 = Column(Float)
    balance_native = Column(Float)

class ScanPool(Base):
    __tablename__ = "scan_pool"
    id = Column(Integer, primary_key=True)
    
    chain = Column(String)
    proto = Column(String)
    fee = Column(Integer)
    token0 = Column(String)
    token1 = Column(String)

    timestamp = Column(DateTime)
    price = Column(Float)
    price_lo = Column(Float)
    price_hi = Column(Float)
    
    locked0 = Column(Float)
    locked1 = Column(Float)
    liq = Column(Float)
    gross0 = Column(Float)
    gross1 = Column(Float)
    liq_net_u10 = Column(Float)
    liq_net_u30 = Column(Float)
    liq_net_d10 = Column(Float)
    liq_net_d30 = Column(Float)


# =============================================== Bot operations
class BotPos:
    def __init__(self, descriptor, inst_main):
        self.chain = inst_main
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
            self.P_hi = self.P_act
            self.P_lo = self.P_act
        self.P_min = self.range_min
        self.P_max = self.range_max
        self.rangemod_not_needed = False
        load_dotenv("private/secrets.env")

        engine = create_engine(os.getenv("SQL"), pool_pre_ping=True, pool_recycle=1800)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.Session = Session

        if self.nft_id and not self.mint_time:
            self.mint_time = datetime.now()
            
        self.L_fee = self.chain.L_fee
        for fee, pool in self.chain.pools.items():
            res = self.chain.get_liquidity(fee=fee)
            if res is not None:
                pool["liquidity"], pool["gross0"], pool["gross1"] = res
        print('-'*25, '\nInit bot layer completed\n')


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
                tx_hash, x0, x1 = self.chain.get_swap_ammount_router(self.amm0_get, self.amm1_limitation, 0, 'Q')
            else:
                self.amm1_limitation = -self.amm0_get * self.P_act * (1 - self.slippage)
                print('Limit1:', self.amm1_limitation)
                # self.chain.approve_token(-self.amm0_get, 0, 'r', wait=1)
                # self.chain.approve_token(0, 0, 'r', wait=1)
                self.chain.S_fee = self.scan_swap(-self.amm0_get, 1, 'I')
                tx_hash, x0, x1 = self.chain.get_swap_ammount_router(-self.amm0_get, self.amm1_limitation, 1, 'I')
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
                tx_hash, x0, x1 = self.chain.get_swap_ammount_router(self.amm1_get, self.amm0_limitation, 1, 'Q')
            else:
                self.amm0_limitation = -self.amm1_get / self.P_act * (1 - self.slippage)
                print('Limit0:', self.amm0_limitation)
                # self.chain.approve_token(-self.amm1_get, 1, 'r', wait=1)
                # self.chain.approve_token(0, 1, 'r', wait=1)
                self.chain.S_fee = self.scan_swap(-self.amm1_get, 0, 'I')
                tx_hash, x0, x1 = self.chain.get_swap_ammount_router(-self.amm1_get, self.amm0_limitation, 0, 'I')
            # self.amm0 -= self.amm1_get / self.P_act
            # self.amm1 += self.amm1_get  
            # am1new = (k * am0 * p) / (k + p)
        if tx_hash:
            with self.Session() as session:
                with session.begin():
                    row = Positions(
                        timestamp = datetime.now(),
                        delta0 = x0,
                        delta1 = x1
                    )
                    session.add(row)
            return 1
        else:
            print('Debug: swap failed')
            return 0

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
        tx_hash, x0, x1, self.nft_id, self.L = self.chain.liq_mint(self.P_min_tick, self.P_max_tick, self.amm0, self.amm1, wait=1)
        print('Pos id:', self.nft_id)
        print('Not used tokens:')
        if tx_hash:
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.P_min = self.chain.price_from_tick(self.P_min_tick)
            self.P_max = self.chain.price_from_tick(self.P_max_tick)
            self.mint_time = datetime.now()

            with self.Session() as session:
                with session.begin():
                    row = Positions(
                        timestamp=self.mint_time,
                        token0_in=x0,
                        token1_in=x1,
                        liq=self.L,
                        range_min=self.P_min,
                        range_max=self.P_max
                    )
                    session.add(row)
            return 1
        else:
            print('Debug: add failed')
            return 0

    def proc_increase(self):
        res = self.chain.get_current_tick()
        if res is not None:
            self.P_act_tick, self.P_act = res
        print('\nIncrease position assets:')
        self.amm0 = self.chain.get_balance_token(0)
        self.amm1 = self.chain.get_balance_token(1)
        print('='*25)
        tx_hash, x0, x1, self.L = self.chain.liq_increase(self.nft_id, self.amm0, self.amm1)
        if tx_hash:
            with self.Session() as session:
                with session.begin():
                    row = Positions(
                        chain=self.chain.chain_name,
                        proto=self.chain.proto_name,
                        fee=self.chain.L_fee,
                        token0=self.chain.token0_name,
                        token1=self.chain.token1_name,
                        operation='increase',
                        nft=self.nft_id,
                        tx_hash=tx_hash,

                        timestamp = datetime.now(),
                        delta0=x0,
                        delta1=x1,
                        price=self.P_act
                    )
                    session.add(row)
            return 1
        else:
            print('Debug: increase failed')
            return 0

    def proc_remove(self):
        tx_hash, x0, x1 = self.chain.liq_remove(self.nft_id)
        if tx_hash:
            with self.Session() as session:
                with session.begin():
                    row = Positions(
                        chain=self.chain.chain_name,
                        proto=self.chain.proto_name,
                        fee=self.chain.L_fee,
                        token0=self.chain.token0_name,
                        token1=self.chain.token1_name,
                        operation='remove',
                        nft=self.nft_id,
                        tx_hash=tx_hash,

                        timestamp = datetime.now(),
                        delta0=x0,
                        delta1=x1,
                        price=self.P_act
                    )
                    session.add(row)
            return 1
        else:
            print('Debug: remove failed')
            return 0

    def proc_collect(self):
        tx_hash, x0, x1 = self.chain.collect(self.nft_id)
        if tx_hash:
            self.amm0 = self.chain.get_balance_token(0)
            self.amm1 = self.chain.get_balance_token(1)
            self.native = self.chain.get_balance_native()

            with self.Session() as session:
                with session.begin():
                    row = Positions(
                        chain=self.chain.chain_name,
                        proto=self.chain.proto_name,
                        fee=self.chain.L_fee,
                        token0=self.chain.token0_name,
                        token1=self.chain.token1_name,
                        operation='collect',
                        nft=self.nft_id,
                        tx_hash=tx_hash,
                        
                        timestamp = datetime.now(),
                        delta0 = x0,
                        delta1 = x1,
                        price = self.P_act,

                        balance_0=self.amm0,
                        balance_1=self.amm1,
                        balance_native=self.native,
                    )
                    session.add(row)
            return 1
        else:
            print('Debug: collect failed')
            return 0


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

        print('\n\n\n', '=' * 25, 'Shifting')
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
        print('New TEO range:', self.P_min, self.P_max, '\n')


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


    def actuate_win_reg(self):
        res = self.chain.get_current_tick()
        if res is not None:
            self.P_act_tick, self.P_act = res
            if self.P_act > self.P_hi:
                self.P_hi = self.P_act
            if self.P_act < self.P_lo:
                self.P_lo = self.P_act
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

        # REFRESH CONFIG
        self.params = self.load_config(self.descriptor)
        for key, value in self.params.items():
            setattr(self, key, value)


    def collect_pool_state(self):
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

            # Updated part

            bal_0 = self.chain.get_balance_token(0, pool['address'])
            bal_1 = self.chain.get_balance_token(1, pool['address'])
            res = self.chain.get_liquidity(scaner=True, fee=fee)
            if res is not None:
                netliq_up_near, netliq_up_far, netliq_down_near, netliq_down_far = res

            # ADD TO DB
            now = datetime.now()
            with self.Session() as session:
                with session.begin():
                    row = ScanPool(
                        timestamp = now,
                        chain = self.chain.chain_name,
                        proto = 'uni3',
                        fee = fee,
                        price = self.P_act,
                        price_h = self.P_hi,
                        price_l = self.P_lo,
                        balance_0 = bal_0,
                        balance_1 = bal_1,
                        gross_0 = d0,
                        gross_1 = d1,
                        liq = pool.get("liquidity"),
                        liq_net_up_near = netliq_up_near,
                        liq_net_up_far = netliq_up_far,
                        liq_net_down_near = netliq_down_near,
                        liq_net_down_far = netliq_down_far
                    )
                    session.add(row)

        valid = {fee: data for fee, data in results.items() if data.get("gross", 0) > 0}
        if valid:
            self.L_fee = max(valid, key=lambda f: valid[f]["gross"])
        print(f"Gross best {self.L_fee} pool", results[self.L_fee]["gross"])

        # Updated part
        self.P_hi = self.P_act
        self.P_lo = self.P_act







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
    def load_config(desc, path='config/'):
        file_path = os.path.join(path, 'params' + str(desc) + '.json')
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"File {file_path} corrupted. Creating new.")
            return {}

    @staticmethod    
    def save_config(config, desc, path='config/'):
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, 'params' + str(desc) + '.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)