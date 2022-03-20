'''
Created on Feb 18, 2022

@author: arno

Get all ERC20 tokens and main (ETH or BNB or ...) balance of an address with Moralis

'''
from web3 import Web3
import requests
import config
import sys

# check configuration
if (config.MORALIS_NODE_KEY=='' or config.MORALIS_API_DEF==''):
    sys.exit('No Moralis node key or API defined in config file. Aborting')

# add your blockchain connection information
chain = input("What chain you want to query(eth or bsc or polygon)?: ")
moralisProvider = config.MORALIS_HTTP_PROVIDER + config.MORALIS_NODE_KEY + '/' + chain + '/mainnet'   
w3 = Web3(Web3.HTTPProvider(moralisProvider))
print(w3.isConnected())

header = {
  'x-api-key': config.MORALIS_API_DEF
}

ethAddress = Web3.toChecksumAddress(config.ETH_ADDRESS[8])


# 1: Normal balance
balanceWei = w3.eth.getBalance(ethAddress)
balance = Web3.fromWei(balanceWei,'ether')
print('Balance: {}'.format(balance))
print()

# 2: ERC20 Token balance
urlErc20balance = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '/erc20?chain=' + chain
response = requests.request("GET", urlErc20balance, headers=header)
resp = response.json()
print('number of tokens: ', len(resp))
for i in resp:
    tknName  = i['name']
    tknSymbol  = i['symbol']
    tknAddr = i['token_address']
    tknRawBalance = int(i['balance'])
    tknDecimals = int(i['decimals'])
    tknBalance = tknRawBalance / 10**tknDecimals
    tknLogo = i['logo']
    tknThumbnail = i['thumbnail']
    #print("{} {}, {}, {}".format(tknBalance,tknSymbol,tknName,tknAddr))
    print("%s : %-20f %10s , %s"%(tknAddr,tknBalance,tknSymbol,tknName))
print()

# 2: ERC721 Token balance
urlErc721balance = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '/nft?chain=' + chain
response = requests.request("GET", urlErc721balance, headers=header)
resp = response.json()
#print(resp)
txTotal = resp['total']
txPage = resp['page']
txPageSize = resp['page_size']
print("Total nft %s, page %s, pagesize %s"%(txTotal,txPage,txPageSize))
print('number of nft: ', len(resp['result']))
for i in resp['result']:
    tknName  = i['name']
    tknSymbol  = i['symbol']
    tknAmount  = i['amount']
    tknAddr = i['token_address']
    tknId = i['token_id']
    tknUri = i['token_uri']
    tknMetadata = i['metadata']
    tknSyncedAt = i['synced_at']
    tknContractType = i['contract_type']
    tknOwnerOf = i['owner_of']
    tknBlockNumber = i['block_number']
    tknBlockNumberMinted = i['block_number_minted']
    tknIsValid = i['is_valid']
    tknSyncing = i['syncing']
    tknFrozen = i['frozen']
    #print("{} {}, {}, {}".format(tknBalance,tknSymbol,tknName,tknAddr))
    print("%s : %s %10s , %s , id: %s"%(tknAddr,tknAmount, tknSymbol, tknName, tknId))
print()

