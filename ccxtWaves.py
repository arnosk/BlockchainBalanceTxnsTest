'''
Created on May 06, 2022

@author: arno

Collecting prices

CCXT
'''
import ccxt
#import ccxt.async_support as ccxt

def __main__():
    '''
    Get Waves Exchange price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    '''
    print(ccxt.exchanges)
    we = ccxt.wavesexchange({
    #    'apiKey': 'YOUR_PUBLIC_KEY'
    #    'secret': 'YOUR_PRIVATE_KEY',
    #    'proxy': 'https://crossorigin.me/'
    })

    markets = we.load_markets()
    print(markets)


if __name__=='__main__':
    __main__()
