'''
Created on Mar 23, 2022

@author: arno

Collecting prices

Coingecko
'''
import requests
import json
import sys
import time
import pandas as pd
import DbHelper
import config
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dateutil import parser
#from requests.packages.urllib3.util.retry import Retry

# Sleep and print countdown timer
# Used for a 429 response retry-after
def SleepAndPrintTime(sleepingTime):
    for i in range(sleepingTime,0,-1):
        sys.stdout.write("\r")
        sys.stdout.write("{:3d} seconds remaining.".format(i))
        sys.stdout.flush()
        time.sleep(1)
    print()

# general request url function 
# shoud be a class, with _init etc
def getRequestResponse(url, downloadFile = False):
    resp = []
    request_timeout = 120
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    try:
        while True:
            response = session.get(url, timeout=request_timeout)
            if response.status_code == 429:
                sleepTime = int(response.headers["Retry-After"])+1
                print("Retrying in %s s"%(sleepTime))
                SleepAndPrintTime(sleepTime)
            else:
                break
    except requests.exceptions.RequestException:
        raise

    if downloadFile:
        return response
    
    try:
        response.raise_for_status()
        resp = response.json()
    except Exception as e:
        raise
    
    return resp

# add params to url
# not used yet
def api_url_params(url, params, api_url_has_params=False):
    if params:
        # if api_url contains already params and there is already a '?' avoid
        # adding second '?' (api_url += '&' if '?' in api_url else '?'); causes
        # issues with request parametes (usually for endpoints with required
        # arguments passed as parameters)
        url += '&' if api_url_has_params else '?'
        for key, value in params.items():
            if type(value) == bool:
                value = str(value).lower()

            url += "{0}={1}&".format(key, value)
        url = url[:-1]
    return url

# convert timestamp to date string
# ts = timestamp in sec if ms = False
# ts = timestamp in msec if ms = True
def convertTimestamp(ts, ms=False):
    if ms:
        ts = int(ts/1000)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return str(dt)

# convert LastUpdated field in dictonary from timestamp to date
def convertTimestampLastUpdated(resp):
    key = 'last_updated_at'
    for v in resp.values():
        if key in v.keys():
            ts = v[key]
            v.update({key:convertTimestamp(ts, False)})
    return resp


# Get coingecko history price
# one price per day, not suitable for tax in Netherlands on 31-12-20xx 23:00
# Thumbnail image is available
# coins can be a list of strings or a single string
def getPriceHistory(coins, currencies, date):
    if not isinstance(coins, list):
        coins = [coins]

    # set date in correct format for url call
    dt = parser.parse(date)
    date = dt.strftime("%d-%m-%Y")
    
    prices = {}
    for coin in coins:
        url = "https://api.coingecko.com/api/v3/coins/"+coin+"/history?date="+date+"&localization=false"
        resp = getRequestResponse(url)
        #print("price of "+coin+" "+date+": ", resp['market_data']['current_price'][currency],currency)
        #print("MarketCap of "+coin+" "+date+": ", resp['market_data']['market_cap'][currency],currency)
        price = {}
        for c in currencies:
            price[c] = resp['market_data']['current_price'][c]
        prices[coin] = price
        
    return prices



# Get coingecko current price
# Thumbnail image is available
def getPrice(coins, currencies, **kwargs):
    # convert list to comma-separated string
    if isinstance(coins, list):
        coins = ','.join(coins)
    if isinstance(currencies, list):
        currencies = ','.join(currencies)
        
    # make parameters
    kwargs['ids'] = coins
    kwargs['vs_currencies'] = currencies
        
    url = "https://api.coingecko.com/api/v3/simple/price"
    url = api_url_params(url, kwargs)
    resp = getRequestResponse(url)
    
    # convert timestamp to date
    resp = convertTimestampLastUpdated(resp)

    return resp

# Get coingecko current price of a token
def getTokenPrice(chain, contracts, currencies, **kwargs):
    # convert list to comma-separated string
    if isinstance(contracts, list):
        contracts = ','.join(contracts)
    if isinstance(currencies, list):
        currencies = ','.join(currencies)
        
    # make parameters
    kwargs['contract_addresses'] = contracts
    kwargs['vs_currencies'] = currencies
        
    url = "https://api.coingecko.com/api/v3/simple/token_price/"+chain
    url = api_url_params(url, kwargs)
    resp = getRequestResponse(url)
    
    # convert timestamp to date
    resp = convertTimestampLastUpdated(resp)

    return resp

# Get coingecko history price of a coin or a token
# coins_contracts can be a list of strings or a single string
# If chain = "none" or None search for a coins otherwise search for token contracts
def getTokenPriceHistory(chain, coins_contracts, currencies, date):
    if not isinstance(coins_contracts, list):
        contracts = [coins_contracts]
    if isinstance(currencies, list):
        currencies = currencies[0]

    # convert date to unix timestamp
    dt = parser.parse(date)
    ts = int(dt.timestamp())
    
    # make parameters
    params = {}
    params['vs_currency'] = currencies
    params['from'] = ts
    params['to'] = ts+3600

    if (chain is not None):
        chain = chain.lower()
    prices = {}
    for coin_contract in coins_contracts:
        if (chain=='none' or chain is None): 
            url = "https://api.coingecko.com/api/v3/coins/"+coin_contract+"/market_chart/range"
        else:
            url = "https://api.coingecko.com/api/v3/coins/"+chain+"/contract/"+coin_contract+"/market_chart/range"
        url = api_url_params(url, params)
        resp = getRequestResponse(url)
        price = resp['prices']

        if (len(price) > 0):
            # convert timestamp to date
            for p in price:
                p[0] = convertTimestamp(p[0], True)
            
            prices[coin_contract] = price
        else:
            # no data, set empty record
            prices[coin_contract] = [['no data', 0]]
        
    return prices



def __main__():
    # Get Coingecko price history
    
    # init
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', '{:e}'.format)
    
    # check if database and table coins exists and has values
    db = DbHelper.DbHelper(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb(table_name = 'coins')
    print('Database and table coins exist: %s'%dbExist)
    
    # if yes, read the coingecko ids, if not use default
    if dbExist:
        coins = db.query("SELECT coingeckoid FROM coins")
        coins = [i[0] for i in coins]
    else:
        coins = ["bitcoin","litecoin","cardano","solana","ardor","proton"]
        
    curr = ["usd","eur","btc","eth"]
    date = "2022-04-01"
    chain = "binance-smart-chain"
    contracts = ["0x62858686119135cc00C4A3102b436a0eB314D402","0xacfc95585d80ab62f67a14c566c1b7a49fe91167"]
    
    print("* Current price of coins")
    price = getPrice(coins, curr, include_last_updated_at=True)
    df = pd.DataFrame(price).transpose()
    print(df)
    print()

    print("* History price of coins")
    price = getPriceHistory(coins, curr, date)
    df = pd.DataFrame(price).transpose()
    print(date) #("%s: %s"%(date, price))
    print(df)
    print()
 
    print("* History price of coins via market_chart")
    price = getTokenPriceHistory(None, coins, curr[0], date)
    df = pd.DataFrame(price).transpose()
    print(df)
    print()
      
    print("* Current price of token")
    price = getTokenPrice(chain, contracts, curr, include_last_updated_at=True)
    df = pd.DataFrame(price).transpose()
    print(df)
    print()
    
    print("* History price of token")
    price = getTokenPriceHistory(chain, contracts, curr[0], date)
    df = pd.DataFrame(price).transpose()
    print(df)
    print()

if __name__=='__main__':
    __main__()
