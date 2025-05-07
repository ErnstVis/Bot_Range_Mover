import random
import matplotlib.pyplot as plt

# Параметры симуляции
start_price = 2000.0
iterations = 10000
price = start_price
prices = [price]

mu = 0         # 0.001 означает +0.1% средний рост на шаг
sigma = 0.005  # 0.005 означает 0.5% стандартное отклонение, которое реализуется в 68% случаев

# Симуляция движения
for _ in range(iterations):
    change_percent = random.gauss(mu, sigma)  # Нормальное распределение
    price *= (1 + change_percent)
    prices.append(price)

# Визуализация
plt.figure(figsize=(12, 6))
plt.plot(prices, label="Симулированная цена")
plt.title("Эмуляция движения цены на основе случайных изменений на ±1%")
plt.xlabel("Итерации")
plt.ylabel("Цена")
plt.grid(True)
plt.legend()
plt.savefig('pictures/price_sim_' + str(random.randint(1000, 9999)) + '.png')
