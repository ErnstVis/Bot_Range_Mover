import sqlite3
import matplotlib.pyplot as plt


db_name = 'prices_cex.db'
# db_name = 'prices.db'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute('''SELECT * 
    FROM data_log 
    ORDER BY id 
    ''')
rows = cursor.fetchall()

# ======================================================================================================

# # #   Trands
# timestamps = [row[1] for row in rows]
# values1 = [row[2] for row in rows]
# values4 = [row[5] for row in rows]
# values5 = [row[6] for row in rows]
# values7 = [row[13] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='blue')
# plt.plot(timestamps, values4, color='g')
# plt.plot(timestamps, values5, color='g')
# plt.plot(timestamps, values7, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('graph_005.png')

# ======================================================================================================

# #   Trands CEX
timestamps = [row[1] for row in rows]
values1 = [row[2] for row in rows]
values2 = [row[3] for row in rows]
values3 = [row[4] for row in rows]
values4 = [row[5] for row in rows]
values5 = [row[6] for row in rows]
values6 = [row[7] for row in rows]
plt.figure(figsize=(40, 15))
plt.plot(timestamps, values1, color='r')
plt.plot(timestamps, values2, color='r')
plt.plot(timestamps, values3, color='r')
plt.plot(timestamps, values4, color='b')
plt.plot(timestamps, values5, color='b')
plt.plot(timestamps, values6, color='b')
plt.gca().xaxis.set_visible(False)
plt.savefig('cex_prices.png')

# ======================================================================================================

# timestamps = [row[1] for row in rows]
# values1 = [row[2] for row in rows]
# values2 = [row[3] for row in rows]
# values3 = [row[4] for row in rows]
# values6 = [row[12] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='blue')
# plt.plot(timestamps, values2, color='r')
# plt.plot(timestamps, values3, color='r')
# plt.plot(timestamps, values6, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('graph_03.png')

# ======================================================================================================

# timestamps = [row[1] for row in rows]
# values1 = [row[2] for row in rows]
# values2 = [row[3] for row in rows]
# values3 = [row[4] for row in rows]
# values4 = [row[5] for row in rows]
# values5 = [row[6] for row in rows]
# values6 = [row[12] for row in rows]
# values7 = [row[13] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='blue')
# plt.plot(timestamps, values2, color='r')
# plt.plot(timestamps, values3, color='r')
# plt.plot(timestamps, values4, color='g')
# plt.plot(timestamps, values5, color='g')
# plt.plot(timestamps, values6, color='black')
# plt.plot(timestamps, values7, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('graph_com.png')

# ======================================================================================================

# timestamps = [row[1] for row in rows]

# values1 = [row[8] for row in rows]
# values2 = [row[9] for row in rows]
# values3 = [row[10] for row in rows]

# fig, ax1 = plt.subplots(figsize=(40, 15))
# ax2 = ax1.twinx()
# ax3 = ax1.twinx()

# ax1.plot(timestamps, values1, color='black')
# ax2.plot(timestamps, values2, color='blue')
# ax3.plot(timestamps, values3, color='green')

# plt.savefig('tick.png')

# ======================================================================================================

# #timestamps = [row[1] for row in rows]
# values1 = [row[8] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('tok0.png')

# #timestamps = [row[1] for row in rows]
# values1 = [row[9] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('tok1.png')

# #timestamps = [row[1] for row in rows]
# values1 = [row[10] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('liqC.png')

# #timestamps = [row[1] for row in rows]
# values1 = [row[11] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='black')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('liqT.png')

# ======================================================================================================

conn.close()