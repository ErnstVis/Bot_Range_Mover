from solana.rpc.api import Client
client = Client("https://api.devnet.solana.com")
print(client.is_connected())

