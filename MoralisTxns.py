'''
Created on Feb 18, 2022

@author: arno

Get all transactions of an address with Moralis

'''
from web3 import Web3
import json
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
urlErc20balance = 'https://deep-index.moralis.io/api/v2/'+ ethAddress + '/erc20?chain=' + chain
headers = {
  'x-api-key': config.MORALIS_API_DEF
}

response = w3.eth.getBalance(ethAddress)
#resp = response.json()
print(response)

