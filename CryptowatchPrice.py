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
import json
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
    allowanceStr = json.dumps(allowance)[1:50]
    print("\r"+allowanceStr.rjust(80), end='', flush=True)


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
    outputCSV = base filename for csv output file
    outputXLS = base filename for xlsx output file
    suffix = last part of filename

    filename CSV file = config.OUTPUT_PATH+outputCSV+suffix.csv
    filename XLS file = config.OUTPUT_PATH+outputXLS+suffix.xlsx
    '''
    suffix = re.sub('[:;,!@#$%^&*()]', '', suffix)
    outputPath = config.OUTPUT_PATH
    if outputPath != '':
        outputPath = outputPath + '\\'

    if outputCSV is not None:
        filepath = Path('%s%s%s.csv'%(outputPath, outputCSV, suffix))  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df.to_csv(filepath)
        print("File written: %s"%(filepath))

    if outputXLS is not None:
        filepath = Path('%s%s%s.xlsx'%(outputPath, outputXLS, suffix))  
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

    if coin does not exist as base, try as quote
    '''
    if not isinstance(coins, list):
        coins = [coins]
    if not isinstance(curr, list):
        curr = [curr]

    markets = []
    for symbol in coins:
        url = config.CRYPTOWATCH_URL + "/assets/" + symbol
        resp = req.getRequestResponse(url)

        if resp['status_code'] == 200:
            #             res = resp['result']['markets']['base']
            res = resp['result']['markets']

            # check if base or quote exists in result
            if 'base' in res:
                res = res['base']
                for r in res:
                    r["coin"] = symbol
                    r["curr"] = r["pair"].replace(symbol,"")
            elif 'quote' in res:
                res = res['quote']
                for r in res:
                    r["curr"] = symbol
                    r["coin"] = r["pair"].replace(symbol,"")
            else:
                print('Error, no quote or base in requested market symbol: ', symbol)

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

        else:
            res = [{'active':False,
                    'coin':symbol,
                    'pair':'error',
                    'curr':'error',
                    'volume':'error',
                    'error':resp['error'], 
                    'route':''}]
        
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

        if not 'error' in market:
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

        if not 'error' in market:
            urlList = market["route"] + "/ohlc?periods=3600&after=%s&before=%s"%(ts,ts) 
            urlList = market["route"] + "/ohlc"
            urlList = req.api_url_params(urlList, params)
            resp = req.getRequestResponse(urlList)
            if resp['status_code'] == "error":
                # got no status from request, must be an error
                res = [{'exchange':market["exchange"],
                        'pair':market["pair"],
                        'coin':market["coin"],
                        'curr':market["curr"],
                        'open':resp['error'],
                        'close':"no data",
                        'volume':"no data",
                        'date':"no data"}]
            else:
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

            if "allowance" in resp:
                allowance = resp['allowance']
                showAllowance(allowance)
        
    return prices


def filterMarketPairOnVolume(prices, maxMarketsPerPair):
    '''
    Filter the price data with same market pair. 
    Only the exchanges with the greatest volume for a market pair will stay
    
    prices = all prices of market pairs and exchange with volume column
    maxMarketsPerPair = maximum rows of the same pair on different exchanges
                        when 0, no filtering will be done and all markets are shown
    '''
    # do nothing
    if maxMarketsPerPair <= 0 or len(prices) == 0:
        return prices

    # make new dictionary, with pair as key, list of price as value
    pricePerPair = {}
    for price in prices:
        if "volume" in price:
            pair = price["pair"]
            if not pair in pricePerPair.keys():
                pricePerPair[pair] = []
            pricePerPair[pair].append(price)
    
    # make new list of prices with max markets per pair
    newprices = []
    for valPrices in pricePerPair.values():
        # sort list of dictionaries of same pair on volume
        valPricesSorted = sorted(valPrices, 
                key=lambda d: -1 if isinstance(d['volume'],str) else d['volume'], 
                reverse=True)

        # get the first x price items
        for i in range(0, min(len(valPricesSorted), maxMarketsPerPair)):
            newprices.append(valPricesSorted[i])

    return newprices


def __main__():
    '''
    Get Cryptowatch price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    - max markets per pair, 0 is no maximum
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str, help='Historical date to search on Cryptowatch', default='2022-05-01')
    argparser.add_argument('-c', '--coin', type=str, help='List of coins to search on Cryptowatch')
    argparser.add_argument('-oc', '--outputCSV', type=str, help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--outputXLS', type=str, help='Filename and path to the output Excel file', required=False)
    argparser.add_argument('-mp', '--maxMarketsPerPair', type=int, help='Maximum markets per pair, 0 is no max', default=2)
    args = argparser.parse_args()
    date = args.date
    coinStr = args.coin
    outputCSV = args.outputCSV
    outputXLS = args.outputXLS
    maxMarketsPerPair = args.maxMarketsPerPair
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

    print()
    print("* Available markets of coins")
    markets = getMarkets(req, coins, curr)
    resdf = pd.DataFrame(markets)
    resdf_print = resdf.drop('route', axis=1)
    print(resdf_print)
    print()

    print("* Current price of coins")
    price = getPrice(req, markets)
    price = filterMarketPairOnVolume(price, maxMarketsPerPair)
    print()
    if len(price) > 0:
        df = pd.DataFrame(price) #.transpose()
        df = df.sort_values(by=["pair"], key=lambda x: x.str.lower())
        print(df)
        writeToFile(df, outputCSV, outputXLS, "_current_coins_%s"%(currentDate))
    else:
        print('No data')
    print()

    print("* History price of coins via market_chart")
    price = getTokenPriceHistory(req, markets, date)
    price = filterMarketPairOnVolume(price, maxMarketsPerPair)
    print()
    if len(price) > 0:
        df = pd.DataFrame(price) #.transpose()
        df = df.sort_values(by=["pair"], key=lambda x: x.str.lower())
        print(df)
        writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_%s"%(date))
    else:
        print('No data')
    print()
      

if __name__=='__main__':
    __main__()
