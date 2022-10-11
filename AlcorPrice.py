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
import copy
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


def addCoinSymbol(db, prices:dict):
    '''
    Adds a new column with the symbol name
    Symbol name is retrieved from the database

    prices = a dictionary with coin id from Alcor and prices
    '''
    coins = db.query("SELECT alcorid, quote FROM {}".format(db.table['coinAlcor']))
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
        url = config.ALCOR_URL.replace('?', key_chain) + "/markets"
        url = req.api_url_params(url, kwargs)
        resp = req.getRequestResponse(url)
        
        # remove status_code from dictionary
        #resp.pop("status_code")

        #res_coins = []
        for item in resp['result']:
            if item['id'] in val_coins:
                #res_coins.append(item)
                prices.setdefault(item['quote_token']['str'], []).append(item['last_price'])
                prices.setdefault(item['quote_token']['str'], []).append(item['base_token']['str'])
        
        #prices.append(res_coins)

    # convert timestamp to date
    #resp = convertTimestampLastUpdated(resp)
    return prices


def getPriceHistoryMarketChart(req, coins, date):
    '''
    Get alcor history price of a coin via market chart data
    
    req = instance of RequestHelper
    coins = list of [chain, coinid] with assets or token contracts for market base
    date = historical date 
    '''

    # convert date to unix timestamp
    dt = parser.parse(date) # local time
    ts = int(dt.timestamp())
    
    # make parameters
    params = {}
    params['resolution'] = 60
    params['from'] = ts #-3600
    params['to'] = ts #+3600

    prices = {}
    i = 0
    for coin in coins:
        i += 1
        showProgress(i, len(coins))

        url = config.ALCOR_URL.replace('?', coin[0]) + "/markets/{}/charts".format(coin[1])
        paramsTry = copy.deepcopy(params)
        nrTry = 1

        # get coin name
        if len(coin) > 2:
            coinName = coin[2]
            coinBase = coin[3]
        else:
            coinName = str(coin[1]).zfill(3)
            coinBase = '-'

        # try to get history data from and to specific date
        # increase time range until data is found
        while True: 
            urlTry = req.api_url_params(url, paramsTry)
            resp = req.getRequestResponse(urlTry)

            # check for correct result
            if resp['status_code'] == "error":
                # got no status from request, must be an error
                prices[coinName] = [resp['error'], 0, coinBase]
                break

            else:
                result = resp['result']

                if len(result) > 0:
                    # select result with timestamp nearest to desired date ts
                    resultMinimal = {}
                    timeDiffMinimal = -1
                    for res in result:
                        timeDiff = abs(ts*1000 - res['time'])
                        if timeDiff < timeDiffMinimal or timeDiffMinimal == -1:
                            # remember record
                            resultMinimal = res
                            timeDiffMinimal = timeDiff

                    # convert timestamp to date
                    resultMinimal['time'] = convertTimestamp(resultMinimal['time'], True)
                    
                    # take first record?
                    prices[coinName] = [resultMinimal['time'], resultMinimal['open'], coinBase]
                    break

                elif nrTry > 10:
                    # if too many retries for date ranges, stop
                    prices[coinName] = ['no data', 0, coinBase]
                    break

                else:
                    # retry same coin with new date range
                    paramsTry['from'] -= 2**nrTry * 3600
                    paramsTry['to'] += 2**nrTry * 3600
                    nrTry += 1

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
        coins = db.query("SELECT chain, alcorid, quote, base FROM {}".format(db.table['coinAlcor']))
        coins = [[i[0], i[1], i[2], i[3]] for i in coins]
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

    print("* History price of coins via market_chart")
    price = getPriceHistoryMarketChart(req, coins, date)
    #if dbExist:
    #    price = addCoinSymbol(db, price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    writeToFile(df, outputCSV, outputXLS, "_hist_marketchart_%s"%(date))
    print()


if __name__=='__main__':
    __main__()
