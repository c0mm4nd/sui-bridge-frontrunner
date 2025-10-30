import json
import os
import time
from datetime import datetime
import requests
from web3 import Web3, Account

NONCE = 0 # [YOUR NONCE HERE]
SUI = "https://mysten-rpc.mainnet.sui.io/"
ETH = "https://eth.llamarpc.com/" # Do not use the RPC which checks revert, as it will cause a delay.

# Initialize Web3 instance
web3 = Web3(Web3.HTTPProvider(ETH))

# Load private key from environment variable
private_key = os.environ.get("PRIVATE_KEY")
if not private_key:
    raise ValueError("PRIVATE_KEY environment variable not set")

# Create wallet account from private key
wallet = Account.from_key(private_key)
print(f"Using wallet address: {wallet.address}")

# Define transaction details
contract_address = "0xda3bD1fE1973470312db04551B65f401Bc8a92fD"
# transferBridgedTokensWithSignatures(bytes[] signatures,tuple message)
FUNC_ABI = {
    "inputs": [
        {"internalType": "bytes[]", "name": "signatures", "type": "bytes[]"},
        {
            "components": [
                {"internalType": "uint8", "name": "messageType", "type": "uint8"},
                {"internalType": "uint8", "name": "version", "type": "uint8"},
                {"internalType": "uint64", "name": "nonce", "type": "uint64"},
                {"internalType": "uint8", "name": "chainID", "type": "uint8"},
                {"internalType": "bytes", "name": "payload", "type": "bytes"},
            ],
            "internalType": "struct BridgeMessage",
            "name": "message",
            "type": "tuple",
        },
    ],
    "name": "transferBridgedTokensWithSignatures",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function",
}
contract = web3.eth.contract(address=contract_address, abi=[FUNC_ABI])


def suix_getDynamicFieldObject_for_bridge_tx(
    bridge_seq_num: int, source_chain: int = 0, message_type: int = 0
):
    return (
        requests.post(
            SUI,
            json={
                "jsonrpc": "2.0",
                "id": 112,
                "method": "suix_getDynamicFieldObject",
                "params": [
                    "0xec526c0819f5d2183bc14cc444ea8777338eaabc9761eb5e6d21aa664ba86d69",
                    {
                        "type": "0x000000000000000000000000000000000000000000000000000000000000000b::message::BridgeMessageKey",
                        "value": {
                            "bridge_seq_num": str(bridge_seq_num),
                            "message_type": message_type,
                            "source_chain": source_chain,
                        },
                    },
                ],
            },
        )
        .json()
        .get("result", {})
        .get("data", {})
    )


def byte_list_to_bytes(byte_list):
    return bytes([int(b) for b in byte_list])


def get_signatures_for_bridge_message(bridge_seq_num: int):
    dynamic_field_object = suix_getDynamicFieldObject_for_bridge_tx(bridge_seq_num)
    values = (
        dynamic_field_object.get("content")
        .get("fields", {})
        .get("value", {})
        .get("fields", {})
        .get("value", {})
        .get("fields", {})
    )
    if values.get("claimed"):
        raise Exception("Bridge message already claimed")

    payload = values.get("message", {}).get("fields", {}).get("payload", [])
    # convert list of chars to bytes
    payload = "0x" + byte_list_to_bytes(payload).hex()
    print(f"Bridge message bytes: {payload}")

    signatures = [
        "0x" + byte_list_to_bytes(sig).hex()
        for sig in values.get("verified_signatures", [])
    ]
    return payload, signatures


# TODO: auto find all your bridge tx, for batch claim
def get_all_tx(address: str, chainId: int = 0):
    return requests.get(
        "https://bridge.sui.io/api/trpc/post.getAllTransactions",
        params={
            "batch": "1",
            "input": json.dumps(
                {
                    "0": {
                        "json": {
                            "sourceAddress": address,
                            "chainId": 0,
                            "limit": 100,
                            "direction": "forward",
                        }
                    }
                }
            ),
        },
    ).json()


# Function to send transaction
def send_transaction(nonce):
    payload, signatures = get_signatures_for_bridge_message(nonce)

    try:
        # signed_tx = wallet.sign_transaction(transaction)
        # tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        result = contract.functions.transferBridgedTokensWithSignatures(
            signatures,
            {
                "messageType": 0,
                "version": 0,
                "nonce": nonce,
                "chainID": 0,
                "payload": payload,
            },
        ).transact(
            {
                "from": wallet.address,
                "gas": 856551,
                "maxFeePerGas": Web3.to_wei("10", "gwei"),
                "maxPriorityFeePerGas": Web3.to_wei("5", "gwei"),
                "nonce": web3.eth.get_transaction_count(wallet.address),
                "chainId": 1,
            }
        )
        tx_hash = web3.to_hex(result)
        print(f"Transaction sent successfully: {tx_hash}")
        # wait for receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction receipt: {receipt}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Function to test transaction, always fail unless there is a remaining limit > your withdraw
def test_transaction(nonce):
    payload, signatures = get_signatures_for_bridge_message(nonce)

    transaction = contract.functions.transferBridgedTokensWithSignatures(
        signatures,
        (
            0,  # messageType
            1,  # version
            nonce,  # nonce
            0,  # chainID
            payload,  # payload
        ),
    ).build_transaction(
        {
            "from": wallet.address,
            "gas": 856551,
            "maxFeePerGas": Web3.to_wei("4", "gwei"),
            "maxPriorityFeePerGas": Web3.to_wei("2.5", "gwei"),
            "nonce": web3.eth.get_transaction_count(wallet.address),
            "chainId": 1,
        }
    )

    try:
        gas_estimate = web3.eth.estimate_gas(transaction)
        print(f"Transaction estimated successfully: {gas_estimate} gas")
    except Exception as e:
        print(f"An error occurred: {e}")

while True:
    latest_block = web3.eth.get_block("latest")
    latest_block_timestamp = latest_block.get("timestamp")
    if latest_block_timestamp is None:
        print("Warning: Latest block does not contain a timestamp. Retrying...")
        time.sleep(1)
        continue

    print(
        f"Latest block timestamp: {latest_block_timestamp}: {datetime.fromtimestamp(latest_block_timestamp)}"
    )

    # Check if the last block was before the hour and the next block is after the hour
    if (
        latest_block_timestamp
        and datetime.fromtimestamp(latest_block_timestamp).minute == 59
        and datetime.fromtimestamp(latest_block_timestamp + 12).minute == 0
    ):
        # test_transaction() # always error, because of the timestamp has not updated yet
        send_transaction(NONCE)

    time.sleep(1)  # Poll every second
