from package import BotPos, ChainLink
import math
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils")


chain = ChainLink('polygon', 'weth', 'usdt', 'uniswap', 'test')
pos = BotPos(2, 0, chain)

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


# print(pos.chain.get_liquidity())


# pos.range_width = 180
# print(pos.test_min_width())
# pos.range_width = 100
# print(pos.test_min_width())
# print(pos.dyn_period_scale())
# pos.range_width = 800
# print(pos.dyn_period_scale())
# pos.range_width = 1250
# print(pos.dyn_period_scale())

# a = datetime.now()
# time.sleep(2)
# b = datetime.now()
# c = b - a
# print(c)
# d = timedelta(seconds=2)
# print(d)
# print(c > d)










# p = 3752.0807
# mn = 3662.83
# mx = 3952.05


# w = mx - mn
# var_times = pos.dyn_period_max - pos.dyn_period_min
# var_width = pos.range_width_max - pos.range_width_min
# var_ratio = var_width / var_times
# var_aux = (w - pos.range_width_min) / var_ratio
# y = pos.dyn_period_max - var_aux
# print(y)


# z1 = int(50 * (p - mn) / (mx - mn))
# z2 = 50 - z1
# print(z1, z2)
# print('\t|', '.' * z1, '|', '.' * z2, '|', sep='')












# j = -191800 + 360
# for i in range(11):
#     print(pos.chain.price_from_tick(j))
#     j -= 360




# ============================================================== APROVE ALL
'''
pos.chain.approve_token(0, 0, 'r', wait=1)
pos.chain.approve_token(0, 1, 'r', wait=1)
pos.chain.approve_token(0, 0, 'm', wait=1)
pos.chain.approve_token(0, 1, 'm', wait=1)

'''



# ============================================================== POS ACTIONS
'''
pos_id = 2797759
position = pos.chain.contract_manager.functions.positions(pos_id).call()

nonce         = position[0]
operator      = position[1]
token0        = position[2] 
token1        = position[3]
fee           = position[4]
tick_lower    = position[5]
tick_upper    = position[6]
liquidity     = position[7]
feeGrowth0    = position[8]
feeGrowth1    = position[9]
tokensOwed0   = position[10]
tokensOwed1   = position[11]

print("Liquidity:", liquidity)
print("Range:", tick_lower, tick_upper)

pos.chain.liq_remove(pos_id)
pos.chain.collect(pos_id)

# pos.pos_data.step = 0
# pos.session.commit()
'''


# P_min = pos.chain.price_from_tick(tick_lower)
# P_max =  pos.chain.price_from_tick(tick_upper)
# print("Price range:", P_min, P_max, pos.chain.price_from_tick(-192160))
# ammount0_teo = liquidity * (math.sqrt(P_max) - math.sqrt(P_min)) / (math.sqrt(P_max) * math.sqrt(P_min))
# ammount1_teo = liquidity * (math.sqrt(P_max) - math.sqrt(P_min))
# print(pos.chain.decimals0, pos.chain.decimals1)
# print("Theoretical ammounts:", ammount0_teo / 10**(pos.chain.decimals0 - pos.chain.decimals1), ammount1_teo / 10**(pos.chain.decimals0 - pos.chain.decimals1))
# print("Theoretical ammounts eth in mid usd course:", (ammount0_teo/10**(pos.chain.decimals0 - pos.chain.decimals1)) * ((P_min + P_max)/2))







# ============================================================== DATABASE VIEW
'''
# pos.pos_data.step = 0
# pos.session.commit()

rows = (
    pos.session.query(Positions)
    .order_by(Positions.id.desc())
    .limit(1000)
    .all()
)

for r in rows:
    print(r.id, r.step, r.position, r.timestamp_IN, r.descriptor)
'''








# pos.step = 0
# pos.id = 2797759
# pos.proc_close()



# pos.proc_shift("UT")
# pos.proc_swap("UT")
# pos.proc_open("UT")

# pos.chain.send_token(2.377, 1)
# pos.chain.send_native(9.824)