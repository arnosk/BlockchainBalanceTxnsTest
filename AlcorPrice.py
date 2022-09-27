'''
Created on Aug 31, 2022

@author: arno

Collecting prices

Alcor
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
    print("\rRetrieving nr {:3d} of {}".format(nr, total), end='', flush=True)
    #sys.stdout.write("Retrieving nr {:3d} of {}\r".format(nr, total))
    #sys.stdout.flush()


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

    resp = a list of dictionaries with history data from alcor
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


def addCoinSymbol(db, prices:dict):
    '''
    Adds a new column with the symbol name
    Symbol name is retrieved from the database

    prices = a dictionary with coin id from Alcor and prices
    '''
    coins = db.query("SELECT chain, alcorid, base, quote FROM {}".format(db.table['coinAlcor']))
    for priceKey, priceVal in prices.items():
        print(priceVal, priceKey)
        if isinstance(priceVal, dict):
            for coinKey, coinVal in coins:
                if priceKey == coinKey:
                    priceVal["symbol"] = coinVal
        if isinstance(priceVal, list):
            for coinKey, coinVal in coins:
                if priceKey == coinKey:
                    priceVal.append(coinVal)

    return prices


def getPriceHistory(req, coins, curr, date):
    '''
    Get alcor history price
    one price per day, not suitable for tax in Netherlands on 31-12-20xx 23:00
    coins can be a list of strings or a single string
    Thumbnail image is available

    req = instance of RequestHelper
    coins = one string or list of strings with assets for market base
    curr = one string or list of strings with assets for market quote
    date = historical date 
    '''
    if not isinstance(coins, list):
        coins = [coins]
    if not isinstance(curr, list):
        curr = [curr]

    # set date in correct format for url call
    dt = parser.parse(date)
    date = dt.strftime("%d-%m-%Y")
    
    prices = {}
    i = 0
    for coin in coins:
        i += 1
        showProgress(i, len(coins))
        url = "https://api.alcor.com/api/v3/coins/"+coin+"/history?date="+date+"&localization=false"
        resp = req.getRequestResponse(url)
        market_dataExist = "market_data" in resp
        #print("coin:", coin)
        #print("price of "+coin+" "+date+": ", resp['market_data']['current_price'][currency],currency)
        #print("MarketCap of "+coin+" "+date+": ", resp['market_data']['market_cap'][currency],currency)
        # init price
        price = {}
        if resp['status_code'] == "error":
            # got no status from request, must be an error
            for c in curr:
                price[c] = resp['error']
        else:
            price["symbol"] = resp['symbol']
            for c in curr:
                price[c] = "no data"

            for c in curr:
                if market_dataExist:
                    if c in resp['market_data']['current_price']:
                        price[c] = resp['market_data']['current_price'][c]

        prices[coin] = price
        
    return prices


def getPrice(req, coins, **kwargs):
    '''
    Get alcor current price
    
    req = instance of RequestHelper
    coins = list of market id and chain
    **kwargs = extra arguments in url 
    '''
    # refactor coins list into dict a list of id's (value) per chain (key)
    coinsrch = {}
    for item in coins:
        key_chain = item[0]
        val_coin = item[1]
        coinsrch.setdefault(key_chain,[]).append(val_coin)
    
    # get all market data per chain, and then search through that list for the id's
    prices = {}
    for key_chain, val_coins in coinsrch.items():
        url = "https://{}.alcor.exchange/api/markets".format(key_chain)
        url = req.api_url_params(url, kwargs)
        resp = req.getRequestResponse(url)
        
        # remove status_code from dictionary
        #resp.pop("status_code")

        #res_coins = []
        for item in resp['result']:
            if item['id'] in val_coins:
                #res_coins.append(item)
                prices.setdefault(item['quote_token']['symbol']['name'], []).append(item['last_price'])
                prices.setdefault(item['quote_token']['symbol']['name'], []).append(item['base_token']['symbol']['name'])
        
        #prices.append(res_coins)

    # convert timestamp to date
    #resp = convertTimestampLastUpdated(resp)
    return prices


def getTokenPrice(req, contracts, **kwargs):
    '''
    Get alcor current price of a token

    req = instance of RequestHelper
    coins = one string or list of strings with token contracts for market base
    **kwargs = extra arguments in url 
    '''
    # convert list to comma-separated string
    if isinstance(contracts, list):
        contracts = ','.join(contracts)
    if isinstance(curr, list):
        curr = ','.join(curr)
        
    # make parameters
    kwargs['contract_addresses'] = contracts
    kwargs['vs_currencies'] = curr
    kwargs['include_last_updated_at'] = True
        
    url = "https://api.alcor.com/api/v3/simple/token_price/"+chain
    url = req.api_url_params(url, kwargs)
    resp = req.getRequestResponse(url)

    # remove status_code from dictionary
    resp.pop("status_code")

    # convert timestamp to date
    resp = convertTimestampLastUpdated(resp)

    return resp


def getTokenPriceHistory(req, coins, date):
    '''
    Get alcor history price of a coin or a token
    coins_contracts can be a list of strings or a single string
    If chain = "none" or None search for a coins otherwise search for token contracts

    req = instance of RequestHelper
    coins = one string or list of strings with assets or token contracts for market base
    date = historical date 
    '''
    if not isinstance(coins, list):
        contracts = [coins]
    if isinstance(curr, list):
        curr = curr[0]

    # convert date to unix timestamp
    dt = parser.parse(date) # local time
    ts = int(dt.timestamp())
    
    # make parameters
    params = {}
    params['vs_currency'] = curr
    params['from'] = ts
    params['to'] = ts+3600

    if (chain is not None):
        chain = chain.lower()

    prices = {}
    i = 0
    for coin in coins:
        i += 1
        showProgress(i, len(coins))
        if (chain=='none' or chain is None): 
            url = "https://api.alcor.com/api/v3/coins/"+coin+"/market_chart/range"
        else:
            url = "https://api.alcor.com/api/v3/coins/"+chain+"/contract/"+coin+"/market_chart/range"
        url = req.api_url_params(url, params)
        resp = req.getRequestResponse(url)

        if resp['status_code'] == "error":
            # got no status from request, must be an error
            prices[coin] = [resp['error'], 0]
        else:
            price = resp['prices']
            if (len(price) > 0):
                # convert timestamp to date
                for p in price:
                    p[0] = convertTimestamp(p[0], True)
                
                prices[coin] = price[0]
            else:
                # no data, set empty record
                prices[coin] = ['no data', 0]
        
    return prices


def __main__():
    '''
    Get Alcor price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str, help='Historical date to search on Alcor', default='2022-05-01')
    argparser.add_argument('-c', '--coin', type=str, help='List of coins to search on Alcor')
    argparser.add_argument('-ch', '--chain', type=str, help='Chain to search on Alcor')
    argparser.add_argument('-oc', '--outputCSV', type=str, help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--outputXLS', type=str, help='Filename and path to the output Excel file', required=False)
    args = argparser.parse_args()
    date = args.date
    coinStr = args.coin
    chainStr = args.chain
    outputCSV = args.outputCSV
    outputXLS = args.outputXLS
    currentDate = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("Current date:", currentDate)
    
    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request helper class
    req = RequestHelper.RequestHelper()
    
    # check if database and table coins exists and has values
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb(table_name = db.table['coinAlcor'])
    print('Database and table coins exist: %s'%dbExist)
    
    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coinStr != None:
        coins = re.split('[;,]', coinStr)
        chain = chainStr if chainStr != None else 'proton'
        coins = [[chain, i] for i in coins]
    elif dbExist:
        coins = db.query("SELECT chain, alcorid FROM {}".format(db.table['coinAlcor']))
        coins = [[i[0], i[1]] for i in coins]
    else:
        coins = [['proton', 157], ['wax', 158], ['proton', 13], ['wax', 67], ['proton', 5], ['eos', 2], ['telos', 34], ['proton', 96]]

    # For testing
    #coins = [['proton', 157], ['wax', 158], ['proton', 13], ['wax', 67], ['proton', 5], ['eos', 2], ['telos', 34], ['proton', 96]]

    print("* Current price of coins")
    price = getPrice(req, coins)
    #if dbExist:
    #    price = addCoinSymbol(db, price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_current_coins_%s"%(currentDate))
    print()

    print("* History price of coins")
    price = getPriceHistory(req, coins, date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(date)
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_%s"%(date))
    print()
 
    print("* History price of coins via market_chart")
    price = getTokenPriceHistory(req, coins, date)
    if dbExist:
        price = addCoinSymbol(db, price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_%s"%(date))
    print()


if __name__=='__main__':
    __main__()
