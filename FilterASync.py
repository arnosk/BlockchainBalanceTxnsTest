'''
Created on Feb 12, 2022

@author: arno
'''
from web3 import Web3
import config
import asyncio

def handle_event(event):
    print(event)

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)
        
def main():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        print("No ethereum provider, Web3 disconnected")
        exit()
    
    block_filter = w3_eth.eth.filter('latest')
    tx_filter = w3_eth.eth.filter('pending')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(block_filter, 2),
                log_loop(tx_filter, 2)))
    finally:
        loop.close()
    
if __name__ == '__main__':
    main()
    