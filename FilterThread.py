'''
Created on Feb 12, 2022

@author: arno
'''
from web3 import Web3
from threading import Thread
import time
import config
import sys

def handle_event(event):
    print(event)

def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)
        
def main():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        sys.exit("No ethereum provider, Web3 disconnected")
    
    block_filter = w3_eth.eth.filter('latest')
    worker = Thread(target=log_loop, args=(block_filter, 5), daemon=True)
    worker.start()
    
    while True:
        time.sleep(50)
    
if __name__ == '__main__':
    main()
    