import configparser
import os
import json
from time import sleep
import asyncio

import base58
from typing import AsyncIterator
from asyncstdlib import enumerate
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Finalized
from solana.rpc.api import Client
from solana.exceptions import SolanaRpcException
from websockets.exceptions import ConnectionClosedError, ProtocolError
from solana.rpc.websocket_api import SolanaWsClientProtocol
from solders.signature import Signature
from solana.rpc.api import Pubkey, Keypair
from solana.rpc.commitment import Commitment
from utils._core import buy, sell, get_pool_infos


async def main():
    async for websocket in connect(wss_url):
        try:
            subscription_id = await subscribe_to_logs(
                websocket,
                RpcTransactionLogsFilterMentions(raydium_lp_v4),
                Finalized
            )
            async for i, signature in enumerate(process_messages(websocket, log_instruction)):  # type: ignore
                try:
                    transaction = solana_client.get_transaction(
                        signature,
                        encoding="jsonParsed",
                        max_supported_transaction_version=0
                    )
                    instructions = transaction.value.transaction.transaction.message.instructions
                    filtered_instuctions = [instruction for instruction in instructions if
                                            instruction.program_id == raydium_lp_v4]
                    for instruction in filtered_instuctions:
                        accounts = instruction.accounts
                        print(f'token name: {accounts[8].__str__()}')
                        print(f"dex trade, https://dexscreener.com/solana/{str(accounts[8])}")
                        print(f"signature info, https://solscan.io/tx/{signature}")
                        if is_auto_buy != '0':
                            private_key_bytes = base58.b58decode(private_key_string)
                            payer = Keypair.from_bytes(private_key_bytes)
                            # write pool_keys to local
                            pool_keys = get_pool_infos(accounts, solana_client)

                            account_info = solana_client.get_account_info_json_parsed(
                                Pubkey.from_string(pool_keys.get('quoteVault')))
                            if account_info.value:
                                token_lamports = account_info.value.lamports
                                lamport_per_sol = 1000000000
                                pool_number = token_lamports / lamport_per_sol
                                print(f'pool size: {pool_number}')
                                if pool_number >= float(pool_size):
                                    _pool_infos = {
                                        "name": accounts[8].__str__(),
                                        "value": pool_keys,
                                    }

                                    if not os.path.exists('pool_information.json'):
                                        with open('pool_information.json', 'w') as fw:
                                            fw.write('[]')
                                    with open('pool_information.json', 'r') as fw:
                                        contents = json.load(fw)
                                    contents.append(_pool_infos)
                                    with open('pool_information.json', 'w') as fw:
                                        json.dump(contents, fw)

                                    token_contract_address = accounts[8].__str__()
                                    buy_task = asyncio.create_task(
                                        buy(solana_client, token_contract_address, payer, float(buy_amount), pool_keys))
                                    buy_result = await buy_task
                                    if is_auto_sell != '0' and buy_result:
                                        sell_task = asyncio.create_task(
                                            sell(solana_client, token_contract_address, payer, pool_keys))
                                        # waiting to sell token
                                        await asyncio.sleep(int(gap_time))
                                        sell_result = await sell_task
                                        if not sell_result:
                                            for _ in range(10):
                                                sell_task = asyncio.create_task(
                                                    sell(solana_client, token_contract_address, payer, pool_keys))
                                                result = await sell_task
                                                if result:
                                                    break
                            else:
                                print(f'pool size: {0}')
                        else:
                            print('switch buy status: close')

                    break
                except SolanaRpcException as err:
                    print(f"sleep for 5 seconds and try again, error information: {err}")
                    sleep(5)
                    continue
        except (ProtocolError, ConnectionClosedError) as err:
            continue
        except KeyboardInterrupt:
            if websocket:
                await websocket.logs_unsubscribe(subscription_id)


async def subscribe_to_logs(websocket: SolanaWsClientProtocol,
                            mentions: RpcTransactionLogsFilterMentions,
                            commitment: Commitment) -> int:
    await websocket.logs_subscribe(
        filter_=mentions,
        commitment=commitment
    )
    first_resp = await websocket.recv()
    return first_resp[0].result  # type: ignore


async def process_messages(websocket: SolanaWsClientProtocol,
                           instruction: str) -> AsyncIterator[Signature]:
    async for idx, msg in enumerate(websocket):
        value = msg[0].result.value
        if not idx % 100:
            print(f'idx: {idx}')
        for log in value.logs:
            if instruction not in log:
                continue
            yield value.signature


def transfer_pool_keys_to_pk(pool_keys: dict):
    tf_pool_keys = {}
    for name, value in pool_keys.items():
        if isinstance(value, int):
            tf_pool_keys[name] = value
        else:
            tf_pool_keys[name] = Pubkey.from_string(value)

    return tf_pool_keys


if __name__ == "__main__":
    # config proxy
    os.environ["http_proxy"] = "http://127.0.0.1:10809"
    os.environ["https_proxy"] = "http://127.0.0.1:10809"

    config = configparser.ConfigParser()
    config.read('./config.ini')
    # solana init config
    main_url = config['solanaConfig']['main_url']
    wss_url = config['solanaConfig']['wss_url']
    raydium_lp_v4 = config['solanaConfig']['raydium_lp_v4']
    log_instruction = config['solanaConfig']['log_instruction']

    # trade config
    private_key_string = config['user']['private_key']
    is_auto_buy = config['config']['is_auto_buy']
    is_auto_sell = config['config']['is_auto_sell']
    pool_size = config['config']['pool_size']
    buy_amount = config['config']['buy_amount']
    gap_time = config['config']['gap_time']

    solana_client = Client(main_url)
    raydium_lp_v4 = Pubkey.from_string(raydium_lp_v4)
    print(f"start solana sniper...")
    asyncio.run(main())

