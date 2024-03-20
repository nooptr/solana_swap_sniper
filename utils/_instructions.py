import os
import json
import requests

from spl.token.instructions import create_associated_token_account, get_associated_token_address

from solders.pubkey import Pubkey
from solders.instruction import Instruction

from solana.rpc.types import TokenAccountOpts
from solana.transaction import AccountMeta

from utils.layouts import SWAP_LAYOUT

AMM_PROGRAM_ID = Pubkey.from_string('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
SERUM_PROGRAM_ID = Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')


def make_swap_instruction(amount_in: int, token_account_in: Pubkey.from_string, token_account_out: Pubkey.from_string,
                          accounts: dict, mint, ctx, owner) -> Instruction:
    tokenPk = mint
    accountProgramId = ctx.get_account_info_json_parsed(tokenPk)
    TOKEN_PROGRAM_ID = accountProgramId.value.owner
    keys = [
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["id"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["openOrders"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["targetOrders"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["baseVault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["quoteVault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SERUM_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["marketId"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketBids"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketAsks"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketEventQueue"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketBaseVault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketQuoteVault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["marketAuthority"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),  # UserSourceTokenAccount
        AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True),  # UserDestTokenAccount
        AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False)  # UserOwner
    ]
    data = SWAP_LAYOUT.build(
        dict(
            instruction=9,
            amount_in=int(amount_in),
            min_amount_out=0
        )
    )
    return Instruction(AMM_PROGRAM_ID, data, keys)


def get_token_account(ctx,
                      owner: Pubkey.from_string,
                      mint: Pubkey.from_string):
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey, None
    except:
        swap_associated_token_address = get_associated_token_address(owner, mint)
        swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
        return swap_associated_token_address, swap_token_account_Instructions


def sell_get_token_account(ctx,
                           owner: Pubkey.from_string,
                           mint: Pubkey.from_string):
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey
    except:
        print("Mint Token Not found")
        return None


def extract_pool_info(pools_list: list, mint: str) -> dict:
    for pool in pools_list:

        if pool['baseMint'] == mint and pool['quoteMint'] == 'So11111111111111111111111111111111111111112':
            return pool
        elif pool['quoteMint'] == mint and pool['baseMint'] == 'So11111111111111111111111111111111111111112':
            return pool
    raise Exception(f'{mint} pool not found!')


def fetch_local_pool_keys(mint: str):
    try:
        # Using this so it will be faster else no option, we go the slower way.
        pool_keys = {}
        # 关键步骤更新
        local_pool_infos_path = '../pool_information.json'
        if os.path.exists(local_pool_infos_path):
            with open(local_pool_infos_path, 'r') as file:
                items = json.load(file)
            for item in items:
                if item.get("name") == mint:
                    pool_keys = item.get('value')
                    break
            if pool_keys:
                return {
                    'id': Pubkey.from_string(pool_keys['id']),
                    'authority': Pubkey.from_string(pool_keys['authority']),
                    'baseMint': Pubkey.from_string(pool_keys['baseMint']),
                    'baseDecimals': pool_keys['baseDecimals'],
                    'quoteMint': Pubkey.from_string(pool_keys['quoteMint']),
                    'quoteDecimals': pool_keys['quoteDecimals'],
                    'lpMint': Pubkey.from_string(pool_keys['lpMint']),
                    'openOrders': Pubkey.from_string(pool_keys['openOrders']),
                    'targetOrders': Pubkey.from_string(pool_keys['targetOrders']),
                    'baseVault': Pubkey.from_string(pool_keys['baseVault']),
                    'quoteVault': Pubkey.from_string(pool_keys['quoteVault']),
                    'marketId': Pubkey.from_string(pool_keys['marketId']),
                    'marketBaseVault': Pubkey.from_string(pool_keys['marketBaseVault']),
                    'marketQuoteVault': Pubkey.from_string(pool_keys['marketQuoteVault']),
                    'marketAuthority': Pubkey.from_string(pool_keys['marketAuthority']),
                    'marketBids': Pubkey.from_string(pool_keys['marketBids']),
                    'marketAsks': Pubkey.from_string(pool_keys['marketAsks']),
                    'marketEventQueue': Pubkey.from_string(pool_keys['marketEventQueue'])
                }
            else:
                return fetch_pool_keys(mint)
        else:
            return fetch_pool_keys(mint)
    except:
        print('not find pool keys')
        return {}


def fetch_pool_keys(mint: str):
    _pool_keys = {}
    all_pools = {}
    try:
        with open('all_pools.json', 'r') as file:
            all_pools = json.load(file)
        _pool_keys = extract_pool_info(all_pools, mint)
    except:
        try:
            resp = requests.get('https://api.raydium.io/v2/sdk/liquidity/mainnet.json', stream=True)
        except:

            raise
        pools = resp.json()
        official = pools['official']
        unofficial = pools['unOfficial']
        all_pools = official + unofficial

        with open('all_pools.json', 'w') as file:
            json.dump(all_pools, file)
        try:
            _pool_keys = extract_pool_info(all_pools, mint)
        except:
            return "failed"
    return {
        'id': Pubkey.from_string(_pool_keys['id']),
        'authority': Pubkey.from_string(_pool_keys['authority']),
        'baseMint': Pubkey.from_string(_pool_keys['baseMint']),
        'baseDecimals': _pool_keys['baseDecimals'],
        'quoteMint': Pubkey.from_string(_pool_keys['quoteMint']),
        'quoteDecimals': _pool_keys['quoteDecimals'],
        'lpMint': Pubkey.from_string(_pool_keys['lpMint']),
        'openOrders': Pubkey.from_string(_pool_keys['openOrders']),
        'targetOrders': Pubkey.from_string(_pool_keys['targetOrders']),
        'baseVault': Pubkey.from_string(_pool_keys['baseVault']),
        'quoteVault': Pubkey.from_string(_pool_keys['quoteVault']),
        'marketId': Pubkey.from_string(_pool_keys['marketId']),
        'marketBaseVault': Pubkey.from_string(_pool_keys['marketBaseVault']),
        'marketQuoteVault': Pubkey.from_string(_pool_keys['marketQuoteVault']),
        'marketAuthority': Pubkey.from_string(_pool_keys['marketAuthority']),
        'marketBids': Pubkey.from_string(_pool_keys['marketBids']),
        'marketAsks': Pubkey.from_string(_pool_keys['marketAsks']),
        'marketEventQueue': Pubkey.from_string(_pool_keys['marketEventQueue'])
    }
