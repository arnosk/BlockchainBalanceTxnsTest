"""
Created on Feb 18, 2022

@author: arno

Get all transactions of an address with Moralis

1: Normal (Native) ethereum balance
2: Get a list of ‘Normal’ Transactions By Address
3: Not done, Get a list of ‘Internal’ Transactions by Address
4: Get a list of “ERC20 — Token Transfer Events” by Address
5: Get a list of “ERC721 — Token Transfer Events” by Address
6: Not done, Get [a] list of Blocks Mined by Address

"""
from web3 import Web3
from datetime import datetime, timezone
import requests
import sys
import config

# check configuration
if (config.MORALIS_NODE_KEY=='' or config.MORALIS_API_DEF==''):
    sys.exit('No Moralis node key or API defined in config file. Aborting')

# add your blockchain connection information
chain = input('What chain you want to query(eth or bsc or polygon)?: ')
moralis_provider = config.MORALIS_HTTP_PROVIDER + config.MORALIS_NODE_KEY + '/' + chain + '/mainnet'   
w3 = Web3(Web3.HTTPProvider(moralis_provider))
print(w3.isConnected())

eth_address = Web3.toChecksumAddress(config.ETH_ADDRESS[3])

# 1: Normal balance
balance_wei = w3.eth.getBalance(eth_address)
balance = Web3.fromWei(balance_wei,'ether')
print('Balance: {}'.format(balance))


header = {
  'x-api-key': config.MORALIS_API_DEF
}

# 2: Get a list of ‘Normal’ Transactions By Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c?chain=eth
print('Get a list of "Normal" Transactions By Address')
url_eth_txlist = 'https://deep-index.moralis.io/api/v2/'+ eth_address + '?chain=' + chain + '&page=1'
response = requests.get(url_eth_txlist, headers=header)
resp = response.json()
tx_total = resp['total']
tx_page = resp['page']
tx_page_size = resp['page_size']
print('Total tx %s, page %s, pagesize %s'%(tx_total,tx_page,tx_page_size))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    tx_hash = i['hash']
    tx_nonce = i['nonce']
    tx_txns_index = i['transaction_index']
    tx_from = i['from_address']
    tx_to = i['to_address']
    tx_value = int(i['value']) / 10**18
    tx_gas = int(i['gas'])
    tx_gas_price = int(i['gas_price'])
    tx_time = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    tx_block  = i['block_number']
    tx_block_hash = i['block_hash']
    tx_cumulative_gas_used = int(i['receipt_cumulative_gas_used'])
    tx_gas_used = int(i['receipt_gas_used'])
    tx_contract_address = i['receipt_contract_address']
    tx_input = i['input']
    tx_receipt_status = i['receipt_status']
    tx_receipt_root = i['receipt_root']
   
    tx_fee = tx_gas_price * tx_gas_used / 10**18
    tx_method_id = tx_input[:10]
    tx_method = ''
    # temporalely disabled because of speed
    # if len(tx_method_id) == 10:
    #     urlGetMethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + tx_method_id
    #     responseMethod = requests.request('GET', urlGetMethod)
    #     respMethod = responseMethod.json()
    #     #print(respMethod)
    #     for j in respMethod['results']:
    #         tx_method += j['text_signature'] + ';'

    print('Block: %s %s, From: %s -> To: %s, Contract: %s, value: %s, fee: %s, method: %s, %s'%
          (tx_block, tx_time, tx_from, tx_to, tx_contract_address, tx_value, tx_fee, tx_method_id, tx_method))
print()


# 4: Get a list of “ERC20 — Token Transfer Events” by Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c/erc20/transfers?chain=eth
print('Get a list of "ERC20 — Token Transfer Events" Transactions By Address')
url_eth_token_txlist = 'https://deep-index.moralis.io/api/v2/'+ eth_address + '/erc20/transfers?chain=' + chain
response = requests.get(url_eth_token_txlist, headers=header)
resp = response.json()
tx_total = resp['total']
tx_page = resp['page']
tx_page_size = resp['page_size']
print('Total tx %s, page %s, pagesize %s'%(tx_total,tx_page,tx_page_size))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    tx_hash = i['transaction_hash']
    tx_contract_address = i['address']
    tx_time = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    tx_block  = i['block_number']
    tx_block_hash = i['block_hash']
    tx_from = i['from_address']
    tx_to = i['to_address']
    tx_value = int(i['value'])
    print('Block: %s %s, From: %s -> Contract: %s, to: %s, value: %s'%
          (tx_block, tx_time, tx_from, tx_contract_address, tx_to, tx_value))
print()


# 5: Get a list of “ERC721 — Token Transfer Events” by Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c/nft/transfers?chain=eth
print('Get a list of "ERC721 — Token Transfer Events" Transactions By Address')
url_eth_token_nft_txlist = 'https://deep-index.moralis.io/api/v2/'+ eth_address + '/nft/transfers?chain=' + chain
response = requests.get(url_eth_token_nft_txlist, headers=header)
resp = response.json()
tx_total = resp['total']
tx_page = resp['page']
tx_page_size = resp['page_size']
print('Total tx %s, page %s, pagesize %s'%(tx_total,tx_page,tx_page_size))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    tx_block  = i['block_number']
    tx_time = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    tx_hash = i['transaction_hash']
    tx_type = i['transaction_type']
    tx_transaction_index = i['transaction_index']
    tx_block_hash = i['block_hash']
    tx_from = i['from_address']
    tx_contract_address = i['token_address']
    tx_to = i['to_address']
    tx_tokenID = i['token_id']
    tx_value = int(i['value']) / 10**18
    tx_amount = int(i['amount'])
    tx_contract_type = i['contract_type']
    tx_log_index = i['log_index']
    tx_verified = i['verified']
    tx_operator = i['operator']
    print('Block: %s %s, From: %s -> Contract: %s, to: %s, ID: %s'%
          (tx_block, tx_time, tx_from, tx_contract_address, tx_to, tx_tokenID))
print()

