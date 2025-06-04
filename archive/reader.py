import sqlite3
import matplotlib.pyplot as plt

# Подключение к базе данных
db_name = 'prices.db'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
# Чтение данных из таблицы
cursor.execute('''SELECT * 
    FROM data_log 
    ORDER BY id 
    ''')
rows = cursor.fetchall()



# #   Trands
# timestamps = [row[1] for row in rows]
# values1 = [row[2] for row in rows]
# values2 = [row[3] for row in rows]
# values3 = [row[4] for row in rows]
# values4 = [row[5] for row in rows]
# values5 = [row[6] for row in rows]
# plt.figure(figsize=(40, 15))
# plt.plot(timestamps, values1, color='b')
# plt.plot(timestamps, values2, color='r')
# plt.plot(timestamps, values3, color='r')
# plt.plot(timestamps, values4, color='g')
# plt.plot(timestamps, values5, color='g')
# plt.gca().xaxis.set_visible(False)
# plt.savefig('graph.png')


init_dex_eth = 0
init_dex_usd = 3600
init_cex_eth = 1
init_cex_usd = 0

cur_dex_eth = init_dex_eth
cur_dex_usd = init_dex_usd
cur_cex_eth = init_cex_eth
cur_cex_usd = init_cex_usd

direction = -1

# best 1 .. 2.5
level_take = 1.5
text = ''

for row in rows:
    if row[7] > 1 or row[8] > 1 or row[9] > 1 or row[10] > 1 or row[11] > 1:
        print(row[1], '\t', row[7], '\t', row[8], '\t', row[9], '\t', row[10], '\t', row[11], '\t', row[7]+row[8]+row[9]+row[10]+row[11])
print()
print()
print(rows[0][1], '     Balances in DEX - ETH:', cur_dex_eth, ' USD:', cur_dex_usd, '     Balances in CEX - ETH:', cur_cex_eth, ' USD:', cur_cex_usd)
print('\n')

for row in rows:
    # Cross
    cex_price = row[2]
    dex_buy_price_005 = row[5]
    dex_sell_price_005 = row[6]
    dex_buy_price_03 = row[3]
    dex_sell_price_03 = row[4]
    profit_buy_005 = cex_price - dex_buy_price_005
    profit_buy_03 = cex_price - dex_buy_price_03
    profit_sell_005 = dex_sell_price_005 - cex_price
    profit_sell_03 = dex_sell_price_03 - cex_price
    
    if profit_buy_005 > level_take and direction == -1:
        direction = 1
        dex_price = dex_buy_price_005
        if cur_cex_eth * cex_price <= cur_dex_usd:
            mem_usd = cur_cex_eth * cex_price
            cur_cex_usd += mem_usd
            cur_cex_eth = 0 
            cur_dex_eth += mem_usd / dex_buy_price_005
            cur_dex_usd -= mem_usd
            print('0.05% pool buy          ', mem_usd, 'usd  >>> ', mem_usd / dex_buy_price_005, 'eth.     Price:', dex_buy_price_005)
            print('CEX sell                ', mem_usd / cex_price, 'eth  >>> ', mem_usd, 'usd.     Price:', cex_price)
            print('Profit ETH              ', mem_usd / dex_buy_price_005 - mem_usd / cex_price)
        else:
            mem_eth = cur_dex_usd / dex_buy_price_005
            cur_dex_eth += mem_eth
            cur_dex_usd = 0
            cur_cex_usd += mem_eth * cex_price
            cur_cex_eth -= mem_eth
            print('0.05% pool buy          ', mem_eth * dex_buy_price_005, 'usd  >>> ', mem_eth, 'eth.     Price:', dex_buy_price_005)
            print('CEX sell                ', mem_eth, 'eth  >>> ', mem_eth * cex_price, 'usd.     Price:', cex_price)
            print('Profit USD              ', mem_eth * cex_price - mem_eth * dex_sell_price_005)

    elif profit_buy_03 > level_take and direction == -1:
        direction = 1
        dex_price = dex_buy_price_03
        if cur_cex_eth * cex_price <= cur_dex_usd:
            mem_usd = cur_cex_eth * cex_price
            cur_cex_usd += mem_usd
            cur_cex_eth = 0 
            cur_dex_eth += mem_usd / dex_buy_price_03
            cur_dex_usd -= mem_usd
            print('0.3% pool buy           ', mem_usd, 'usd  >>> ', mem_usd / dex_buy_price_03, 'eth.     Price:', dex_buy_price_03)
            print('CEX sell                ', mem_usd / cex_price, 'eth  >>> ', mem_usd, 'usd.     Price:', cex_price)
            print('Profit ETH              ', mem_usd / dex_buy_price_03 - mem_usd / cex_price)
        else:
            mem_eth = cur_dex_usd / dex_buy_price_03
            cur_dex_eth += mem_eth
            cur_dex_usd = 0
            cur_cex_usd += mem_eth * cex_price
            cur_cex_eth -= mem_eth
            print('0.3% pool buy           ', mem_eth * dex_buy_price_03, 'usd  >>> ', mem_eth, 'eth.     Price:', dex_buy_price_03)
            print('CEX sell                ', mem_eth, 'eth  >>> ', mem_eth * cex_price, 'usd.     Price:', cex_price)
            print('Profit USD              ', mem_eth * cex_price - mem_eth * dex_buy_price_03)

    elif profit_sell_005 > level_take and direction == 1:
        direction = -1
        if cur_dex_eth * dex_sell_price_005 <= cur_cex_usd:
            mem_usd = cur_dex_eth * dex_sell_price_005
            cur_dex_usd += mem_usd
            cur_dex_eth = 0
            cur_cex_eth += mem_usd / cex_price
            cur_cex_usd -= mem_usd
            print('0.05% pool sell         ', mem_usd / dex_sell_price_005, 'eth  >>> ', mem_usd, 'usd.     Price:', dex_sell_price_005)
            print('CEX buy                 ', mem_usd, 'usd  >>> ', mem_usd / cex_price, 'eth.     Price:', cex_price)
            print('Profit ETH              ', mem_usd / cex_price - mem_usd / dex_sell_price_005)
        else:
            mem_eth = cur_cex_usd / cex_price
            cur_cex_eth += mem_eth
            cur_cex_usd = 0
            cur_dex_usd += mem_eth * dex_sell_price_005
            cur_dex_eth -= mem_eth
            print('0.05% pool sell         ', mem_eth, 'eth  >>> ', mem_eth * dex_sell_price_005, 'usd.     Price:', dex_sell_price_005)
            print('CEX buy                 ', mem_eth * cex_price, 'usd  >>> ', mem_eth, 'eth.     Price:', cex_price)
            print('Profit USD              ', mem_eth * dex_sell_price_005 - mem_eth * cex_price)

    elif profit_sell_03 > level_take and direction == 1:
        direction = -1
        if cur_dex_eth * dex_sell_price_03 <= cur_cex_usd:
            mem_usd = cur_dex_eth * dex_sell_price_03
            cur_dex_usd += mem_usd
            cur_dex_eth = 0
            cur_cex_eth += mem_usd / cex_price
            cur_cex_usd -= mem_usd
            print('0.3% pool sell          ', mem_usd / dex_sell_price_03, 'eth  >>> ', mem_usd, 'usd.     Price:', dex_sell_price_03)
            print('CEX buy                 ', mem_usd, 'usd  >>> ', mem_usd / cex_price, 'eth.     Price:', cex_price)
            print('Profit ETH              ', mem_usd / cex_price - mem_usd / dex_sell_price_03)
        else:
            mem_eth = cur_cex_usd / cex_price
            cur_cex_eth += mem_eth
            cur_cex_usd = 0
            cur_dex_usd += mem_eth * dex_sell_price_03
            cur_dex_eth -= mem_eth
            dex_volume = cur_dex_eth
            print('0.3% pool sell          ', mem_eth, 'eth  >>> ', mem_eth * dex_sell_price_03, 'usd.     Price:', dex_sell_price_03)
            print('CEX buy                 ', mem_eth * cex_price, 'usd  >>> ', mem_eth, 'eth.     Price:', cex_price)
            print('Profit USD              ', mem_eth * dex_sell_price_03 - mem_eth * cex_price)
    else:
        continue
    
    print('-------------------------------------------------------------------------------------------------------------------------------------------------------')
    print(row[1], '     Balances in DEX - ETH:', cur_dex_eth, ' USD:', cur_dex_usd, '     Balances in CEX - ETH:', cur_cex_eth, ' USD:', cur_cex_usd)
    print()
    print()
    print()

init_eth_sum = init_cex_eth + init_dex_eth
init_usd_sum = init_cex_usd + init_dex_usd
cur_eth_sum = cur_cex_eth + cur_dex_eth
cur_usd_sum = cur_cex_usd + cur_dex_usd
change_eth = (cur_eth_sum - init_eth_sum) / init_eth_sum * 100
change_usd = (cur_usd_sum - init_usd_sum) / init_usd_sum * 100

print()
print('Start values: ', init_eth_sum, 'eth.', init_usd_sum, 'usd.')
print('Finish values: ', cur_eth_sum, 'eth.', cur_usd_sum, 'usd.')
print('Changed: ', change_eth, '% eth.', change_usd, '% usd.')
print('APR:', (change_eth + change_usd) / 2 * 3 * 365, '%')

conn.close()