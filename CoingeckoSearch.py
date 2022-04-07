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
import config


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
#parser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko', default='BTC')
#parser.add_argument('-o', '--output', type=str, help="Path to the output JSON file", required=True)

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


def search(db, coinSearch):
    # Check if coin already in database and add to search result on row 0
    dbExist = db.checkDB(table_name = 'coins')
    print('Database and table coins exist: %s'%dbExist)

    dbResult = []
    if dbExist:
        dbResult = db.query("SELECT * FROM coins WHERE coin='%s'"%(coinSearch))

    # Do search on coingecko
    cgResult = searchId(coinSearch)
    cgResultSize = len(cgResult)
    dbResultSize = len(dbResult)
    
    ps.set_option("display.max_colwidth", 20)
    if (dbResultSize > 0):
        dbResultdf = ps.DataFrame(dbResult)
        print("Search in database:")
        print(dbResultdf)
    cgResultdf = ps.DataFrame(cgResult)
    print("Search from coingecko:")
    print(cgResultdf)
    
    # ask user which row is the correct answer
    userInput = inputNumber("Select correct coin to store in database, or (N)ew search, or (Q)uit: ",
                            0, cgResultSize-1)
    

    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit
    if userInput == "n":
        print("New search")
    elif userInput == "q":
        sys.exit("Exiting")
    else:
        # coin selected add to
        print("Number chosen = %s"%userInput)
        row = cgResult[userInput]
        print(row)
        # adding selected coin to database
        # don't add row in is already in dbResult



def __main__():
    args = parser.parse_args()
    coinSearch = args.coin
    db = DbHelper.DbHelper(config.DB_CONFIG, config.DB_TYPE)

    while True:
        if coinSearch == None:
            coinSearch = input("Search for coin: ")
        search(db, coinSearch)
        coinSearch = None

if __name__=='__main__':
    __main__()

