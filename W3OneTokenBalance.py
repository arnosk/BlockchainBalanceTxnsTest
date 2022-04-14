'''
Created on Feb 6, 2022

@author: arno

Get balance for an address of a specific token via Web3
'''
import config
from web3 import Web3
import sys



def getTokenBalance(ethAddr, tokenAddr, w3, ABI):
    '''
    Get token balance for an address via Web3
    '''
    tokenContract = w3.eth.contract(tokenAddr, abi=ABI)
    tokenBalance = tokenContract.functions.balanceOf(ethAddr).call()
    tokenName = tokenContract.functions.name().call()
    tokenSymbol = tokenContract.functions.symbol().call()
    tokenDecimals = tokenContract.functions.decimals().call()
    tokenAdjBalance = tokenBalance / 10**(tokenDecimals)
    print(str(tokenAdjBalance) + ' ' + tokenSymbol + ' (' + tokenName + ')')

def __main__():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        sys.exit("No ethereum provider, Web3 disconnected")
    
    minABI = config.ERC20_ABI
    tokenAddress = '0x7DD9c5Cba05E151C895FDe1CF355C9A1D5DA6429' # GOLEM
    ethAddress = config.ETH_ADDRESS[3]
    getTokenBalance(ethAddress, tokenAddress, w3_eth, minABI)
    
    #t = w3_eth.getAllERC20()
    #print(t)
    
if __name__=='__main__':
    __main__()

