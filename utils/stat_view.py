from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

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
    .order_by(Position.id.desc())
    .limit(3)
    .all()
)

for row in lasts:
    print('|Pos:', row.position, row.range_MIN, row.range_MAX, row.descriptor)
    print('|IN:', row.token0_IN, row.token1_IN)
    print('|OUT:', row.token0_OUT, row.token1_OUT)
    print('|Fee:', row.token0_fee, row.token1_fee)
    print('|Swap:', row.token0_swap, row.token1_swap)
    print('|Balance:', row.balance_0, row.balance_1, row.native)
    print('-'*40)
   