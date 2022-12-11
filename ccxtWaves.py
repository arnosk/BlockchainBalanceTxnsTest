"""
Created on May 06, 2022

@author: arno

Collecting prices

CCXT
"""
import ccxt

#import ccxt.async_support as ccxt
import RequestHelper


def test_ccxt():
    print(ccxt.exchanges)
    we = ccxt.wavesexchange({
        #    'apiKey': 'YOUR_PUBLIC_KEY'
        #    'secret': 'YOUR_PRIVATE_KEY',
        #    'proxy': 'https://crossorigin.me/'
    })

    markets = we.load_markets()
    print(markets)

    res = we.fetch_ticker('WAVESUSDNLP/USDN')
    print(res)


def test_api():
    # init request helper class
    req = RequestHelper.RequestHelper()
    api_url = 'https://api.waves.exchange'
    get_url = '/v1/platforms'
    resp = req.get_request_response(api_url+get_url)
    print(resp)


def __main__():
    """
    Get Waves Exchange price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    """
    test_api()


if __name__ == '__main__':
    __main__()
