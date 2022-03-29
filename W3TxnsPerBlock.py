'''
Created on Feb 11, 2022

@author: arno

Get all transactions of an eth address by fetching all blocks
through Web3 hhtp provider
Is very slow
result is written to json file

same as W3TxnsPerBlockArgs but without args example
'''
#!/usr/bin/python
import sys
import json
import config

from web3 import Web3
from hexbytes import HexBytes

# Exports transactions to a JSON file where each line
# contains the data returned from the JSONRPC interface

# The following script fetches blocks and filters transactions to/from the given
# address. You can modify it to suit your needs.



def tx_to_json(tx):
    result = {}
    for key, val in tx.items():
        if isinstance(val, HexBytes):
            result[key] = val.hex()
        else:
            result[key] = val

    return json.dumps(result)

def __main__():
    w3_eth = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER))
    w3_bsc = Web3(Web3.HTTPProvider(config.BSC_HTTP_PROVIDER))
    if (not w3_eth.isConnected()):
        sys.exit("No ethereum provider, Web3 disconnected")
    
    if (not w3_bsc.isConnected()):
        sys.exit("No binance smart chain provider, Web3 disconnected")
    
    w3 = w3_eth
    
    start_block = 1
    end_block = w3.eth.blockNumber

    address_lowercase = config.ETH_ADDRESS[3].lower()

    ofile = open('transactions.json', 'w')

    for idx in range(start_block, end_block):
        print('Fetching block %d, remaining: %d, progress: %d%%'%(
            idx, (end_block-idx), 100*(idx-start_block)/(end_block-start_block)))

        block = w3.eth.getBlock(idx, full_transactions=True)

        for tx in block.transactions:
            if tx['to']:
                to_matches = tx['to'].lower() == address_lowercase
            else:
                to_matches = False

            if tx['from']:
                from_matches = tx['from'].lower() == address_lowercase
            else:
                from_matches = False

            if to_matches or from_matches:
                print('Found transaction with hash %s'%tx['hash'].hex())
                ofile.write(tx_to_json(tx)+'\n')
                ofile.flush()

if __name__ == '__main__':
    __main__()
