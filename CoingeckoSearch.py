'''
Created on Mar 29, 2022

@author: arno

Coingecko search
Search id for coins to finally get price from coingecko

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
from CoingeckoPrice import getRequestResponse
import DbHelper
from DbHelper import DbType
import config
import os 



# search coin id from coingecko
def searchId(searchStr):
    url = "https://api.coingecko.com/api/v3/search?query="+searchStr
    resp = getRequestResponse(url)
    resCoins = resp['coins']
    return resCoins
    

# Input row number from user
def inputNumber(message: str, min: int = 1, max: int = 1):
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

def safeFile(url, folder, filename):
    #r = requests.get(url, allow_redirects=True)
    if not os.path.isdir(folder):
        os.makedirs(folder)
        
    r = getRequestResponse(url, downloadFile=True)
    file = "%s\%s"%(folder,filename)
    print("Saving file from url: %s as file: %s"%(url, file))
    open(file, 'wb').write(r.content)

# Insert new row into coins table
def insertCoin(db, params):
    safeFile(params['thumb'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"thumb"))    
    safeFile(params['large'], "CoinImages", "coingecko_%s_%s.png"%(params['id'],"large"))    
    query = "INSERT INTO coins (coingeckoid, name, symbol) " \
            "VALUES(?,?,?)"
    args = (params['id'], params['name'], params['symbol'])
    db.execute(query, args)
    db.commit()

def search(db, coinSearch):
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
    cgResult = searchId(coinSearch)
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
                insertCoin(db, coin)
                


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    #parser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko', default='BTC')
    #parser.add_argument('-o', '--output', type=str, help='Path to the output JSON file', required=True)
    args = parser.parse_args()
    coinSearch = args.coin
    
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    dbExist = db.checkDb()
    print("Database exists:", dbExist)
    print("Database exists:", db.hasConnection())
    dbTableExist = db.checkDb(table_name = 'coins')
    print("Table coins exist:", dbTableExist)

    while True:
        if coinSearch == None:
            coinSearch = input("Search for coin: ")
        search(db, coinSearch)
        coinSearch = None

if __name__=='__main__':
    __main__()

