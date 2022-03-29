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
    res = searchId(coinSearch)
    df = ps.DataFrame(res)
    print(df)

if __name__=='__main__':
    __main__()

