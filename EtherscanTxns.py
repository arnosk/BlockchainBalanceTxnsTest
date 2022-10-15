"""
Created on Feb 20, 2022

@author: arno

Get all transactions of an eth address with Etherscan.io
 
1: Normal (Native) ethereum balance
2: Get a list of ‘Normal’ Transactions By Address
3: Get a list of ‘Internal’ Transactions by Address
4: Get a list of “ERC20 — Token Transfer Events” by Address
5: Get a list of “ERC721 — Token Transfer Events” by Address
6: Get [a] list of Blocks Mined by Address

"""
from web3 import Web3
import requests
import config
from datetime import datetime, timezone
import time
import sys


eth_address = Web3.toChecksumAddress(config.ETH_ADDRESS[3])
#eth_address = '0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3' # internal tx
#eth_address = '0x4e83362442b8d1bec281594cea3050c8eb01311c' # token
#eth_address = '0x6975be450864c02b4613023c2152ee0743572325' # NFT
#eth_address = '0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b' # mined block

def get_request_response(url):
    """
    Get a response from an url request
    Will retry in case of an exception after
    """
    resp = []
    retries = 1
    succes = False
    while not succes:
        try:
            response = requests.get(url)
            resp = response.json()
            print(resp['status'], resp['message'])
            if (resp['status']=='0' and resp['message']=='NOTOK'):
                err_msg = resp['result']
                raise Exception(err_msg)
            succes = True
        except Exception as e:
            wait = retries*15;
            print('Error: %s. Waiting %s secs and retrying' % (e, wait))
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1
    
    return resp


# 1: Normal ethereum balance
url_eth_balance = config.ETHERSCAN_URL + \
                '?module=account&action=balance&address=' + \
                eth_address + '&tag=latest&apikey=' + \
                config.ETHERSCAN_API 
resp = get_request_response(url_eth_balance)
eth_balance = int(resp['result']) / 10**18
print('Balance: %s ETH'%(eth_balance))
print()


# 2: Get a list of ‘Normal’ Transactions By Address
# http://api.etherscan.io/api?module=account&action=txlist&address=0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "Normal" Transactions By Address')
url_eth_txlist =  config.ETHERSCAN_URL + \
                '?module=account&action=txlist&address=' + \
                eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
resp = get_request_response(url_eth_txlist)
res = resp['result']
print('number of tx: ', len(res))
for i in res:
    tx_block = i['blockNumber']
    tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    tx_hash = i['hash']
    tx_nonce = i['nonce']
    tx_blockhash = i['blockHash']
    tx_transaction_index = i['transactionIndex']
    tx_from = i['from']
    tx_to = i['to']
    tx_value = int(i['value']) / 10**18
    tx_gas = int(i['gas'])
    tx_gas_price = int(i['gasPrice'])
    tx_gas_used = int(i['gasUsed'])
    tx_is_error = i['isError']
    tx_receipt_status = i['txreceipt_status']
    tx_input = i['input']
    tx_contract_address = i['contractAddress']
    tx_cumulative_gas_used = int(i['cumulativeGasUsed'])
    tx_confirmations = int(i['confirmations'])
    tx_fee = tx_gas_price * tx_gas_used / 10**18
    tx_method_id = tx_input[:10]
    tx_method = ''
    if len(tx_method_id) == 10:
        url_getmethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + tx_method_id
        response_method = requests.request('GET', url_getmethod)
        resp_method = response_method.json()
        #print(resp_method)
        for j in resp_method['results']:
            tx_method += j['text_signature'] + ';'

    print('Block: %s %s, From: %s -> To: %s, Contract: %s, value: %s, fee: %s, method: %s, %s'%
          (tx_block, tx_time, tx_from, tx_to, tx_contract_address, tx_value, tx_fee, tx_method_id, tx_method))
print()


# 3: Get a list of ‘Internal’ Transactions by Address
# http://api.etherscan.io/api?module=account&action=txlistinternal&address=0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3&startblock=0&endblock=2702578&sort=asc&apikey=YourApiKeyToken
print('Get a list of "Internal" Transactions By Address')
url_eth_txlist_int =  config.ETHERSCAN_URL + \
                '?module=account&action=txlistinternal&address=' + \
                eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
resp = get_request_response(url_eth_txlist_int)
res = resp['result']
print('number of tx: ', len(res))
for i in res:
    tx_block  = i['blockNumber']
    tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    tx_hash = i['hash']
    tx_from = i['from']
    tx_to = i['to']
    tx_value = int(i['value']) / 10**18
    tx_contract_address = i['contractAddress']
    tx_input = i['input']
    tx_type = i['type']
    tx_gas = int(i['gas'])
    tx_gas_price = 0 #int(i['gasPrice'])
    tx_gas_used = int(i['gasUsed'])
    tx_trace_id = i['traceId']
    tx_is_error = i['isError']
    tx_err_code = i['errCode']
    tx_fee = tx_gas_price * tx_gas_used / 10**18
    print('Block: %s %s, From: %s -> Contract: %s, value: %s, fee: %s'%
          (tx_block, tx_time, tx_from, tx_contract_address, tx_value, tx_fee))
print()


# 4: Get a list of “ERC20 — Token Transfer Events” by Address
# http://api.etherscan.io/api?module=account&action=tokentx&address=0x4e83362442b8d1bec281594cea3050c8eb01311c&startblock=0&endblock=999999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "ERC20 — Token Transfer Events" Transactions By Address')
url_eth_token_txlist =  config.ETHERSCAN_URL + \
                '?module=account&action=tokentx&address=' + \
                eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
resp = get_request_response(url_eth_token_txlist)
res = resp['result']
print('number of tx: ', len(res))
for i in res:
    tx_block  = i['blockNumber']
    tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    tx_hash = i['hash']
    tx_nonce = i['nonce']
    tx_blockhash = i['blockHash']
    tx_from = i['from']
    tx_contract_address = i['contractAddress']
    tx_to = i['to']
    tx_token_name = i['tokenName']
    tx_token_symbol = i['tokenSymbol']
    tx_token_decimal = int(i['tokenDecimal'])
    tx_value = int(i['value']) / 10**tx_token_decimal
    tx_transaction_index = i['transactionIndex']
    tx_gas = int(i['gas'])
    tx_gas_price = int(i['gasPrice'])
    tx_gas_used = int(i['gasUsed'])
    tx_cumulative_gas_used = int(i['cumulativeGasUsed'])
    tx_input = i['input']
    tx_confirmations = int(i['confirmations'])
    tx_fee = tx_gas_price * tx_gas_used / 10**18
    print('Block: %s %s, From: %s -> Contract: %s, to: %s, value: %s %s (%s), fee: %s'%
          (tx_block, tx_time, tx_from, tx_contract_address, tx_to, tx_value, tx_token_symbol, tx_token_name, tx_fee))
print()


# 5: Get a list of “ERC721 — Token Transfer Events” by Address
# http://api.etherscan.io/api?module=account&action=tokennfttx&address=0x6975be450864c02b4613023c2152ee0743572325&startblock=0&endblock=999999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "ERC721 — Token Transfer Events" Transactions By Address')
url_eth_token_nft_txlist =  config.ETHERSCAN_URL + \
                '?module=account&action=tokennfttx&address=' + \
                eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
resp = get_request_response(url_eth_token_nft_txlist)
res = resp['result']
print('number of tx: ', len(res))
for i in res:
    tx_block  = i['blockNumber']
    tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    tx_hash = i['hash']
    tx_nonce = i['nonce']
    tx_blockhash = i['blockHash']
    tx_from = i['from']
    tx_contract_address = i['contractAddress']
    tx_to = i['to']
    tx_token_id = i['tokenID']
    tx_token_name = i['tokenName']
    tx_token_symbol = i['tokenSymbol']
    tx_token_decimal = int(i['tokenDecimal'])
    tx_transaction_index = i['transactionIndex']
    tx_gas = int(i['gas'])
    tx_gas_price = int(i['gasPrice'])
    tx_gas_used = int(i['gasUsed'])
    tx_cumulative_gas_used = int(i['cumulativeGasUsed'])
    tx_input = i['input']
    tx_confirmations = int(i['confirmations'])
    tx_fee = tx_gas_price * tx_gas_used / 10**18
    print('Block: %s %s, From: %s -> Contract: %s, to: %s, ID: %s %s (%s), fee: %s'%
          (tx_block, tx_time, tx_from, tx_contract_address, tx_to, tx_token_id, tx_token_symbol, tx_token_name, tx_fee))
print()


# 6: Get [a] list of Blocks Mined by Address
# https://api.etherscan.io/api?module=account&action=getminedblocks&address=0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b&blocktype=blocks&apikey=YourApiKeyToken
print('Get a list of Blocks Mined By Address')
url_eth_mined_blocklist =  config.ETHERSCAN_URL + \
                '?module=account&action=getminedblocks&address=' + \
                eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
resp = get_request_response(url_eth_mined_blocklist)
res = resp['result']
print('number of tx: ', len(res))
for i in res:
    tx_block  = i['blockNumber']
    tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    tx_block_reward  = int(i['blockReward']) / 10**18
    print('Block: %s %s, reward: %s'%
          (tx_block, tx_time, tx_block_reward))
print()
