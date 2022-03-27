'''
Created on Feb 18, 2022

@author: arno

Get all transactions of an address with Moralis

1: Normal (Native) ethereum balance
2: Get a list of ‘Normal’ Transactions By Address
3: Not done, Get a list of ‘Internal’ Transactions by Address
4: Get a list of “ERC20 — Token Transfer Events” by Address
5: Get a list of “ERC721 — Token Transfer Events” by Address
6: Not done, Get [a] list of Blocks Mined by Address

'''
from web3 import Web3
from datetime import datetime, timezone
import requests
import sys
import config

# check configuration
if (config.MORALIS_NODE_KEY=='' or config.MORALIS_API_DEF==''):
    sys.exit('No Moralis node key or API defined in config file. Aborting')

# add your blockchain connection information
chain = input("What chain you want to query(eth or bsc or polygon)?: ")
moralisProvider = config.MORALIS_HTTP_PROVIDER + config.MORALIS_NODE_KEY + '/' + chain + '/mainnet'   
w3 = Web3(Web3.HTTPProvider(moralisProvider))
print(w3.isConnected())

ethAddress = Web3.toChecksumAddress(config.ETH_ADDRESS[3])

# 1: Normal balance
balanceWei = w3.eth.getBalance(ethAddress)
balance = Web3.fromWei(balanceWei,'ether')
print('Balance: {}'.format(balance))


header = {
  'x-api-key': config.MORALIS_API_DEF
}

# 2: Get a list of ‘Normal’ Transactions By Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c?chain=eth
print('Get a list of "Normal" Transactions By Address')
urlEthTxlist = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '?chain=' + chain + '&page=1'
response = requests.get(urlEthTxlist, headers=header)
resp = response.json()
txTotal = resp['total']
txPage = resp['page']
txPageSize = resp['page_size']
print("Total tx %s, page %s, pagesize %s"%(txTotal,txPage,txPageSize))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    txHash = i['hash']
    txNonce = i['nonce']
    txTxnsIndex = i['transaction_index']
    txFrom = i['from_address']
    txTo = i['to_address']
    txValue = int(i['value']) / 10**18
    txGas = int(i['gas'])
    txGasPrice = int(i['gas_price'])
    txTime = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    txBlock  = i['block_number']
    txBlockHash = i['block_hash']
    txCumulativeGasUsed = int(i['receipt_cumulative_gas_used'])
    txGasUsed = int(i['receipt_gas_used'])
    txContractAddress = i['receipt_contract_address']
    txInput = i['input']
    txReceipt_status = i['receipt_status']
    txReceipt_root = i['receipt_root']
   
    txFee = txGasPrice * txGasUsed / 10**18
    txMethodId = txInput[:10]
    txMethod = ''
    # temporalely disabled because of speed
    # if len(txMethodId) == 10:
    #     urlGetMethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + txMethodId
    #     responseMethod = requests.request("GET", urlGetMethod)
    #     respMethod = responseMethod.json()
    #     #print(respMethod)
    #     for j in respMethod['results']:
    #         txMethod += j['text_signature'] + ';'

    print("Block: %s %s, From: %s -> To: %s, Contract: %s, value: %s, fee: %s, method: %s, %s"%
          (txBlock, txTime, txFrom, txTo, txContractAddress, txValue, txFee, txMethodId, txMethod))
print()


# 4: Get a list of “ERC20 — Token Transfer Events” by Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c/erc20/transfers?chain=eth
print('Get a list of "ERC20 — Token Transfer Events" Transactions By Address')
urlEthTokenTxlist = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '/erc20/transfers?chain=' + chain
response = requests.get(urlEthTokenTxlist, headers=header)
resp = response.json()
txTotal = resp['total']
txPage = resp['page']
txPageSize = resp['page_size']
print("Total tx %s, page %s, pagesize %s"%(txTotal,txPage,txPageSize))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    txHash = i['transaction_hash']
    txContractAddress = i['address']
    txTime = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    txBlock  = i['block_number']
    txBlockHash = i['block_hash']
    txFrom = i['from_address']
    txTo = i['to_address']
    txValue = int(i['value'])
    print("Block: %s %s, From: %s -> Contract: %s, to: %s, value: %s"%
          (txBlock, txTime, txFrom, txContractAddress, txTo, txValue))
print()


# 5: Get a list of “ERC721 — Token Transfer Events” by Address
# https://deep-index.moralis.io/api/v2/0x4e83362442b8d1bec281594cea3050c8eb01311c/nft/transfers?chain=eth
print('Get a list of "ERC721 — Token Transfer Events" Transactions By Address')
urlEthTokenNftTxlist = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '/nft/transfers?chain=' + chain
response = requests.get(urlEthTokenNftTxlist, headers=header)
resp = response.json()
txTotal = resp['total']
txPage = resp['page']
txPageSize = resp['page_size']
print("Total tx %s, page %s, pagesize %s"%(txTotal,txPage,txPageSize))
print('number of tx: ', len(resp['result']))
for i in resp['result']:
    txBlock  = i['block_number']
    txTime = datetime.fromisoformat(i['block_timestamp'][:-1]).astimezone(timezone.utc)
    txHash = i['transaction_hash']
    txType = i['transaction_type']
    txTransactionIndex = i['transaction_index']
    txBlockHash = i['block_hash']
    txFrom = i['from_address']
    txContractAddress = i['token_address']
    txTo = i['to_address']
    txTokenID = i['token_id']
    txValue = int(i['value']) / 10**18
    txAmount = int(i['amount'])
    txContractType = i['contract_type']
    txLogIndex = i['log_index']
    txVerified = i['verified']
    txOperator = i['operator']
    print("Block: %s %s, From: %s -> Contract: %s, to: %s, ID: %s"%
          (txBlock, txTime, txFrom, txContractAddress, txTo, txTokenID))
print()

