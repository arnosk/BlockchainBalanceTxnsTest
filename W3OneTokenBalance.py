"""
Created on Feb 6, 2022

@author: arno

Get balance for an address of a specific token via Web3
"""
import config
from web3 import Web3
import sys



def get_token_balance(eth_addr, token_addr, w3, fabi):
    """Get token balance for an address via Web3
    """
    token_contract = w3.eth.contract(token_addr, abi=fabi)
    token_balance = token_contract.functions.balanceOf(eth_addr).call()
    token_name = token_contract.functions.name().call()
    token_symbol = token_contract.functions.symbol().call()
    token_decimals = token_contract.functions.decimals().call()
    token_adj_balance = token_balance / 10**(token_decimals)
    print(str(token_adj_balance) + ' ' + token_symbol + ' (' + token_name + ')')

def __main__():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        sys.exit('No ethereum provider, Web3 disconnected')
    
    min_abi = config.ERC20_ABI
    token_address = '0x7DD9c5Cba05E151C895FDe1CF355C9A1D5DA6429' # GOLEM
    eth_address = config.ETH_ADDRESS[3]
    get_token_balance(eth_address, token_address, w3_eth, min_abi)
    
    #t = w3_eth.getAllERC20()
    #print(t)
    
if __name__=='__main__':
    __main__()

