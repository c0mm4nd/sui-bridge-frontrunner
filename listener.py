import os
import time
import requests

RPC = "https://rpc.flashbots.net/"
THRESHOLD = 1000

LIMIT = 5000000000000000 # Sui raised limit @ https://etherscan.io/tx/0xd9f503cd0c2694260c8d9db6af42c4f2f82ed74f41c5d12b09c870b1ec1a79e3

def calcWindowAmountUsed() -> int:
    response = requests.post(
        RPC,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [
                {
                    "data": "0xc6b478dd0000000000000000000000000000000000000000000000000000000000000000",
                    "to": "0x12183B0796BBc4678999100e8c6C5715D5736767",
                },
                "latest",
            ],
        },
    )
    result = response.json()
    if "result" not in result:
        raise Exception(f"eth_call failed: {result}")
    result = result.get("result")
    amount_used = int(result, 16)
    return amount_used

while True:
    try:
        withdrawable_usd = (LIMIT - calcWindowAmountUsed()) / 1e8
        # log with datetime
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}: Withdrawable USDT amount: {withdrawable_usd} USDT")
        if withdrawable_usd >= THRESHOLD:
            # say notify
            os.system(f'say "Withdraw {withdrawable_usd}"')
        time.sleep(2)
    except Exception as e:
        print(f"Error occurred: {e}")
        os.system('say "Error"')
        time.sleep(4)
