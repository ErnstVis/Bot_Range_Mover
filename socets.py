import asyncio
import json
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)

# # твой сокетный эндпоинт Infura (не https, а wss)
# RPC = "wss://arbitrum-mainnet.infura.io/ws/v3/ba14886447744dbcb8b619b34beca025"


# async def main():
#     async with AsyncWeb3(WebSocketProvider(RPC)) as w3:
#         # подписка
#         print("Connected:", await w3.is_connected())
#         subscription_id = await w3.eth.subscribe("newHeads")
#         print("Sub. active:", subscription_id)

#         async for response in w3.socket.process_subscriptions():
#             block = response.get("result")
#             if block:
#                 block_number = int(block["number"])
#                 timestamp = block["timestamp"]
#                 miner = block["miner"]
#                 tx_count = len(block.get("transactions", []))  # иногда в заголовке могут быть tx

#                 print(f"\nNew block: {block_number}")
#                 print(f"\nTime: {timestamp}")
#                 print(f"\nMiner: {miner}")
#                 print(f"\nGas Limit: {block['gasLimit']}, GasUsed: {block['gasUsed']}")
#                 print(f"\nBase Fee: {block.get('baseFeePerGas')}")
#                 print("-" * 40)

# asyncio.run(main())



RPC = "wss://arbitrum-mainnet.infura.io/ws/v3/ba14"   # твой WebSocket RPC
POOL_ADDRESS = "0x6f38e884725a116C9C7fBF208e79FE8828a2595F"               # адрес пула Uniswap
POOL_ABI = json.load(open("config/abi/uniswap_pool.json"))



async def main():
    async with AsyncWeb3(WebSocketProvider(RPC)) as w3:
        pool_contract = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)
        swap_event = pool_contract.events.Swap()

        # 💡 Правильный способ вычислить topic для события
        # swap_topic = w3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)").hex()

        # создаём подписку
        params = {
            "address": POOL_ADDRESS,
            # "topics": [swap_topic],  # слушаем только Swap
        }

        sub_id = await w3.eth.subscribe("logs", params)
        print("Subscribed:", sub_id)

        async for response in w3.socket.process_subscriptions():
            log = response.get("result")
            if not log:
                continue

            try:
                event = swap_event.process_log(log)
                print("\n💧 Swap Event")
                print("Sender:", event["args"]["sender"])
                print("Amount0:", event["args"]["amount0"])
                print("Amount1:", event["args"]["amount1"])
                print("Price:", event["args"]["sqrtPriceX96"])
                print("-" * 40)
            except Exception as e:
                # возможно пришло другое событие
                pass

asyncio.run(main())