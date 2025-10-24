from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math



Base = declarative_base()
class Scan_window(Base):
    __tablename__ = "scan_window"
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    search_max = Column(Float)
    search_min = Column(Float)
    actual_max = Column(Float)
    actual_min = Column(Float)



engine = create_engine("sqlite:///data/positions.db")
Session = sessionmaker(bind=engine)
session = Session()


lasts = (
    session.query(Scan_window)
    .order_by(Scan_window.id.asc())
    .all()
)
prices = [pos.price for pos in lasts]
prices_min = [pos.search_max for pos in lasts]
prices_max = [pos.search_min for pos in lasts]
prices_teo_min = [pos.actual_min for pos in lasts]
prices_teo_max = [pos.actual_max for pos in lasts]

x = np.arange(len(lasts))
fig, ax1 = plt.subplots(figsize=(18, 12))
# --- Левая ось (доллары) ---
ax1.set_xlabel("Profits")
ax1.set_ylabel("Dollars", color="black")
ax1.plot(x, prices, color="orange", label="Loss ($)", linewidth=2)
ax1.plot(x, prices_min, color="cyan", label="Gas ($)", linewidth=2)
ax1.plot(x, prices_max, color="cyan", label="Profit ($)", linewidth=2)
ax1.plot(x, prices_teo_min, color="green", label="Fee ($)", linewidth=2)
ax1.plot(x, prices_teo_max, color="green", label="Fee ($)", linewidth=2)
ax1.tick_params(axis="y", labelcolor="black")
# --- Правая ось (проценты) ---
# ax2 = ax1.twinx()
# ax2.set_ylabel("Percent", color="grey")
# ax2.plot(x, loss_var_alt_m, color="orange", linestyle="--", label="Loss (%)", linewidth=2, alpha=0.6)
# ax2.plot(x, gas_costs_alt_m, color="red", linestyle="--", label="Gas (%)", linewidth=2, alpha=0.6)
# ax2.plot(x, profit_var_alt_m, color="cyan", linestyle="--", label="Profit (%)", linewidth=2, alpha=0.6)
# ax2.plot(x, sum_fee_alt_m, color="green", linestyle="--", label="Fee (%)", linewidth=2, alpha=0.6)
# ax2.tick_params(axis="y", labelcolor="grey")
# --- Общие настройки ---
plt.grid(True, linestyle="--", alpha=0.5)
plt.xticks(x, [])  # скрыть метки по оси X
fig.tight_layout()
# Легенду можно объединить (чтобы обе оси показывались в одном месте)
lines_1, labels_1 = ax1.get_legend_handles_labels()
# lines_2, labels_2 = ax2.get_legend_handles_labels()
# ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", ncol=2)
plt.savefig('pictures/window_lines.png', dpi=200)
plt.close()





