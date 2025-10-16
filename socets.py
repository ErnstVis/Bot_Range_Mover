import asyncio
from web3 import AsyncWeb3
from web3.providers.persistent import (
    AsyncIPCProvider,
    WebSocketProvider,
)

# твой сокетный эндпоинт Infura (не https, а wss)
RPC = "wss://arbitrum-mainnet.infura.io/ws/v3/ba14886447744dbcb8b619b34beca025"


async def main():
    async with AsyncWeb3(WebSocketProvider(RPC)) as w3:
        # подписка
        print("Connected:", await w3.is_connected())
        subscription_id = await w3.eth.subscribe("newHeads")
        print("Sub. active:", subscription_id)

        async for response in w3.socket.process_subscriptions():
            block = response.get("result")
            if block:
                block_number = int(block["number"])
                timestamp = block["timestamp"]
                miner = block["miner"]
                tx_count = len(block.get("transactions", []))  # иногда в заголовке могут быть tx

                print(f"\nNew block: {block_number}")
                print(f"\nTime: {timestamp}")
                print(f"\nMiner: {miner}")
                print(f"\nGas Limit: {block['gasLimit']}, GasUsed: {block['gasUsed']}")
                print(f"\nBase Fee: {block.get('baseFeePerGas')}")
                print("-" * 40)

asyncio.run(main())