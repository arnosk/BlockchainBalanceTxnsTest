'''
Created on Mar 23, 2022

@author: arno

Collecting prices

From Cryptowatch
'''
import sys
import json
import argparse
from tracemalloc import reset_peak
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
    Show progress to standard output on one row
    '''
    print("\rRetrieving nr {:3d} of {}".format(nr, total), end='', flush=True)
    #sys.stdout.write("Retrieving nr {:3d} of {}\r".format(nr, total))
    #sys.stdout.flush()


def showAllowance(allowance):
    '''
    Show allowance data to standard output on same row
    '''
    print(allowance.rjust(80), end='', flush=True)


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

    resp = a list of dictionaries with history data from Coingecko
    '''
    keyLastUpdated = 'last_updated_at'
    for v in resp.values():
        if isinstance(v, dict):
            if keyLastUpdated in v.keys():
                ts = v[keyLastUpdated]
                v.update({keyLastUpdated:convertTimestamp(ts, False)})
    return resp


def writeToFile(df, outputCSV, outputXLS, suffix):
    '''
    Write a dataframe to a csv file and/or excel file

    df = DataFrame to write to file
    outputCSV = path + base filename for csv output file
    outputXLS = path + base filename for xlsx output file
    suffix = last part of filename

    filename CSV file = outputCSV+suffix.csv
    filename XLS file = outputXLS+suffix.xlsx
    '''
    suffix = re.sub('[:;,!@#$%^&*()]', '', suffix)
    if outputCSV is not None:
        filepath = Path('%s%s.csv'%(outputCSV, suffix))  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df.to_csv(filepath)
        print("File written: %s"%(filepath))

    if outputXLS is not None:
        filepath = Path('%s%s.xlsx'%(outputXLS, suffix))  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df.to_excel(filepath)
        print("File written: %s"%(filepath))
    

def getMarkets(req, coins, curr, strictness=0):
    '''
    Get cryptowatch markets for chosen coins

    req = instance of RequestHelper
    coins = one string or list of strings with assets for market base
    curr = one string or list of strings with assets for market quote
            "coin+curr" = pair of market
    strictness = strictly (0), loose (1) or very loose (2) search for quote
    '''
    if not isinstance(coins, list):
        coins = [coins]
    if not isinstance(curr, list):
        curr = [curr]

    markets = []
    for symbol in coins:
        url = config.CRYPTOWATCH_URL + "/assets/" + symbol
        resp = req.getRequestResponse(url)
        res = resp['result']['markets']['base']
        for r in res:
            r["coin"] = symbol
            r["curr"] = r["pair"].replace(symbol,"")

        # filter active pairs
        res = list(filter(lambda r: r['active']==True, res))

        if strictness == 0:
            # Strict/Exact filter only quote from currencies
            res_0 = list(filter(lambda r: r['curr'] in curr, res))

            # check if markets are found, else don't filter
            if len(res_0) > 0:
                res = res_0


        if strictness >= 1:
            # Loose filter only quote from currencies
            resFilter = []
            for c in curr:
                if strictness == 1:
                    # Loose (quote can have 0 or 1 character before and/or after given currency)
                    resCurr = list(filter(lambda r: re.match("^"+symbol+"\w?"+c+"\w?$", r['pair']), res))
                else:
                    # Very Loose (quote must contain given currency)
                    resCurr = list(filter(lambda r: c in r['curr'], res))
                resFilter.extend(resCurr)
            res = resFilter
        
        markets.extend(res)
    return markets


def getPrice(req, markets):
    '''
    Get Cryptowatch current price
    
    req = instance of RequestHelper
    markets = all market pairs and exchange to get price
    '''
    prices = []
    i = 0
    currentDate = datetime.now().strftime("%Y-%m-%d %H:%M")
    for market in markets:
        i += 1
        showProgress(i, len(markets))

        urlList = market["route"] + "/summary"
        resp = req.getRequestResponse(urlList)
        res = [{'exchange':market["exchange"],
                'pair':market["pair"],
                'coin':market["coin"],
                'curr':market["curr"],
                'price':resp['result']['price']['last'],
                'volume':resp['result']['volume'],
                'date':currentDate}]
        
        if "allowance" in resp:
            allowance = resp['allowance']
            showAllowance(allowance)
        
        prices.extend(res)

    return prices


def getTokenPriceHistory(req, markets, date):
    '''
    Get coingecko history price of a coin or a token
    coins_contracts can be a list of strings or a single string
    If chain = "none" or None search for a coins otherwise search for token contracts

    req = instance of RequestHelper
    markets = all market pairs and exchange to get price
    date = historical date 
    '''
    # convert date to unix timestamp
    dt = parser.parse(date) # local time
    #dt = dt.replace(tzinfo=tz.UTC) # set as UTC time
    ts = int(dt.timestamp())
    
    # make parameters
    params = {}
    params['after'] = ts
    params['before'] = ts
    params['periods'] = 3600

    prices = []
    i = 0
    for market in markets:
        i += 1
        showProgress(i, len(markets))

        urlList = market["route"] + "/ohlc?periods=3600&after=%s&before=%s"%(ts,ts) 
        urlList = market["route"] + "/ohlc"
        urlList = req.api_url_params(urlList, params)
        resp = req.getRequestResponse(urlList)
        if len(resp['result']['3600']) > 0:
            res = [{'exchange':market["exchange"],
                    'pair':market["pair"],
                    'coin':market["coin"],
                    'curr':market["curr"],
                    'open':resp['result']['3600'][0][1],
                    'close':resp['result']['3600'][0][4],
                    'volume':resp['result']['3600'][0][5],
                    'date':convertTimestamp(resp['result']['3600'][0][0])}]
        else:
            res = [{'exchange':market["exchange"],
                    'pair':market["pair"],
                    'coin':market["coin"],
                    'curr':market["curr"],
                    'open':"no data",
                    'close':"no data",
                    'volume':"no data",
                    'date':"no data"}]
        prices.extend(res)
    return prices


def __main__():
    '''
    Get Cryptowatch price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str, help='Historical date to search on Cryptowatch', default='2022-05-01')
    argparser.add_argument('-c', '--coin', type=str, help='List of coins to search on Cryptowatch')
    argparser.add_argument('-oc', '--outputCSV', type=str, help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--outputXLS', type=str, help='Filename and path to the output Excel file', required=False)
    args = argparser.parse_args()
    date = args.date
    coinStr = args.coin
    outputCSV = args.outputCSV
    outputXLS = args.outputXLS
    currentDate = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("Current date:", currentDate)
    
    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request helper class
    req = RequestHelper.RequestHelper()
    req.updateHeader({'X-CW-API-Key': config.CRYPTOWATCH_API})
    
    # check if database and table coins exists and has values
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb(table_name = db.table['coinCryptowatch'])
    print('Database and table coins exist: %s'%dbExist)
    
    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coinStr != None:
        coins = re.split('[;,]', coinStr)
    elif dbExist:
        coins = db.query("SELECT symbol FROM {}".format(db.table['coinCryptowatch']))
        coins = [i[0] for i in coins]
    else:
        coins = ["btc","ltc","ada","sol","ardr","xpr"]
        
    curr = ["usd","btc","eth"]

    markets = getMarkets(req, coins, curr)

    resdf = pd.DataFrame(markets)
    resdf_print = resdf.drop('route', axis=1)
    print(resdf_print)
    print()

    print("* Current price of coins")
    price = getPrice(req, markets)
    df = pd.DataFrame(price) #.transpose()
    df = df.sort_values(by=["pair"], key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_current_coins_%s"%(currentDate))
    print()

    print("* History price of coins via market_chart")
    price = getTokenPriceHistory(req, markets, date)
    df = pd.DataFrame(price) #.transpose()
    df = df.sort_values(by=["pair"], key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_%s"%(date))
    print()
      

if __name__=='__main__':
    __main__()
