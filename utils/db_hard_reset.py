from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float
from dotenv import load_dotenv
import os


# 1. Ваша обновленная схема
Base = declarative_base()

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

# 2. Подключение к вашей базе PostgreSQL
# Замените на ваши реальные доступы (из .env или конфига)
load_dotenv("private/secrets.env")


def reset_database():
    engine = create_engine(os.getenv("SQL"))
    
    print("Удаление старых таблиц (если они были)...")
    # Метод drop_all удалит ТОЛЬКО таблицы, которые описаны в Base (positions и scan_pool)
    Base.metadata.drop_all(engine)
    
    print("Создание новых таблиц по свежей схеме...")
    Base.metadata.create_all(engine)
    
    print("Готово! База данных абсолютно чиста и обновлена.")

if __name__ == "__main__":
    reset_database()