'''
Created on Feb 6, 2022

@author: arno

Get native balance of an address on the ETH and BSC chain
Through a Web3 HTTP provider

'''
import config
from web3 import Web3
import sys


def __main__():
    '''
    Get native balance of an address on the ETH and BSC chain
    Through a Web3 HTTP provider
    '''
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    w3_bsc = Web3(Web3.HTTPProvider(config.BSC_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        sys.exit("No ethereum provider, Web3 disconnected")
    
    if (not w3_bsc.isConnected()):
        sys.exit("No binance smart chain provider, Web3 disconnected")
    
    lstAddrEth = config.ETH_ADDRESS
    
    for addr in lstAddrEth:
        addrh = Web3.toChecksumAddress(addr)
    
        balanceETHWei = w3_eth.eth.get_balance(addrh)
        balanceETH = Web3.fromWei(balanceETHWei,'ether')
        balanceBNBWei = w3_bsc.eth.get_balance(addrh)
        balanceBNB = Web3.fromWei(balanceBNBWei,'ether')
    
        print('Address: ' + addrh)
        print('ETH Balance: ' + str(balanceETH))
        print('BNB Balance: ' + str(balanceBNB))
        print()

if __name__=='__main__':
    __main__()

