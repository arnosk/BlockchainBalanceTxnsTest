'''
Created on Mar 23, 2022

@author: arno

Collecting prices

Coingecko
'''
import sys
import json
import argparse
import pandas as pd
import re
import openpyxl
import DbHelper
import RequestHelper
import config
from datetime import datetime, timezone
from dateutil import parser
from pathlib import Path


def showProgress(nr, total):
    '''
    Show progress to standard output
    '''
    sys.stdout.write("Retrieving nr {:3d} of {}\r".format(nr, total))
    sys.stdout.flush()


def convertTimestamp(ts, ms=False):
    '''
    convert timestamp to date string
    ts = timestamp in sec if ms = False
    ts = timestamp in msec if ms = True
    '''
    if ms:
        ts = int(ts/1000)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return str(dt)


def convertTimestampLastUpdated(resp):
    '''
    Convert LastUpdated field in dictonary from timestamp to date
    '''
    key = 'last_updated_at'
    for v in resp.values():
        if key in v.keys():
            ts = v[key]
            v.update({key:convertTimestamp(ts, False)})
    return resp


def writeToFile(df, outputCSV, outputXLS, extension):
    '''
    Write a dataframe to a csv file and/or excel file
    '''
    if outputCSV is not None:
        filepath = Path('%s%s.csv'%(outputCSV, extension))  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df.to_csv(filepath)
        print("File written: %s"%(filepath))

    if outputXLS is not None:
        filepath = Path('%s%s.xlsx'%(outputXLS, extension))  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df.to_excel(filepath)
        print("File written: %s"%(filepath))
    

def getPriceHistory(req, coins, currencies, date):
    '''
    Get coingecko history price
    one price per day, not suitable for tax in Netherlands on 31-12-20xx 23:00
    coins can be a list of strings or a single string
    Thumbnail image is available
    '''
    if not isinstance(coins, list):
        coins = [coins]

    # set date in correct format for url call
    dt = parser.parse(date)
    date = dt.strftime("%d-%m-%Y")
    
    prices = {}
    i = 0
    for coin in coins:
        i += 1
        showProgress(i, len(coins))
        url = "https://api.coingecko.com/api/v3/coins/"+coin+"/history?date="+date+"&localization=false"
        resp = req.getRequestResponse(url)
        #print("price of "+coin+" "+date+": ", resp['market_data']['current_price'][currency],currency)
        #print("MarketCap of "+coin+" "+date+": ", resp['market_data']['market_cap'][currency],currency)
        price = {}
        for c in currencies:
            price[c] = resp['market_data']['current_price'][c]
        prices[coin] = price
        
    return prices


def getPrice(req, coins, currencies, **kwargs):
    '''
    Get coingecko current price
    Thumbnail image is available
    '''
    # convert list to comma-separated string
    if isinstance(coins, list):
        coins = ','.join(coins)
    if isinstance(currencies, list):
        currencies = ','.join(currencies)
        
    # make parameters
    kwargs['ids'] = coins
    kwargs['vs_currencies'] = currencies
        
    url = "https://api.coingecko.com/api/v3/simple/price"
    url = req.api_url_params(url, kwargs)
    resp = req.getRequestResponse(url)
    
    # convert timestamp to date
    resp = convertTimestampLastUpdated(resp)

    return resp


def getTokenPrice(req, chain, contracts, currencies, **kwargs):
    '''
    Get coingecko current price of a token
    '''
    # convert list to comma-separated string
    if isinstance(contracts, list):
        contracts = ','.join(contracts)
    if isinstance(currencies, list):
        currencies = ','.join(currencies)
        
    # make parameters
    kwargs['contract_addresses'] = contracts
    kwargs['vs_currencies'] = currencies
        
    url = "https://api.coingecko.com/api/v3/simple/token_price/"+chain
    url = req.api_url_params(url, kwargs)
    resp = req.getRequestResponse(url)
    
    # convert timestamp to date
    resp = convertTimestampLastUpdated(resp)

    return resp


def getTokenPriceHistory(req, chain, coins_contracts, currencies, date):
    '''
    Get coingecko history price of a coin or a token
    coins_contracts can be a list of strings or a single string
    If chain = "none" or None search for a coins otherwise search for token contracts
    '''
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
    i = 0
    for coin_contract in coins_contracts:
        i += 1
        showProgress(i, len(coins_contracts))
        if (chain=='none' or chain is None): 
            url = "https://api.coingecko.com/api/v3/coins/"+coin_contract+"/market_chart/range"
        else:
            url = "https://api.coingecko.com/api/v3/coins/"+chain+"/contract/"+coin_contract+"/market_chart/range"
        url = req.api_url_params(url, params)
        resp = req.getRequestResponse(url)
        price = resp['prices']

        if (len(price) > 0):
            # convert timestamp to date
            for p in price:
                p[0] = convertTimestamp(p[0], True)
            
            prices[coin_contract] = price[0]
        else:
            # no data, set empty record
            prices[coin_contract] = ['no data', 0]
        
    return prices


def __main__():
    '''
    Get Coingecko price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str, help='Historical date to search on Coingecko', default='2022-04-01')
    argparser.add_argument('-c', '--coin', type=str, help='List of coins to search on Coingecko')
    argparser.add_argument('-oc', '--outputCSV', type=str, help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--outputXLS', type=str, help='Filename and path to the output Excel file', required=False)
    args = argparser.parse_args()
    date = args.date
    coinStr = args.coin
    outputCSV = args.outputCSV
    outputXLS = args.outputXLS
    currentDate = datetime.now().strftime("%Y%m%d-%H%M")
    print("Current date:", currentDate)
    
    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request helper class
    req = RequestHelper.RequestHelper()
    
    # check if database and table coins exists and has values
    db = DbHelper.DbHelper(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb(table_name = 'coins')
    print('Database and table coins exist: %s'%dbExist)
    
    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coinStr != None:
        coins = re.split('[;,]', coinStr)
    elif dbExist:
        coins = db.query("SELECT coingeckoid FROM coins")
        coins = [i[0] for i in coins]
    else:
        coins = ["bitcoin","litecoin","cardano","solana","ardor","proton"]
        
    curr = ["usd","eur","btc","eth"]
    chain = "binance-smart-chain"
    contracts = ["0x62858686119135cc00C4A3102b436a0eB314D402","0xacfc95585d80ab62f67a14c566c1b7a49fe91167"]
    
    print("* Current price of coins")
    price = getPrice(req, coins, curr, include_last_updated_at=True)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_current_coins_%s"%(currentDate))
    print()

    print("* History price of coins")
    price = getPriceHistory(req, coins, curr, date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(date) #("%s: %s"%(date, price))
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_%s"%(date))
    print()
 
    print("* History price of coins via market_chart")
    price = getTokenPriceHistory(req, None, coins, curr[0], date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_%s"%(date))
    print()
      
    print("* Current price of token")
    price = getTokenPrice(req, chain, contracts, curr, include_last_updated_at=True)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_current_token_%s"%(currentDate))
    print()
    
    print("* History price of token via market_chart")
    price = getTokenPriceHistory(req, chain, contracts, curr[0], date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_token_%s"%(date))
    print()


if __name__=='__main__':
    __main__()
