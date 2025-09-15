from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import random




# === Подключение к SQLite ===
engine = create_engine("sqlite:///positions.db")  # echo=True покажет SQL-запросы
Base = declarative_base()
Session = sessionmaker(bind=engine)

# === Определение таблицы ===
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

# === Создание таблицы (один раз) ===
Base.metadata.create_all(engine)

# === Работаем через сессию ===
session = Session()

# 1. Добавление строки
pos1 = Position(token0_IN = 1000, token1_IN = 0.4, position = random.randint(100000, 999999), timestamp_IN = datetime.now())
session.add(pos1)
session.commit()

# 2. Чтение строк

print('-'*20)
positions = session.query(Position).all()
for p in positions:
    print(p.id, p.token0_IN, p.token1_IN, p.position, p.timestamp_IN, p.timestamp_OUT)

# # 3. Редактирование (например, поменяем цену первой позиции)
last_pos = session.query(Position).order_by(Position.id.desc()).first()
last_pos.token0_IN = 1111
session.commit()


print('-'*20)
positions = session.query(Position).all()
for p in positions:
    print(p.id, p.token0_IN, p.token1_IN, p.position, p.timestamp_IN, p.timestamp_OUT)

    
# # 4. Удаление строки
# session.delete(edit_pos)
# session.commit()

# print('-'*20)
# positions = session.query(Position).all()
# for p in positions:
    # print(p.id, p.token0_IN, p.token1_IN, p.position, p.timestamp_IN, p.timestamp_OUT)


