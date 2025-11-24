# from solana.rpc.api import Client
# client = Client("https://api.devnet.solana.com")
# print(client.is_connected())



from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients import sync_client


def main():
    # создаём конфиг с RPC
    cfg = SuiConfig(rpc_url="https://fullnode.testnet.sui.io")

    # создаём клиент
    client = sync_client(cfg)

    # проверяем подключение
    latest = client.get_latest_checkpoint_sequence_number()
    print("Latest checkpoint:", latest.result_data)


if __name__ == "__main__":
    main()

