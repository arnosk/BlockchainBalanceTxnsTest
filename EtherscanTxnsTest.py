'''
Created on Feb 20, 2022

@author: arno

Get all transactions of an eth address with Etherscan.io
 
1: Normal (Native)ethereum balance
2: Get a list of ‘Normal’ Transactions By Address
3: Get a list of ‘Internal’ Transactions by Address
4: Get a list of “ERC20 — Token Transfer Events” by Address
5: Get a list of “ERC721 — Token Transfer Events” by Address
6: Get [a] list of Blocks Mined by Address

'''
from web3 import Web3
import requests
import config
from datetime import datetime, timezone
#import json


ethAddress = Web3.toChecksumAddress(config.ETH_ADDRESS[3])
#ethAddress = '0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3' # internal tx
#ethAddress = '0x4e83362442b8d1bec281594cea3050c8eb01311c' # token
#ethAddress = '0x6975be450864c02b4613023c2152ee0743572325' # NFT
#ethAddress = '0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b' # mined block



# 1: Normal ethereum balance
urlEthBalance = config.ETHERSCAN_URL + \
                '?module=account&action=balance&address=' + \
                ethAddress + '&tag=latest&apikey=' + \
                config.ETHERSCAN_API 
#print(urlEthBalance)
response = requests.request("GET", urlEthBalance)
resp = response.json()
ethBalance = int(resp['result']) / 10**18
print('Balance: %s ETH'%(ethBalance))
print()


# 2: Get a list of ‘Normal’ Transactions By Address
# http://api.etherscan.io/api?module=account&action=txlist&address=0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "Normal" Transactions By Address')
urlEthTxlist =  config.ETHERSCAN_URL + \
                '?module=account&action=txlist&address=' + \
                ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
response = requests.request("GET", urlEthTxlist)
resp = response.json()
print('number of tx: ', len(resp['result']))
#print(resp)
for i in resp['result']:
    txBlock = i['blockNumber']
    txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    txHash = i['hash']
    txNonce = i['nonce']
    txBlockHash = i['blockHash']
    txTransactionIndex = i['transactionIndex']
    txFrom = i['from']
    txTo = i['to']
    txValue = int(i['value']) / 10**18
    txGas = int(i['gas'])
    txGasPrice = int(i['gasPrice'])
    txGasUsed = int(i['gasUsed'])
    txIsError = i['isError']
    txReceipt_status = i['txreceipt_status']
    txInput = i['input']
    txContractAddress = i['contractAddress']
    txGasUsed = int(i['gasUsed'])
    txCumulativeGasUsed = int(i['cumulativeGasUsed'])
    txConfirmations = int(i['confirmations'])
    txFee = txGasPrice * txGasUsed / 10**18
    txMethodId = txInput[:10]
    txMethod = ''
    if len(txMethodId) == 10:
        urlGetMethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + txMethodId
        responseMethod = requests.request("GET", urlGetMethod)
        respMethod = responseMethod.json()
        #print(respMethod)
        for j in respMethod['results']:
            txMethod += j['text_signature'] + ';'

    print("Block: %s %s, From: %s -> To: %s, Contract: %s, value: %s, fee: %s, method: %s, %s"%
          (txBlock, txTime, txFrom, txTo, txContractAddress, txValue, txFee, txMethodId, txMethod))
print()


# 3: Get a list of ‘Internal’ Transactions by Address
# http://api.etherscan.io/api?module=account&action=txlistinternal&address=0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3&startblock=0&endblock=2702578&sort=asc&apikey=YourApiKeyToken
print('Get a list of "Internal" Transactions By Address')
urlEthTxlistInt =  config.ETHERSCAN_URL + \
                '?module=account&action=txlistinternal&address=' + \
                ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
response = requests.request("GET", urlEthTxlistInt)
resp = response.json()
print('number of tx: ', len(resp['result']))
#print(resp)
for i in resp['result']:
    txBlock  = i['blockNumber']
    txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    txHash = i['hash']
    txFrom = i['from']
    txTo = i['to']
    txValue = int(i['value']) / 10**18
    txContractAddress = i['contractAddress']
    txInput = i['input']
    txType = i['type']
    txGas = int(i['gas'])
    txGasUsed = int(i['gasUsed'])
    txTraceId = i['traceId']
    txIsError = i['isError']
    txErrCode = i['errCode']
    txFee = txGasPrice * txGasUsed / 10**18
    print("Block: %s %s, From: %s -> Contract: %s, value: %s, fee: %s"%
          (txBlock, txTime, txFrom, txContractAddress, txValue, txFee))
print()


# 4: Get a list of “ERC20 — Token Transfer Events” by Address
# http://api.etherscan.io/api?module=account&action=tokentx&address=0x4e83362442b8d1bec281594cea3050c8eb01311c&startblock=0&endblock=999999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "ERC20 — Token Transfer Events" Transactions By Address')
urlEthTokenTxlist =  config.ETHERSCAN_URL + \
                '?module=account&action=tokentx&address=' + \
                ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
response = requests.request("GET", urlEthTokenTxlist)
resp = response.json()
print('number of tx: ', len(resp['result']))
#print(resp)
for i in resp['result']:
    txBlock  = i['blockNumber']
    txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    txHash = i['hash']
    txNonce = i['nonce']
    txBlockHash = i['blockHash']
    txFrom = i['from']
    txContractAddress = i['contractAddress']
    txTo = i['to']
    txTokenName = i['tokenName']
    txTokenSymbol = i['tokenSymbol']
    txTokenDecimal = int(i['tokenDecimal'])
    txValue = int(i['value']) / 10**txTokenDecimal
    txTransactionIndex = i['transactionIndex']
    txGas = int(i['gas'])
    txGasPrice = int(i['gasPrice'])
    txGasUsed = int(i['gasUsed'])
    txCumulativeGasUsed = int(i['cumulativeGasUsed'])
    txInput = i['input']
    txConfirmations = int(i['confirmations'])
    txFee = txGasPrice * txGasUsed / 10**18
    print("Block: %s %s, From: %s -> Contract: %s, to: %s, value: %s %s (%s), fee: %s"%
          (txBlock, txTime, txFrom, txContractAddress, txTo, txValue, txTokenSymbol, txTokenName, txFee))
print()


# 5: Get a list of “ERC721 — Token Transfer Events” by Address
# http://api.etherscan.io/api?module=account&action=tokennfttx&address=0x6975be450864c02b4613023c2152ee0743572325&startblock=0&endblock=999999999&sort=asc&apikey=YourApiKeyToken
print('Get a list of "ERC721 — Token Transfer Events" Transactions By Address')
urlEthTokenNftTxlist =  config.ETHERSCAN_URL + \
                '?module=account&action=tokennfttx&address=' + \
                ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
response = requests.request("GET", urlEthTokenNftTxlist)
resp = response.json()
print('number of tx: ', len(resp['result']))
#print(resp)
for i in resp['result']:
    txBlock  = i['blockNumber']
    txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    txHash = i['hash']
    txNonce = i['nonce']
    txBlockHash = i['blockHash']
    txFrom = i['from']
    txContractAddress = i['contractAddress']
    txTo = i['to']
    txTokenID = i['tokenID']
    txTokenName = i['tokenName']
    txTokenSymbol = i['tokenSymbol']
    txTokenDecimal = int(i['tokenDecimal'])
    txTransactionIndex = i['transactionIndex']
    txGas = int(i['gas'])
    txGasPrice = int(i['gasPrice'])
    txGasUsed = int(i['gasUsed'])
    txCumulativeGasUsed = int(i['cumulativeGasUsed'])
    txInput = i['input']
    txConfirmations = int(i['confirmations'])
    txFee = txGasPrice * txGasUsed / 10**18
    print("Block: %s %s, From: %s -> Contract: %s, to: %s, ID: %s %s (%s), fee: %s"%
          (txBlock, txTime, txFrom, txContractAddress, txTo, txTokenID, txTokenSymbol, txTokenName, txFee))
print()


# 6: Get [a] list of Blocks Mined by Address
# https://api.etherscan.io/api?module=account&action=getminedblocks&address=0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b&blocktype=blocks&apikey=YourApiKeyToken
print('Get a list of Blocks Mined By Address')
urlEthMinedBlocklist =  config.ETHERSCAN_URL + \
                '?module=account&action=getminedblocks&address=' + \
                ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                config.ETHERSCAN_API
response = requests.request("GET", urlEthMinedBlocklist)
resp = response.json()
print('number of tx: ', len(resp['result']))
#print(resp)
for i in resp['result']:
    txBlock  = i['blockNumber']
    txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
    txBlockReward  = int(i['blockReward']) / 10**18
    print("Block: %s %s, reward: %s"%
          (txBlock, txTime, txBlockReward))
print()
