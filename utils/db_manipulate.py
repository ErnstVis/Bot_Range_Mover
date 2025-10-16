from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math



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
    .filter(Position.id >= 10)
    .order_by(Position.id.desc())
    .limit(20)
    .all()
)


for row in lasts:
    print(row.id, row.position, row.range_MIN, row.range_MAX, row.timestamp_IN, row.native, row.step)





