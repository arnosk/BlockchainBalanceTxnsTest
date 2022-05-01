'''
Created on Apr 23, 2022

@author: arno

Cryptowat.ch test 
'''
import config
import RequestHelper
import DbHelper
import pandas as pd
import argparse
import sys
import re
from datetime import datetime, timezone
from dateutil import parser, tz


def searchId(searchStr, assets):
    '''
    Search f0r coin in list of all assets

    searchStr = string to search in assets
    assets = list of assets from Cryptowatch
    '''
    s = (searchStr).lower()
    resCoins = [item for item in assets \
                if (re.match(s, item["name"].lower()) or \
                    re.match(s, item["symbol"].lower()) )]
    return resCoins


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


def inputNumber(message: str, minimal: int = 1, maximum: int = 1):
    '''
    UI for asking row number

    message = string for printing on screen to ask for user input
    minimal = minimal allowed integer
    maximum = maximum allowed integer
    '''
    while True:
        userInput = input(message)
        userInput = userInput.lower()
        if (userInput == "n" or userInput == "new"):
            userInput = "n"
        elif (userInput == "q" or userInput == "quit"):
            sys.exit("Exiting")
        else:
            try:
                userInput = int(userInput)       
            except ValueError:
                print("No correct input! Try again.")
                continue
            else:
                if (userInput < minimal or userInput > maximum):
                    print("No correct row number! Try again.")
                    continue
        return userInput 
        break


def search(req, db, coinSearch, assets):
    '''
    Search coins in own database (if table exists)
    Show the results
    
    Search coins from Cryptowatch assets (already in assets)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists

    req = instance of RequestHelper
    db = instance of DbHelperArko
    coinSearch = string to search in assets
    assets = list of string with assets from Cryptowatch
    '''
    pd.set_option("display.max_colwidth", 20)

    # Check if coin already in database and add to search result on row 0
    dbResult = []
    if db.chkTable['coins2']:
        coinSearchStr = "%{}%".format(coinSearch)
        dbResult = db.query("SELECT * FROM coins2 WHERE symbol like ? or name like ?", \
                            (coinSearchStr, coinSearchStr))
        if (len(dbResult) > 0):
            dbResultdf = pd.DataFrame(dbResult)
            print("Search in database:")
            print(dbResultdf)

    # Do search on cryptowatch assets in memory
    cwResultCoin = searchId(coinSearch, assets)
    if (len(cwResultCoin) > 0):
        cwResultCoindf = pd.DataFrame(cwResultCoin)
        cwResultCoindf_print = cwResultCoindf.drop('route', axis=1)
        print("Search from cryptowatch:")
        print(cwResultCoindf_print)
    else:
        print("Coin not found")
    
    # ask user which row is the correct answer
    userInput = inputNumber("Select correct coin to store in database, or (N)ew search, or (Q)uit: ",
                            0, len(cwResultCoin)-1)

    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit
    if userInput == "n":
        print("New search")
    elif userInput == "q":
        sys.exit("Exiting")
    else:
        # coin selected add to
        print("Number chosen = %s"%userInput)
        coin = cwResultCoin[userInput]
        print(coin)

        # search markets for chosen asset
        urlList = config.CRYPTOWATCH_URL + "/assets/" + coin["symbol"]
        resp = req.getRequestResponse(urlList)
        print(resp)
        cwResultMarket = resp['result']['markets']['base']
        cwResultMarketdf = pd.DataFrame(cwResultMarket)
        cwResultMarketdf_print = cwResultMarketdf.drop('route', axis=1)
        print(cwResultMarketdf_print)

        # ask user which row is the correct answer
        userInput = inputNumber("Select market, or (N)ew search, or (Q)uit: ",
                                0, len(cwResultMarket)-1)

        if userInput == "n":
            print("New search")
        elif userInput == "q":
            sys.exit("Exiting")
        else:
            # market selected add to
            print("Number chosen = %s"%userInput)
            market = cwResultMarket[userInput]
            print(market)

            # convert date to unix timestamp
            date = '2022-04-01'
            dt = parser.parse(date) # local time
            #dt = dt.replace(tzinfo=tz.UTC) # set as UTC time
            ts = int(dt.timestamp())

            # summary of chosen market
            currentDate = datetime.now().strftime("%Y-%m-%d %H:%M")
            print()
            print("Current price: ", currentDate)
            urlList = market["route"] + "/summary"
            resp = req.getRequestResponse(urlList)
            res = [{'exchange':market["exchange"],
                    'pair':market["pair"],
                    'price':resp['result']['price']['last'],
                    'volume':resp['result']['volume'],
                    'date':currentDate}]
            df = pd.DataFrame(res)
            print(df)

            # ohlc of chosen market
            print()
            print("History price: ", date)
            urlList = market["route"] + "/ohlc?periods=3600&after=%s&before=%s"%(ts,ts) 
            resp = req.getRequestResponse(urlList)
            if len(resp['result']['3600']) > 0:
                res = [{'exchange':market["exchange"],
                        'pair':market["pair"],
                        'open':resp['result']['3600'][0][1],
                        'close':resp['result']['3600'][0][4],
                        'volume':resp['result']['3600'][0][5],
                        'date':convertTimestamp(resp['result']['3600'][0][0])}]
                df = pd.DataFrame(res)
                print(df)
            else:
                print("no data")
            print()
        

def __main__():
    '''
    Get Cryptowatch search assets and then markets

    Arguments:
    - coin to search
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    args = argparser.parse_args()
    coinSearch = args.coin

    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb()
    print("Database exists:", dbExist)
    print("Database exists:", db.hasConnection())
    dbTableExist = db.checkDb(table_name = 'coins2')
    print("Table coins exist:", dbTableExist)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request session
    req = RequestHelper.RequestHelper()
    req.updateHeader({'X-CW-API-Key': config.CRYPTOWATCH_API})

    # get all assets from cryptowatch
    urlList = config.CRYPTOWATCH_URL + "/assets"
    resp = req.getRequestResponse(urlList)
    coinassets = resp['result']
    
    while coinassets != None:
        if coinSearch == None:
            coinSearch = input("Search for coin: ")
        search(req, db, coinSearch, coinassets)
        coinSearch = None

    urlList = config.CRYPTOWATCH_URL + "/assets/xpr"
    resp = req.getRequestResponse(urlList)

    print(resp)
    result = resp['result']
    rescursor = resp['cursor']
    resallow = resp['allowance']
    resstatus = resp['status_code']

    df = pd.DataFrame(result)
    df['route'] = df['route'].str[24:]
    print(df)
    print()
    print(rescursor)
    print(resallow)
    print(resstatus)
    
    

if __name__=='__main__':
    __main__()
