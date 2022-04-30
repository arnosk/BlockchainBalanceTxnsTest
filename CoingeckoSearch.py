'''
Created on Mar 29, 2022

@author: arno

Coingecko search
Search id for coins to finally get price from coingecko
Search if coin already is in database
Put choosen coin in database and downloads coin image

Response is a dictionary with keys
coins, exchanges, icos, categories, nfts
the key coins has a list of the search result of coins
{
  "coins": [
    {
      "id": "astroelon",
      "name": "AstroElon",
      "symbol": "ELONONE",
      "market_cap_rank": null,
      "thumb": "https://assets.coingecko.com/coins/images/16082/thumb/AstroElon.png",
      "large": "https://assets.coingecko.com/coins/images/16082/large/AstroElon.png"
    }
  ],
  "exchanges": [] ...
'''
import pandas as pd
import cfscrape
import argparse
import sys
import RequestHelper
import DbHelper
from DbHelper import DbType
import config
import os 


def searchId(req, searchStr):
    '''
    Search request to Coingecko

    req = instance of RequestHelper
    searchStr = string to search in assets
    '''
    url = "https://api.coingecko.com/api/v3/search?query="+searchStr
    resp = req.getRequestResponse(url)
    resCoins = resp['coins']
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


def saveFile(req, url, folder, filename):
    '''
    Download and safe a file from internet
    If folder doesn't exists, create the folder

    req = instance of RequestHelper
    url = url to download file
    folder = folder for saving downloaded file
    filename = filename for saving downloaded file
    '''
    os.makedirs(folder, exist_ok=True)

    url = url.split("?")[0]
    ext = url.split(".")[-1]
    file = "%s\%s.%s"%(folder, filename, ext)
       
    scraper = cfscrape.create_scraper()
    cfurl = scraper.get(url).content
    
    with open(file, 'wb') as f:
        f.write(cfurl)
        
    '''
    r = req.getRequestResponse(url, downloadFile=True, stream=True)
    if r.ok:
        print("Saving file from url: %s as file: %s"%(url, file))
        with open(file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
    '''
    


def insertCoin(req, db, params):
    '''
    Insert a new coin to the coins table
    And download the thumb and large picture of the coin

    req = instance of RequestHelper
    db = instance of DbHelperArko
    params = dictionary with retrieved coin info from coingecko
            {'id': 'dogecoin',
             'name': 'Dogecoin',
             'symbol': 'DOGE',
             'market_cap_rank': 10,
             'thumb': 'https://assets.coingecko.com/coins/images/5/thumb/dogecoin.png',
             'large': 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png'
            }
    '''
    saveFile(req, params['thumb'], "CoinImages", "coingecko_%s_%s"%(params['id'],"thumb"))    
    saveFile(req, params['large'], "CoinImages", "coingecko_%s_%s"%(params['id'],"large"))    
    query = "INSERT INTO {} (coingeckoid, name, symbol) " \
            "VALUES(?,?,?)".format(db.table['coinCoingecko'])
    args = (params['id'], params['name'], params['symbol'])
    db.execute(query, args)
    db.commit()


def downloadAllImages(req, db):
    '''
    Download image files for all coins in database from Coingecko

    req = instance of RequestHelper
    db = instance of DbHelperArko
    '''
    # Get all coingeckoid's from database
    coins = db.query("SELECT coingeckoid FROM {}".format(db.table['coinCoingecko']))
    coins = [i[0] for i in coins]
    
    # Retrieve coin info from coingecko
    for c in coins:
        url = '''https://api.coingecko.com/api/v3/coins/{}?
                 localization=false&
                 tickers=false&
                 market_data=false&
                 community_data=false&
                 developer_data=false&
                 sparkline=false
              '''.format(c)
        resp = req.getRequestResponse(url)
        paramsImage = resp['image']

        # Save image files
        saveFile(req, paramsImage['thumb'], "CoinImages", "coingecko_%s_%s"%(c,"thumb"))    
        saveFile(req, paramsImage['small'], "CoinImages", "coingecko_%s_%s"%(c,"small"))    
        saveFile(req, paramsImage['large'], "CoinImages", "coingecko_%s_%s"%(c,"large"))    


def search(req, db, coinSearch):
    '''
    Search coins in own database (if table exists)
    Show the results
    
    Search coins from internet (Coingecko)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists

    req = instance of RequestHelper
    db = instance of DbHelperArko
    coinSearch = string to search in assets
    '''
    pd.set_option("display.max_colwidth", 20)

    # Check if coin already in database and add to search result on row 0
    dbResult = []
    if db.checkTable(db.table['coinCoingecko']):
        coinSearchStr = "%{}%".format(coinSearch)
        coinSearchQuery = '''SELECT * FROM {} WHERE
                                coingeckoid like ? or
                                name like ? or
                                symbol like ?
                          '''.format(db.table['coinCoingecko'])
        dbResult = db.query(coinSearchQuery, \
                            (coinSearchStr, coinSearchStr, coinSearchStr))
        if (len(dbResult) > 0):
            dbResultdf = pd.DataFrame(dbResult)
            print("Search in database:")
            print(dbResultdf)

    # Do search on coingecko
    cgResult = searchId(req, coinSearch)
    cgResultdf = pd.DataFrame(cgResult)
    print("Search from coingecko:")
    print(cgResultdf)
    
    # ask user which row is the correct answer
    userInput = inputNumber("Select correct coin to store in database, or (N)ew search, or (Q)uit: ",
                            0, len(cgResult)-1)

    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit
    if userInput == "n":
        print("New search")
    elif userInput == "q":
        sys.exit("Exiting")
    else:
        # coin selected add to
        print("Number chosen = %s"%userInput)
        coin = cgResult[userInput]
        print(coin)

        # check if database exist, in case of sqlite create database
        if not db.hasConnection():
            if db.getDbType() == DbType.sqlite:
                db.open()
            else:
                print("No database %s, do new search"%db.getDbType())

        # check if coingecko id is already in our database
        if db.hasConnection():
            # if table doesn't exist, create table coins
            if not db.checkTable(db.table['coinCoingecko']):
                db.createTable(db.table['coinCoingecko'])
                db.chkTable[db.table['coinCoingecko']] = True
            
            dbResult = db.query("SELECT * FROM %s WHERE coingeckoid='%s'"%
                                (db.table['coinCoingecko'], coin['id']))
            if len(dbResult):
                print("Database already has a row with the coin %s"%(coin['id']))
            else:
                # add new row to table coins
                insertCoin(req, db, coin)
                

def __main__():
    '''
    Get Coingecko search assets and store in databse

    Arguments:
    - coin to search
    - image, save image file for all coins in database
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    argparser.add_argument('-i', '--image', action='store_true', help='Save image file for all coins in database')
    args = argparser.parse_args()
    coinSearch = args.coin

    req = RequestHelper.RequestHelper()
    
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb()
    print("Database exists:", dbExist)
    print("Database exists:", db.hasConnection())
    dbTableExist = db.checkDb(table_name = db.table['coinCoingecko'])
    print("Table coins exist:", dbTableExist)

    if args.image:
        if dbTableExist:
            downloadAllImages(req, db)
        else:
            print("No database, exiting")
    else:
        while True:
            if coinSearch == None:
                coinSearch = input("Search for coin: ")
            search(req, db, coinSearch)
            coinSearch = None

if __name__=='__main__':
    __main__()

