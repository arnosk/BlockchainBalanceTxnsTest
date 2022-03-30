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
from CoingeckoPrice import getRequestResponse
import psycopg2

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko', default='BTC')
#parser.add_argument('-o', '--output', type=str, help="Path to the output JSON file", required=True)

# search coin id from coingecko
def searchId(searchStr):
    url = "https://api.coingecko.com/api/v3/search?query="+searchStr
    resp = getRequestResponse(url)
    resCoins = resp['coins']
    return resCoins
    
    
def __main__():
    args = parser.parse_args()
    coinSearch = args.coin
    
    # Check if coin already in database and add to search result on row 0
    # Do search on coingecko
    
    res = searchId(coinSearch)
    df = ps.DataFrame(res)
    print(df)
    
    # ask user which row is the correct answer
    # or search another coin or exit
    
    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit

if __name__=='__main__':
    __main__()

