'''
Created on Feb 12, 2022

@author: arno

'''

from web3 import Web3
import time
import config
import sys

def handle_event(event):
    print(event)

def log_loop(event_filter, poll_interval):
    while True:
        #for event in event_filter.get_new_entries():
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)
        
def main():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER2))
    if (not w3_eth.isConnected()):
        sys.exit("No ethereum provider, Web3 disconnected")
    
    #block_filter = w3_eth.eth.filter('latest')
    #log_loop(block_filter, 2)
    ethAddress = config.ETH_ADDRESS[3]
    tokenAddress = '0x7DD9c5Cba05E151C895FDe1CF355C9A1D5DA6429' # GOLEM

    block_filter = w3_eth.eth.filter({"fromBlock":1, "toBlock":"latest", "address": tokenAddress})
    log_loop(block_filter, 2)
    
if __name__ == '__main__':
    main()
    