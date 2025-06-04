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


init_dex_eth = 0
init_dex_usd = 4000
init_cex_eth = 1
init_cex_usd = 0

cur_dex_eth = init_dex_eth
cur_dex_usd = init_dex_usd
cur_cex_eth = init_cex_eth
cur_cex_usd = init_cex_usd

direction = -1

# best 1 .. 2.5
level_take = 2.5
level_lim = 500

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

    
    if level_lim > profit_buy_005 > level_take  and direction == -1:
        direction = 1
        dex_price = dex_buy_price_005
        if cur_cex_eth * cex_price < cur_dex_usd:
            teo_cex_usd = cur_cex_eth * cex_price
        else:
            teo_cex_usd = cur_dex_usd
        cur_cex_usd += teo_cex_usd
        cur_cex_eth -= teo_cex_usd / cex_price
        cur_dex_eth += teo_cex_usd / dex_price
        cur_dex_usd -= teo_cex_usd
        print('0.05% pool buy          ', teo_cex_usd, 'usd  >>> ', teo_cex_usd / dex_price, 'eth.     Price:', dex_price)
        print('CEX sell                ', teo_cex_usd / cex_price, 'eth  >>> ', teo_cex_usd, 'usd.     Price:', cex_price)
        print('Profit ETH              ', teo_cex_usd / dex_price - teo_cex_usd / cex_price)

    elif level_lim > profit_buy_03 > level_take and direction == -1:
        direction = 1
        dex_price = dex_buy_price_03
        if cur_cex_eth * cex_price < cur_dex_usd:
            teo_cex_usd = cur_cex_eth * cex_price
        else:
            teo_cex_usd = cur_dex_usd
        cur_cex_usd += teo_cex_usd
        cur_cex_eth -= teo_cex_usd / cex_price
        cur_dex_eth += teo_cex_usd / dex_price
        cur_dex_usd -= teo_cex_usd
        print('0.3% pool buy           ', teo_cex_usd, 'usd  >>> ', teo_cex_usd / dex_price, 'eth.     Price:', dex_price)
        print('CEX sell                ', teo_cex_usd / cex_price, 'eth  >>> ', teo_cex_usd, 'usd.     Price:', cex_price)
        print('Profit ETH              ', teo_cex_usd / dex_price - teo_cex_usd / cex_price)

    elif level_lim > profit_sell_005 > level_take and direction == 1:
        direction = -1
        dex_price = dex_sell_price_005
        if cur_cex_usd / cex_price <= cur_dex_eth:
            teo_cex_eth = cur_cex_usd / cex_price
        else:
            teo_cex_eth = cur_dex_eth
        cur_cex_usd -= teo_cex_eth * cex_price
        cur_cex_eth += teo_cex_eth
        cur_dex_eth -= teo_cex_eth
        cur_dex_usd += teo_cex_eth * dex_price
        print('0.05% pool sell         ', teo_cex_eth, 'eth  >>> ', teo_cex_eth * dex_price, 'usd.     Price:', dex_price)
        print('CEX buy                 ', teo_cex_eth * cex_price, 'usd  >>> ', teo_cex_eth, 'eth.     Price:', cex_price)
        print('Profit USD              ', teo_cex_eth * dex_price - teo_cex_eth * cex_price)

    elif level_lim > profit_sell_03 > level_take and direction == 1:
        direction = -1
        dex_price = dex_sell_price_03
        if cur_cex_usd / cex_price <= cur_dex_eth:
            teo_cex_eth = cur_cex_usd / cex_price
        else:
            teo_cex_eth = cur_dex_eth
        cur_cex_usd -= teo_cex_eth * cex_price
        cur_cex_eth += teo_cex_eth
        cur_dex_eth -= teo_cex_eth
        cur_dex_usd += teo_cex_eth * dex_price
        print('0.3% pool sell          ', teo_cex_eth, 'eth  >>> ', teo_cex_eth * dex_price, 'usd.     Price:', dex_price)
        print('CEX buy                 ', teo_cex_eth * cex_price, 'usd  >>> ', teo_cex_eth, 'eth.     Price:', cex_price)
        print('Profit USD              ', teo_cex_eth * dex_price - teo_cex_eth * cex_price)

    else:
        continue
    
    print('-------------------------------------------------------------------------------------------------------------------------------------------------------')
    print(row[1], '     Balances in DEX - ETH:', cur_dex_eth, ' USD:', cur_dex_usd, '     Balances in CEX - ETH:', cur_cex_eth, ' USD:', cur_cex_usd)
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