from web3 import Web3
import json
import os

def load_abi(file_name):
    with open(os.path.join("abi", file_name), "r") as abi_file:
        return json.load(abi_file)
    
def init_chain(rpc):
    connection = Web3(Web3.HTTPProvider(rpc))
    if connection.is_connected():
        print("Connected!")
        return connection
    else:
        print("Not connected!")
        exit()

def get_balance_native(connection, address):
    balance_native = connection.eth.get_balance(address)
    balance_in_eth = connection.from_wei(balance_native, 'ether')
    # print(f"Balance native: {balance_in_eth}")
    return balance_in_eth

def get_balance_token(token, address):
    balance = token.functions.balanceOf(address).call()
    decimals = token.functions.decimals().call()
    balance_token = balance / 10**decimals
    #print(f"Balance: {balance_token}")
    return balance_token

def send_native(amount, connection, address_from, address_to, private_key):
    amount_in_wei = connection.to_wei(amount, "ether")
    nonce = connection.eth.get_transaction_count(address_from)
    gas_price = connection.eth.gas_price
    print(f"Recomended gas price: {connection.from_wei(gas_price, 'gwei')} Gwei")
    gas_price = int(gas_price * 1.1)
    if gas_price > 1000000000000:
        print('Gas price very high')
        exit()
    transaction = {
        "to": address_to,
        "value": amount_in_wei,
        "gas": 21000,
        "gasPrice": gas_price,
        "nonce": nonce,
        "chainId": 137,}
    signed_transaction = connection.eth.account.sign_transaction(transaction, private_key)
    tx_hash = connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
    print(f"Transaction sent! Hash: {connection.to_hex(tx_hash)}")
    return tx_hash


def send_token(amount, connection, token, address_from, address_to, private_key):
    decimals = token.functions.decimals().call()
    amount_scaled = int(amount * 10**decimals)
    nonce = connection.eth.get_transaction_count(address_from)
    gas_price = connection.eth.gas_price
    print(f"Recomended gas price: {connection.from_wei(gas_price, 'gwei')} Gwei")
    gas_price = int(gas_price * 1.1)
    if gas_price > 1000000000000:
        print('Gas price very high')
        exit()
    transaction = token.functions.transfer(address_to, amount_scaled).build_transaction({
        "chainId": 137,
        "gas": 210000,
        "gasPrice": gas_price,
        "nonce": nonce,})
    signed_transaction = connection.eth.account.sign_transaction(transaction, private_key)
    tx_hash = connection.eth.send_raw_transaction(signed_transaction.raw_transaction)
    print(f"Transaction sent! Hash: {connection.to_hex(tx_hash)}")
    return tx_hash


def approve_token(amount, connection, token_cont, wallet, address_from, private_key):
    decimals = token_cont.functions.decimals().call()
    amount_scaled = int(amount * 10**decimals)
    nonce = connection.eth.get_transaction_count(wallet)
    tx = token_cont.functions.approve(
        address_from,
        amount #amount_scaled
    ).build_transaction({
        'chainId': 137,
        'gas': 210000,
        'gasPrice': int(connection.eth.gas_price * 1.1),
        'nonce': nonce
    })
    signed_tx = connection.eth.account.sign_transaction(tx, private_key)
    tx_hash = connection.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Approve sended: {connection.to_hex(tx_hash)}")
    return connection.to_hex(tx_hash)