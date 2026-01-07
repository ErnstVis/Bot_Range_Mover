from pysui import SuiConfig, SyncClient
from pysui.sui.sui_types import SuiAddress, ObjectID
from pysui.sui.sui_builders.get_builders import GetAllCoins, GetObject
from pysui.sui.sui_builders.exec_builders import PayAllSui, PaySui, TransferObject
import json
from typing import Dict, List, Optional

class SuiWallet:
    """Класс для работы с кошельком Sui"""
    
    def __init__(self, mnemonic: str = None, config_file: str = None, network: str = "testnet"):
        """
        Инициализация кошелька
        
        Args:
            mnemonic: Мнемоническая фраза (если None - создается новый)
            config_file: Файл конфигурации
            network: Сеть (testnet, mainnet, devnet)
        """
        if config_file:
            # Загрузка из файла
            with open(config_file, 'r') as f:
                cfg_dict = json.load(f)
            self.cfg = SuiConfig.deserialize(cfg_dict)
        elif mnemonic:
            # Создание из мнемонической фразы
            # В новой версии может отличаться
            self.cfg = SuiConfig.user_config(rpc_url=self._get_rpc_url(network))
            # Здесь нужно добавить импорт приватного ключа из мнемоники
            # Пока используем упрощенный вариант
        else:
            # Новый кошелек
            self.cfg = SuiConfig.user_config(rpc_url=self._get_rpc_url(network))
        
        self.client = SyncClient(self.cfg)
        self.address = str(self.cfg.active_address) if hasattr(self.cfg, 'active_address') else None
        
        print(f"Wallet initialized: {self.address}")
        print(f"Network: {network}")
    
    def _get_rpc_url(self, network: str) -> str:
        """Получить RPC URL для сети"""
        urls = {
            "mainnet": "https://fullnode.mainnet.sui.io:443",
            "testnet": "https://fullnode.testnet.sui.io:443",
            "devnet": "https://fullnode.devnet.sui.io:443"
        }
        return urls.get(network, urls["testnet"])
    
    def get_all_coins(self, coin_type: str = None, limit: int = 50) -> Dict:
        """
        Получить все монеты адреса
        
        Args:
            coin_type: Тип монеты (например, "0x2::sui::SUI")
            limit: Максимальное количество
        
        Returns:
            Словарь с монетами сгруппированными по типам
        """
        try:
            coins_query = GetAllCoins(
                owner=SuiAddress(self.address),
                cursor=None,
                limit=limit
            )
            
            result = self.client.execute(coins_query)
            
            if not result.is_ok():
                print(f"Error getting coins: {result.result_string}")
                return {}
            
            coins_data = result.result_data
            coins_by_type = {}
            
            for coin in coins_data.data:
                balance = int(coin.balance)
                if balance <= 0:
                    continue
                    
                coin_type_full = coin.coin_type
                
                if coin_type and coin_type not in coin_type_full:
                    continue
                
                if coin_type_full not in coins_by_type:
                    coins_by_type[coin_type_full] = {
                        'total_balance': 0,
                        'coins': [],
                        'coin_type': coin_type_full
                    }
                
                coin_info = {
                    'id': str(coin.coin_object_id),
                    'balance': balance,
                    'version': coin.version,
                    'digest': coin.digest
                }
                
                coins_by_type[coin_type_full]['coins'].append(coin_info)
                coins_by_type[coin_type_full]['total_balance'] += balance
            
            return coins_by_type
            
        except Exception as e:
            print(f"Exception in get_all_coins: {e}")
            return {}
    
    def get_balance_summary(self) -> Dict:
        """Получить сводку по балансам всех токенов"""
        all_coins = self.get_all_coins(limit=100)
        
        summary = {}
        for coin_type, data in all_coins.items():
            # Определяем decimals и символ
            decimals = self._get_decimals_for_coin(coin_type)
            symbol = self._get_symbol_for_coin(coin_type)
            
            raw_balance = data['total_balance']
            formatted_balance = raw_balance / (10 ** decimals) if decimals > 0 else raw_balance
            
            summary[coin_type] = {
                'raw_balance': raw_balance,
                'formatted_balance': formatted_balance,
                'decimals': decimals,
                'symbol': symbol,
                'coin_count': len(data['coins'])
            }
        
        return summary
    
    def _get_decimals_for_coin(self, coin_type: str) -> int:
        """Определить количество десятичных знаков для токена"""
        # Для SUI - 9 decimals
        if "0x2::sui::SUI" in coin_type:
            return 9
        
        # Для IKA - предположительно 9 (как в вашем случае)
        if "ika::IKA" in coin_type:
            return 9
        
        # Для других токенов - нужно получать метаданные
        # Пока используем 0 как значение по умолчанию
        return 0
    
    def _get_symbol_for_coin(self, coin_type: str) -> str:
        """Получить символ токена"""
        if "0x2::sui::SUI" in coin_type:
            return "SUI"
        elif "ika::IKA" in coin_type:
            return "IKA"
        elif "::" in coin_type:
            # Извлекаем символ из типа
            parts = coin_type.split("::")
            return parts[-1] if len(parts) > 2 else "UNKNOWN"
        return "UNKNOWN"
    
    def merge_coins(self, coin_type: str = None) -> bool:
        """
        Объединить монеты одного типа
        
        Args:
            coin_type: Тип монеты для объединения
            
        Returns:
            True если успешно
        """
        try:
            # Получаем все монеты указанного типа
            coins_by_type = self.get_all_coins(coin_type=coin_type, limit=100)
            
            if not coins_by_type:
                print(f"No coins found for type: {coin_type}")
                return False
            
            # Находим тип монеты (первый ключ в словаре)
            target_coin_type = list(coins_by_type.keys())[0]
            coins_data = coins_by_type[target_coin_type]
            
            if len(coins_data['coins']) <= 1:
                print(f"Only {len(coins_data['coins'])} coin(s), nothing to merge")
                return True
            
            print(f"Merging {len(coins_data['coins'])} coins of type: {target_coin_type}")
            print(f"Total balance: {coins_data['total_balance']}")
            
            # Собираем ID всех монет
            coin_ids = [ObjectID(coin['id']) for coin in coins_data['coins']]
            
            # Для SUI используем PayAllSui
            if "0x2::sui::SUI" in target_coin_type:
                # Выбираем первую монету как primary
                primary_coin = coin_ids[0]
                merge_coins = coin_ids[1:]
                
                # Создаем транзакцию объединения
                tx_builder = PayAllSui(
                    signer=SuiAddress(self.address),
                    input_coins=merge_coins,
                    recipient=SuiAddress(self.address),
                    gas_budget=10000000
                )
                
                result = self.client.execute(tx_builder)
                
            else:
                # Для других токенов нужна более сложная логика через MoveCall
                print(f"Merging non-SUI tokens requires MoveCall, not implemented yet")
                return False
            
            if result.is_ok():
                print(f"Merge successful! Digest: {result.result_data.digest}")
                return True
            else:
                print(f"Merge failed: {result.result_string}")
                return False
                
        except Exception as e:
            print(f"Exception in merge_coins: {e}")
            return False
    
    def transfer_sui(self, recipient: str, amount_sui: float, gas_budget: int = 10000000) -> bool:
        """
        Перевести SUI другому адресу
        
        Args:
            recipient: Адрес получателя
            amount_sui: Количество SUI
            gas_budget: Бюджет на газ в MIST
            
        Returns:
            True если успешно
        """
        try:
            # Конвертируем в MIST
            amount_mist = int(amount_sui * 1_000_000_000)
            
            # Получаем монеты отправителя
            coins_by_type = self.get_all_coins(coin_type="0x2::sui::SUI", limit=10)
            
            if not coins_by_type:
                print("No SUI coins found")
                return False
            
            coins_data = list(coins_by_type.values())[0]
            if len(coins_data['coins']) == 0:
                print("No SUI coins with balance")
                return False
            
            # Выбираем первую монету
            coin_id = ObjectID(coins_data['coins'][0]['id'])
            
            # Создаем транзакцию
            tx_builder = PaySui(
                signer=SuiAddress(self.address),
                input_coins=[coin_id],
                recipients=[SuiAddress(recipient)],
                amounts=[amount_mist],
                gas_budget=gas_budget
            )
            
            result = self.client.execute(tx_builder)
            
            if result.is_ok():
                print(f"Transfer successful! Digest: {result.result_data.digest}")
                return True
            else:
                print(f"Transfer failed: {result.result_string}")
                return False
                
        except Exception as e:
            print(f"Exception in transfer_sui: {e}")
            return False
    
    def save_config(self, filename: str = "sui_wallet.json"):
        """Сохранить конфигурацию кошелька в файл"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.cfg.serialize(), f, indent=2)
            print(f"Wallet saved to {filename}")
        except Exception as e:
            print(f"Error saving wallet: {e}")


        
    

# Создаем экземпляр кошелька
# Вариант 1: Подключиться к mainnet для чтения
wallet = SuiWallet(network="mainnet")

# Вариант 2: Для тестов на testnet с новым кошельком
# wallet = SuiWallet()

print(f"Wallet address: {wallet.address}")

# Получаем сводку по балансам
print("\nGetting balance summary...")
summary = wallet.get_balance_summary()

for coin_type, data in summary.items():
    symbol = data['symbol']
    balance = data['formatted_balance']
    count = data['coin_count']
    print(f"{symbol}: {balance:.6f} ({count} coins)")

# Пример объединения монет SUI
# print("\nMerging SUI coins...")
# wallet.merge_coins("0x2::sui::SUI")

# Пример перевода (ЗАКОММЕНТИРОВАНО для безопасности)
# recipient = "0xANOTHER_ADDRESS"
# wallet.transfer_sui(recipient, 0.01)  # 0.01 SUI