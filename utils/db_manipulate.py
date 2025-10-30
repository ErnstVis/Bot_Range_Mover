from sqlalchemy import create_engine, select, delete, text, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math


engine = create_engine("sqlite:///data/positions.db")


# with engine.connect() as conn:
#     conn.execute(text("ALTER TABLE scan_window ADD COLUMN timestamp DateTime;"))

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
    price = Column(Float)
    liq = Column(Float)
    step = Column(Integer)

# class Scan_window(Base):
#     __tablename__ = "scan_window"
#     id = Column(Integer, primary_key=True)
    # timestamp = Column(DateTime)
#     price = Column(Float)
#     search_max = Column(Float)
#     search_min = Column(Float)
#     actual_max = Column(Float)
#     actual_min = Column(Float)

engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()


row = session.query(Position).filter_by(id=21).first()

if row:
    row.token0_swap = 0.032224291445 - 0.01884269
    row.token1_swap = -49.5
    print(row.token1_swap / row.token0_swap)
    session.commit()
    print("OK")
else:
    print("Not OK")

session.close()
# subquery = (
#     session.query(Scan_window.id)
#     .order_by(Scan_window.id.desc())
#     .offset(300)  # пропускаем 500 последних
#     .limit(1)     # берём 501-ю запись — это наш порог
#     .scalar_subquery()
# )
# session.execute(delete(Scan_window).where(Scan_window.id < subquery))
# session.commit()






# lasts = (
#     session.query(Position)
#     .filter(Position.descriptor == 1)
#     .filter(Position.id >= 10)
#     .order_by(Position.id.desc())
#     .limit(20)
#     .all()
# )


# for row in lasts:
#     print(row.id, row.position, row.range_MIN, row.range_MAX, row.timestamp_IN, row.native, row.step)





