"""
Created on Feb 18, 2022

@author: arno

Get all ERC20 tokens and main (ETH or BNB or ...) balance of an address with Moralis

1: Normal balance
2: ERC20 Token balance

"""
from web3 import Web3
import requests
import config
import sys

# check configuration
if (config.MORALIS_NODE_KEY=='' or config.MORALIS_API_DEF==''):
    sys.exit('No Moralis node key or API defined in config file. Aborting')

# add your blockchain connection information
chain = input('What chain you want to query(eth or bsc or polygon)?: ')
moralis_provider = config.MORALIS_HTTP_PROVIDER + config.MORALIS_NODE_KEY + '/' + chain + '/mainnet'   
w3 = Web3(Web3.HTTPProvider(moralis_provider))
print(w3.isConnected())

header = {
  'x-api-key': config.MORALIS_API_DEF
}

eth_address = Web3.toChecksumAddress(config.ETH_ADDRESS[8])


# 1: Normal balance
balance_wei = w3.eth.getBalance(eth_address)
balance = Web3.fromWei(balance_wei,'ether')
print('Balance: {}'.format(balance))
print()

# 2: ERC20 Token balance
url_erc20_balance = 'https://deep-index.moralis.io/api/v2/'+ eth_address + '/erc20?chain=' + chain
response = requests.request('GET', url_erc20_balance, headers=header)
resp = response.json()
print('number of tokens: ', len(resp))
for i in resp:
    tkn_name  = i['name']
    tkn_symbol  = i['symbol']
    tkn_addr = i['token_address']
    tkn_raw_balance = int(i['balance'])
    tkn_decimals = int(i['decimals'])
    tkn_balance = tkn_raw_balance / 10**tkn_decimals
    tkn_logo = i['logo']
    tkn_thumbnail = i['thumbnail']
    #print('{} {}, {}, {}'.format(tkn_balance,tkn_symbol,tkn_name,tkn_addr))
    print('%s : %-20f %10s , %s'%(tkn_addr,tkn_balance,tkn_symbol,tkn_name))
print()

# 2: ERC721 Token balance
url_erc721_balance = 'https://deep-index.moralis.io/api/v2/'+ eth_address + '/nft?chain=' + chain
response = requests.request('GET', url_erc721_balance, headers=header)
resp = response.json()
#print(resp)
tx_total = resp['total']
tx_page = resp['page']
tx_page_size = resp['page_size']
print('Total nft %s, page %s, pagesize %s'%(tx_total,tx_page,tx_page_size))
print('number of nft: ', len(resp['result']))
for i in resp['result']:
    tkn_name  = i['name']
    tkn_symbol  = i['symbol']
    tkn_amount  = i['amount']
    tkn_addr = i['token_address']
    tkn_id = i['token_id']
    tkn_uri = i['token_uri']
    tkn_metadata = i['metadata']
    tkn_synced_at = i['synced_at']
    tkn_contract_type = i['contract_type']
    tkn_owner_of = i['owner_of']
    tkn_block_number = i['block_number']
    tkn_block_number_minted = i['block_number_minted']
    tkn_is_valid = i['is_valid']
    tkn_syncing = i['syncing']
    tkn_frozen = i['frozen']
    #print('{} {}, {}, {}'.format(tkn_balance,tkn_symbol,tkn_name,tkn_addr))
    print('%s : %s %10s , %s , id: %s'%(tkn_addr,tkn_amount, tkn_symbol, tkn_name, tkn_id))
print()

