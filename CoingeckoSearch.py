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
import pandas as ps
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
    '''
    url = "https://api.coingecko.com/api/v3/search?query="+searchStr
    resp = req.getRequestResponse(url)
    resCoins = resp['coins']
    return resCoins


def inputNumber(message: str, min: int = 1, max: int = 1):
    '''
    UI for asking row number
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
                if (userInput < min or userInput > max):
                    print("No correct row number! Try again.")
                    continue
        return userInput 
        break


def safeFile(req, url, folder, filename):
    '''
    Download and safe a file from internet
    If folder doesn't exists, create the folder
    '''
    os.makedirs(folder, exist_ok=True)
        
    r = req.getRequestResponse(url, downloadFile=True)
    file = "%s\%s"%(folder,filename)
    print("Saving file from url: %s as file: %s"%(url, file))
    open(file, 'wb').write(r.content)


def insertCoin(req, db, params):
    '''
    Insert a new coin to the coins table
    And download the thumb and large picture of the coin
    '''
    safeFile(req, params['thumb'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"thumb"))    
    safeFile(req, params['large'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"large"))    
    query = "INSERT INTO coins (coingeckoid, name, symbol) " \
            "VALUES(?,?,?)"
    args = (params['id'], params['name'], params['symbol'])
    db.execute(query, args)
    db.commit()


def search(req, db, coinSearch):
    '''
    Search coins in own database (if table exists)
    Show the results
    
    Search coins from internet (Coingecko)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists
    '''
    ps.set_option("display.max_colwidth", 20)

    # Check if coin already in database and add to search result on row 0
    dbResult = []
    if db.checkTable['coins']:
        coinSearchStr = "%{}%".format(coinSearch)
        dbResult = db.query("SELECT * FROM coins WHERE coingeckoid like ? or name like ? or symbol like ?", \
                            (coinSearchStr, coinSearchStr, coinSearchStr))
        if (len(dbResult) > 0):
            dbResultdf = ps.DataFrame(dbResult)
            print("Search in database:")
            print(dbResultdf)

    # Do search on coingecko
    cgResult = searchId(req, coinSearch)
    cgResultdf = ps.DataFrame(cgResult)
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
            if not db.checkTable['coins']:
                db.createTable("coins")
                db.checkTable['coins'] = True
            
            dbResult = db.query("SELECT * FROM coins WHERE coingeckoid='%s'"%(coin['id']))
            if len(dbResult):
                print("Database already has a row with the coin %s"%(coin['id']))
            else:
                # add new row to table coins
                insertCoin(req, db, coin)
                

def __main__():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    args = argparser.parse_args()
    coinSearch = args.coin

    req = RequestHelper.RequestHelper()
    
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb()
    print("Database exists:", dbExist)
    print("Database exists:", db.hasConnection())
    dbTableExist = db.checkDb(table_name = 'coins')
    print("Table coins exist:", dbTableExist)

    while True:
        if coinSearch == None:
            coinSearch = input("Search for coin: ")
        search(req, db, coinSearch)
        coinSearch = None

if __name__=='__main__':
    __main__()

