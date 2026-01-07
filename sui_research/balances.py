from pysui import SuiConfig, SyncClient
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_types import SuiAddress, ObjectID
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import inspect

from pysui.sui.sui_builders.get_builders import GetAllCoins, GetCoinTypeBalance



'''
# Подключение к сети
rpc_url = "https://fullnode.mainnet.sui.io:443"
cfg = SuiConfig.user_config(rpc_url=rpc_url)
client = SyncClient(cfg)

print("Client ready")

YOUR_ADDRESS = "0x63e207c8adbd8c33fd74bade16184f93cadebdb875646bddd2f482bcd72e188f"

# Вариант 1: Использование get_gas (работает, но deprecated)
print("Option 1: Using get_gas (deprecated)")
result = client.get_gas(YOUR_ADDRESS)
if result.is_ok():
    coins_data = result.result_data
    if coins_data.data:
        balance_mist = int(coins_data.data[0].balance)
        balance_sui = balance_mist / 1_000_000_000
        print(f"Balance from get_gas: {balance_sui} SUI")
        print(f"Coin object ID: {coins_data.data[0].coin_object_id}")

# Вариант 2: Использование GetAllCoins через execute (более современный способ)
print("\nOption 2: Using GetAllCoins through execute")
try:
    coins_query = GetAllCoins(owner=YOUR_ADDRESS, limit=100)
    result = client.execute(coins_query)
    if result.is_ok():
        coins_data = result.result_data
        total_balance = 0
        for coin in coins_data.data:
            total_balance += int(coin.balance)
            print(f"  Coin: {coin.coin_object_id} - Balance: {int(coin.balance)/1_000_000_000:.6f} SUI")
        total_sui = total_balance / 1_000_000_000
        print(f"Total balance from GetAllCoins: {total_sui} SUI")
except Exception as e:
    print(f"Error with GetAllCoins: {e}")

# Вариант 3: Использование GetCoinTypeBalance (получить общий баланс для типа монеты)
print("\nOption 3: Using GetCoinTypeBalance for total SUI balance")
try:
    balance_query = GetCoinTypeBalance(
        owner=YOUR_ADDRESS,
        coin_type="0x2::sui::SUI"
    )
    result = client.execute(balance_query)
    if result.is_ok():
        balance_data = result.result_data
        if hasattr(balance_data, 'total_balance'):
            total_sui = int(balance_data.total_balance) / 1_000_000_000
            print(f"Total SUI balance from GetCoinTypeBalance: {total_sui} SUI")
except Exception as e:
    print(f"Error with GetCoinTypeBalance: {e}")

# Дополнительно: Получить информацию об объекте (первой монете)
print("\nGetting first coin object details...")
if 'coins_data' in locals() and coins_data.data:
    first_coin_id = coins_data.data[0].coin_object_id
    from pysui.sui.sui_builders.get_builders import GetObject
    obj_query = GetObject(object_id=first_coin_id)
    obj_result = client.execute(obj_query)
    if obj_result.is_ok():
        obj_data = obj_result.result_data
        print(f"Object type: {obj_data.object_type}")
        print(f"Object owner: {obj_data.owner}")
'''




rpc_url = "https://fullnode.mainnet.sui.io:443"
cfg = SuiConfig.user_config(rpc_url=rpc_url)
client = SyncClient(cfg)

YOUR_ADDRESS = "0x63e207c8adbd8c33fd74bade16184f93cadebdb875646bddd2f482bcd72e188f"

print("Getting first 20 coins to see their types...")

try:
    coins_query = GetAllCoins(owner=YOUR_ADDRESS, limit=20)
    result = client.execute(coins_query)
    
    if result.is_ok():
        coins_data = result.result_data
        
        print(f"Found {len(coins_data.data)} coins total:")
        print("-" * 80)
        
        # Создадим словарь для группировки по типам
        type_counts = {}
        
        for i, coin in enumerate(coins_data.data):
            coin_type = coin.coin_type
            balance = int(coin.balance)
            
            # Считаем типы
            if coin_type in type_counts:
                type_counts[coin_type] += 1
            else:
                type_counts[coin_type] = 1
            
            # Выводим информацию о первых 10 монетах
            if i < 10:
                print(f"Coin {i+1}:")
                print(f"  Type: {coin_type}")
                print(f"  ID: {coin.coin_object_id}")
                print(f"  Balance: {balance}")
                if "ika" in coin_type.lower():
                    print("  *** CONTAINS 'ika' IN TYPE! ***")
                print()
        
        print("-" * 80)
        print("\nCoin type summary:")
        for coin_type, count in type_counts.items():
            # Проверяем, содержит ли тип "ika" (без учета регистра)
            if "ika" in coin_type.lower():
                print(f"  FOUND IKA TYPE! {count}x: {coin_type}")
            else:
                print(f"  {count}x: {coin_type[:50]}...")
        
        # Теперь попробуем найти IKA по частичному совпадению
        print("\nSearching for coins containing 'ika' in type...")
        ika_coins = []
        for coin in coins_data.data:
            if "ika" in coin.coin_type.lower() and int(coin.balance) > 0:
                ika_coins.append(coin)
        
        if ika_coins:
            print(f"\nFound {len(ika_coins)} IKA coins!")
            total_ika = 0
            for coin in ika_coins:
                balance = int(coin.balance)
                total_ika += balance
                print(f"  ID: {coin.coin_object_id}")
                print(f"  Type: {coin.coin_type}")
                print(f"  Balance: {balance} IKA")
                print()
            
            print(f"Total IKA balance: {total_ika}")
        else:
            print("No coins with 'ika' in type found.")
            
except Exception as e:
    print(f"Error: {e}")