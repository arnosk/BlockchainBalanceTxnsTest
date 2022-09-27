'''
Created on July 23, 2022

@author: arno

Alcor search

'''
import config
import RequestHelper
import DbHelper
import pandas as pd
import argparse
import sys
import re


def searchId(searchStr, assets):
    '''
    Search for coin in list of all assets

    searchStr = string to search in assets
    assets = list of assets from Alcor
    '''
    s = (searchStr).lower()
    resCoins = [item for item in assets \
                if (re.match(s, item['base_token']['symbol']['name'].lower()) or \
                    re.search(s, item['base_token']['str'].lower()) or \
                    re.match(s, item['quote_token']['symbol']['name'].lower()) or \
                    re.search(s, item['quote_token']['str'].lower()) )]
    return resCoins


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


def insertCoin(req, db, params):
    '''
    Insert a new coin to the coins table
    And download the thumb and large picture of the coin


    req = instance of RequestHelper
    db = instance of DbHelperArko
    params = dictionary with retrieved coin info from Alcor
            {'id': 62,
             'symbol': 'doge',
             'name': 'Dogecoin',
             'fiat': False,
             'route': 'https://api.cryptowat.ch/assets/doge'
            }
    '''
    print(params)
    #safeFile(req, params['thumb'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"thumb"))    
    #safeFile(req, params['large'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"large"))    
    query = "INSERT INTO {} (alcorid, base, quote, chain) " \
            "VALUES(?,?,?,?)".format(db.table['coinAlcor'])
    args = (params['id'], 
            params['base_token']['str'], 
            params['quote_token']['str'], 
            params['chain'])
    db.execute(query, args)
    db.commit()


def search(req, db, coinSearch, assets):
    '''
    Search coins in own database (if table exists)
    Show the results
    
    Search coins from Alcor assets (already in assets)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists

    req = instance of RequestHelper
    db = instance of DbHelperArko
    coinSearch = string to search in assets
    assets = list of string with assets from Alcor
    '''
    pd.set_option("display.max_colwidth", 20)

    # Check if coin already in database and add to search result on row 0
    dbResult = []
    if db.checkTable(db.table['coinAlcor']):
        coinSearchStr = "%{}%".format(coinSearch)
        coinSearchQuery = '''SELECT * FROM {} WHERE
                                base like ? or
                                quote like ?
                          '''.format(db.table['coinAlcor'])
        dbResult = db.query(coinSearchQuery, \
                            (coinSearchStr, coinSearchStr))
        if (len(dbResult) > 0):
            dbResultdf = pd.DataFrame(dbResult)
            print("Search in database:")
            print(dbResultdf)

    # Do search on Alcor assets in memory
    cwResultCoin = searchId(coinSearch, assets)
    if (len(cwResultCoin) > 0):
        cwResultCoinPrint = []
        for item in cwResultCoin:
            cwResultCoinPrint.append(
                {'base': item['base_token']['str'], # item['base_token']['symbol']['name']
                'quote': item['quote_token']['str'], # item['quote_token']['symbol']['name']
                'chain': item['chain'],
                'volume24': item['volume24'],
                'volumeM': item['volumeMonth'],
                'id': item['id'],
                'ticker': item['ticker_id'] if 'ticker_id' in item else '-',
                'frozen': item['frozen']
                }
            )
        cwResultCoindf = pd.DataFrame(cwResultCoinPrint)
        cwResultCoindf_print = cwResultCoindf #.filter(['base_token', 'quote_token'], axis=1)
        print("Search from Alcor:")
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

        # check if database exist, in case of sqlite create database
        if not db.hasConnection():
            if db.getDbType() == DbHelper.DbType.sqlite:
                db.open()
            else:
                print("No database %s, do new search"%db.getDbType())

        # check if coin name, symbol is already in our database
        if db.hasConnection():
            # if table doesn't exist, create table coins
            if not db.checkTable(db.table['coinAlcor']):
                db.createTable(db.table['coinAlcor'])
                db.chkTable[db.table['coinAlcor']] = True
            
            dbResult = db.query("SELECT * FROM %s WHERE alcorid='%s'"%
                                (db.table['coinAlcor'], coin['id']))
            if len(dbResult):
                print("Database already has a row with the coin %s"%(coin['ticker_id']))
            else:
                # add new row to table coins
                insertCoin(req, db, coin)
                

def __main__():
    '''
    Get Alcor search assets and store in database

    Arguments:
    - coin to search
    - chain to search or if not present all chains
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Alcor')
    argparser.add_argument('-ch', '--chain', type=str, help='Chain name to search on Alcor')
    args = argparser.parse_args()
    coinSearch = args.coin
    chainStr = args.chain

    # Select chain from argument or take default all chains
    if chainStr != None:
        chains = re.split('[;,]', chainStr)
    else:
        chains = ["eos","telos","wax","bos","proton"]

    # for start, only search on proton chain
    chains = ['proton']

    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb()
    print("Database exists:", dbExist)
    print("Database exists:", db.hasConnection())
    dbTableExist = db.checkDb(table_name = db.table['coinAlcor'])
    print("Table coins exist:", dbTableExist)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request session
    req = RequestHelper.RequestHelper()
    
    # get all assets from Alcor
    urlList = config.ALCOR_URL.replace('?', chains[0]) + "/markets"
    print(urlList)
    resp = req.getRequestResponse(urlList)
    coinassets = resp['result']
    
    while coinassets != None:
        if coinSearch == None:
            coinSearch = input("Search for coin: ")
        search(req, db, coinSearch, coinassets)
        coinSearch = None


if __name__=='__main__':
    __main__()
