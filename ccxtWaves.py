'''
Created on May 06, 2022

@author: arno

Collecting prices

CCXT
'''
import ccxt
#import ccxt.async_support as ccxt
import RequestHelper


def testCcxt():
    print(ccxt.exchanges)
    we = ccxt.wavesexchange({
    #    'apiKey': 'YOUR_PUBLIC_KEY'
    #    'secret': 'YOUR_PRIVATE_KEY',
    #    'proxy': 'https://crossorigin.me/'
    })

    markets = we.load_markets()
    print(markets)

def testApi():
    # init request helper class
    req = RequestHelper.RequestHelper()
    apiUrl = 'https://api.waves.exchange'
    getUrl = '/v1/platforms'
    resp = req.getRequestResponse(apiUrl+getUrl)
    print(resp)

def __main__():
    '''
    Get Waves Exchange price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    '''
    testApi()


if __name__=='__main__':
    __main__()
